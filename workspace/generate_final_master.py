import os
import json
import base64
import io
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import warnings
warnings.filterwarnings('ignore')

# --- CONFIG & AUTH ---
plt.style.use('dark_background')
BG_COLOR = "#0f172a"
plt.rcParams.update({
    "axes.facecolor": BG_COLOR,
    "figure.facecolor": BG_COLOR,
    "grid.color": "#1e293b",
    "axes.edgecolor": "#1e293b",
    "text.color": "#f8fafc",
    "axes.labelcolor": "#f8fafc",
    "xtick.color": "#94a3b8",
    "ytick.color": "#94a3b8",
    "font.family": "sans-serif",
    "font.size": 11,
})

TOKEN_PATH = "/home/hermeswebui/.hermes/google_token.json"
creds = Credentials.from_authorized_user_file(TOKEN_PATH)
service = build("sheets", "v4", credentials=creds)
spreadsheet_id = "1jzgnRxmmLIe_DAZ7nwHSRXeO6sI4CRxlTatc0T88ukY"

# --- FETCH DATA ---
ranges = [
    "'Day Wise CAC Report'!A1:S5000",
    "DSA_graph1!A1:F60",
    "DSA_graph2!A1:C60",
    "'Brand graph1'!A1:F60",
    "'Brand graph2'!A1:C60",
    "graph1!A1:F60",
    "graph2!A1:C60"
]

print("Fetching data from Google Sheets...")
results = service.spreadsheets().values().batchGet(spreadsheetId=spreadsheet_id, ranges=ranges).execute()
value_ranges = results.get("valueRanges", [])
raw_data_cac = value_ranges[0].get("values", [])
dsa_g1 = value_ranges[1].get("values", [])
dsa_g2 = value_ranges[2].get("values", [])
brand_g1 = value_ranges[3].get("values", [])
brand_g2 = value_ranges[4].get("values", [])
meta_g1 = value_ranges[5].get("values", [])
meta_g2 = value_ranges[6].get("values", [])

# --- UTILS ---
def pnum(val):
    try:
        s = str(val).replace(',', '').strip().replace('%', '').replace('₹', '')
        if s == '-' or s == '': return 0.0
        return float(s)
    except: return 0.0

def format_currency(val):
    return f"₹{val:,.0f}"

def format_pct(val):
    return f"{val:.1f}%"

def format_num(val):
    return f"{val:,.0f}"

# --- PROCESS RAW CAC DATA ---
print("Processing data...")
df = pd.DataFrame(raw_data_cac[2:], columns=raw_data_cac[1])
df['Spends'] = df['Spends'].apply(pnum)
df['Pannel_Lead'] = df['Pannel_Lead'].apply(pnum)
df['Lead_LMS'] = df['Lead_LMS'].apply(pnum)
df['FFH'] = df['FFH'].apply(pnum)
df['Adm'] = df['Adm'].apply(pnum)
df['Invoicing_Var'] = df['Invoicing_Var'].apply(pnum)
df['Date_Parsed'] = pd.to_datetime(df['Date'], errors='coerce')

today = datetime(2026, 5, 2) 
ytd_start = datetime(2026, 1, 1)
mtd_start = datetime(2026, 5, 1)
ftd_start = today - timedelta(days=15)

def aggregate_data(start_date):
    mask = (df['Date_Parsed'] >= start_date) & (df['Date_Parsed'] <= today)
    filtered = df[mask]
    
    platforms = filtered['Platform'].unique()
    hierarchy = {}
    
    for plat in platforms:
        plat_df = filtered[filtered['Platform'] == plat]
        hierarchy[plat] = {}
        
        accounts = plat_df['Account'].unique()
        for acct in accounts:
            if not str(acct).strip() or str(acct).lower() == 'nan': continue
            acct_df = plat_df[plat_df['Account'] == acct]
            
            acct_stats = {
                'Spends': acct_df['Spends'].sum(),
                'Pannel_Lead': acct_df['Pannel_Lead'].sum(),
                'Lead_LMS': acct_df['Lead_LMS'].sum(),
                'FFH': acct_df['FFH'].sum(),
                'Adm': acct_df['Adm'].sum(),
                'Invoicing_Var': acct_df['Invoicing_Var'].sum()
            }
            
            camps = []
            campaign_names = acct_df['Campaign'].unique()
            for camp in campaign_names:
                camp_df = acct_df[acct_df['Campaign'] == camp]
                c_stats = {
                    'Campaign': camp,
                    'Spends': camp_df['Spends'].sum(),
                    'Pannel_Lead': camp_df['Pannel_Lead'].sum(),
                    'Lead_LMS': camp_df['Lead_LMS'].sum(),
                    'FFH': camp_df['FFH'].sum(),
                    'Adm': camp_df['Adm'].sum(),
                    'Invoicing_Var': camp_df['Invoicing_Var'].sum()
                }
                camps.append(c_stats)
            
            hierarchy[plat][acct] = {'stats': acct_stats, 'campaigns': camps}
            
    return hierarchy

ytd_h = aggregate_data(ytd_start)
mtd_h = aggregate_data(mtd_start)
ftd_h = aggregate_data(ftd_start)

# --- GRAPHING HELPERS ---
def prep_graph_data(cpl_rows, lead_rows):
    if not cpl_rows or not lead_rows or len(cpl_rows) < 2: return pd.DataFrame(), "", "", "", "", ""
    df_cpl = pd.DataFrame(cpl_rows[1:], columns=cpl_rows[0])
    df_lead = pd.DataFrame(lead_rows[1:], columns=lead_rows[0])
    
    x_col = df_cpl.columns[0]
    cpl_p = [c for c in df_cpl.columns if 'CPL' in c.upper() and 'PANNEL' in c.upper()][0]
    cpl_l = [c for c in df_cpl.columns if 'CPL' in c.upper() and 'LMS' in c.upper()][0]
    lead_p = [c for c in df_lead.columns if 'PANNEL' in c.upper()][0]
    lead_l = [c for c in df_lead.columns if 'LMS' in c.upper()][0]
    
    df_merged = pd.merge(df_cpl[[x_col, cpl_p, cpl_l]], df_lead[[df_lead.columns[0], lead_p, lead_l]], left_on=x_col, right_on=df_lead.columns[0])
    for c in [cpl_p, cpl_l, lead_p, lead_l]:
        df_merged[c] = pd.to_numeric(df_merged[c].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    
    df_merged[x_col] = pd.to_datetime(df_merged[x_col], errors='coerce')
    df_merged = df_merged.sort_values(by=x_col).dropna(subset=[x_col])
    df_merged[x_col] = df_merged[x_col].dt.strftime('%b %d')
    return df_merged, x_col, cpl_p, cpl_l, lead_p, lead_l

def create_bar_chart(df_g, x, y1, y2, title, l1, l2):
    if df_g.empty: return ""
    fig, ax = plt.subplots(figsize=(10, 3.5), dpi=150)
    pos = np.arange(len(df_g[x]))
    w = 0.35
    ax.bar(pos - w/2, df_g[y1], w, label=l1, color="#22d98a")
    ax.bar(pos + w/2, df_g[y2], w, label=l2, color="#a78bfa")
    ax.set_title(title, pad=15, fontweight='bold', fontsize=14)
    ax.set_xticks(pos)
    ax.set_xticklabels(df_g[x], rotation=45, ha="right", fontsize=9)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.25), ncol=2, frameon=False)
    ax.grid(True, axis='y', linestyle='--', alpha=0.2)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches='tight')
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode('utf-8')

def create_line_chart(df_g, x, y1, y2, title, l1, l2):
    if df_g.empty: return ""
    fig, ax = plt.subplots(figsize=(10, 3.5), dpi=150)
    ax.plot(df_g[x], df_g[y1], marker='o', color="#f5a623", label=l1, markersize=5, linewidth=2)
    ax.plot(df_g[x], df_g[y2], marker='s', color="#ff4d6d", label=l2, markersize=5, linewidth=2)
    ax.set_title(title, pad=15, fontweight='bold', fontsize=14)
    ax.set_xticks(range(len(df_g[x])))
    ax.set_xticklabels(df_g[x], rotation=45, ha="right", fontsize=9)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.25), ncol=2, frameon=False)
    ax.grid(True, axis='both', linestyle='--', alpha=0.2)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches='tight')
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode('utf-8')

# --- HTML GENERATION ---
def make_summary_table(hierarchy, prefix):
    html = '<div class="table-wrap"><table><thead><tr>'
    html += '<th class="text-left sticky-col">Account</th><th class="num">Spends</th><th class="num">P Leads</th><th class="num">LMS Leads</th>'
    html += '<th class="num">Dup%</th><th class="num">FFH</th><th class="num">ADM</th><th class="num">CPL Panel</th><th class="num">CPL LMS</th>'
    html += '<th class="num">CAC FFH</th><th class="num">CAC ADM</th><th class="num">ARPU</th><th class="num">L2F</th><th class="num">F2A</th></tr></thead>'
    
    inputs = ""
    css = ""
    idx = 0
    
    for plat, accounts in hierarchy.items():
        plat_icon = "🔵" if "Google" in plat else "🟣" if "Meta" in plat else "⚪"
        for acct, data in accounts.items():
            idx += 1
            cb_id = f"cb-{prefix}-{idx}"
            inputs += f'<input type="checkbox" id="{cb_id}" class="h-cb">\n'
            css += f"#{cb_id}:checked ~ .wrap #body-{cb_id} {{ display: table-row-group; }}\n"
            css += f"#{cb_id}:checked ~ .wrap label[for='{cb_id}'] .chev {{ transform: rotate(90deg); }}\n"
            
            s = data['stats']
            def calc_ratios(v):
                sp = v['Spends']
                lp = v['Pannel_Lead']
                ll = v['Lead_LMS']
                ff = v['FFH']
                ad = v['Adm']
                iv = v['Invoicing_Var']
                
                cpl_p = sp / lp if lp > 0 else 0
                cpl_l = sp / ll if ll > 0 else 0
                cac_f = sp / ff if ff > 0 else 0
                cac_a = sp / ad if ad > 0 else 0
                arpu = iv / ad if ad > 0 else 0
                dup = ((lp - ll) / lp * 100) if lp > 0 else 0
                l2f = (ff / ll * 100) if ll > 0 else 0
                f2a = (ad / ff * 100) if ff > 0 else 0
                return cpl_p, cpl_l, cac_f, cac_a, arpu, dup, l2f, f2a

            cp, cl, cf, ca, ar, dp, l2f, f2a = calc_ratios(s)
            dup_cls = "warn" if dp > 20 else ""
            
            html += f'''
            <tbody>
              <tr class="account-row">
                <td class="text-left sticky-col">
                  <label for="{cb_id}" class="exp-lbl">
                    <span class="chev">▶</span> {plat_icon} <strong>{acct}</strong>
                  </label>
                </td>
                <td class="num"><strong>{format_currency(s['Spends'])}</strong></td>
                <td class="num"><strong>{format_num(s['Pannel_Lead'])}</strong></td>
                <td class="num"><strong>{format_num(s['Lead_LMS'])}</strong></td>
                <td class="num {dup_cls}"><strong>{format_pct(dp)}</strong></td>
                <td class="num"><strong>{format_num(s['FFH'])}</strong></td>
                <td class="num"><strong>{format_num(s['Adm'])}</strong></td>
                <td class="num"><strong>{format_currency(cp)}</strong></td>
                <td class="num"><strong>{format_currency(cl)}</strong></td>
                <td class="num"><strong>{format_currency(cf)}</strong></td>
                <td class="num"><strong>{format_currency(ca)}</strong></td>
                <td class="num"><strong>{format_currency(ar)}</strong></td>
                <td class="num"><strong>{format_pct(l2f)}</strong></td>
                <td class="num"><strong>{format_pct(f2a)}</strong></td>
              </tr>
            </tbody>
            <tbody class="camp-body" id="body-{cb_id}">
            '''
            
            for c in data['campaigns']:
                ccp, ccl, ccf, cca, car, cdp, cl2f, cf2a = calc_ratios(c)
                cdup_cls = "warn" if cdp > 20 else ""
                html += f'''
                <tr class="camp-row">
                  <td class="text-left sticky-col" style="padding-left:35px; color:#94a3b8;">↳ {c['Campaign']}</td>
                  <td class="num">{format_currency(c['Spends'])}</td>
                  <td class="num">{format_num(c['Pannel_Lead'])}</td>
                  <td class="num">{format_num(c['Lead_LMS'])}</td>
                  <td class="num {cdup_cls}">{format_pct(cdp)}</td>
                  <td class="num">{format_num(c['FFH'])}</td>
                  <td class="num">{format_num(c['Adm'])}</td>
                  <td class="num">{format_currency(ccp)}</td>
                  <td class="num">{format_currency(ccl)}</td>
                  <td class="num">{format_currency(ccf)}</td>
                  <td class="num">{format_currency(cca)}</td>
                  <td class="num">{format_currency(car)}</td>
                  <td class="num">{format_pct(cl2f)}</td>
                  <td class="num">{format_pct(cf2a)}</td>
                </tr>
                '''
            html += '</tbody>'
            
    html += '</table></div>'
    return inputs, css, html

# --- NESTED DRILLDOWN FOR TABS 2,3,4 ---
def generate_nested_drilldown(plat_f=None, type_f=None):
    f_df = df.copy()
    if plat_f: f_df = f_df[f_df['Platform'].str.contains(plat_f, case=False, na=False)]
    if type_f: f_df = f_df[f_df['Type'].str.contains(type_f, case=False, na=False)]
    
    html = ""
    accounts = f_df['Account'].unique()
    for acct in accounts:
        if not str(acct).strip() or str(acct).lower() == 'nan': continue
        a_df = f_df[f_df['Account'] == acct]
        
        html += f'''
        <details class="acc-card">
            <summary class="acc-summary">
                <div class="sum-left">{acct}</div>
                <div class="sum-right">
                    <span class="pill">Spends: {format_currency(a_df['Spends'].sum())}</span>
                    <span class="pill">LMS: {format_num(a_df['Lead_LMS'].sum())}</span>
                </div>
            </summary>
            <div class="acc-body">
        '''
        
        camps = a_df['Campaign'].unique()
        for camp in camps:
            c_df = a_df[a_df['Campaign'] == camp]
            html += f'''
                <details class="camp-card">
                    <summary class="camp-summary">
                        <div class="camp-title">↳ {camp}</div>
                        <div class="camp-stats">
                           <span class="c-pill">Spends: {format_currency(c_df['Spends'].sum())}</span>
                           <span class="c-pill">Adm: {format_num(c_df['Adm'].sum())}</span>
                        </div>
                    </summary>
                    <div class="camp-body">
                        <div class="table-wrap">
                            <table>
                                <thead><tr><th class="text-left">Date</th><th class="text-left">Ad Name</th><th class="num">Spends</th><th class="num">LMS</th><th class="num">Adm</th></tr></thead>
                                <tbody>
            '''
            for _, row in c_df.sort_values(by='Date_Parsed', ascending=False).iterrows():
                html += f'''
                                    <tr>
                                        <td class="text-left">{row['Date']}</td>
                                        <td class="text-left" style="max-width:200px; overflow:hidden; text-overflow:ellipsis;">{row['Ad Name']}</td>
                                        <td class="num">{format_currency(row['Spends'])}</td>
                                        <td class="num">{format_num(row['Lead_LMS'])}</td>
                                        <td class="num">{format_num(row['Adm'])}</td>
                                    </tr>
                '''
            html += '</tbody></table></div></div></details>'
        html += '</div></details>'
    return html

# --- PREPARE ALL SECTIONS ---
print("Generating HTML components...")
g_inputs = ""
g_css = ""

y_in, y_cs, y_ht = make_summary_table(ytd_h, "ytd")
m_in, m_cs, m_ht = make_summary_table(mtd_h, "mtd")
f_in, f_cs, f_ht = make_summary_table(ftd_h, "ftd")

g_inputs += y_in + m_in + f_in
g_css += y_cs + m_cs + f_cs

# Graphing for other tabs
def get_graph_html(g1, g2, title_prefix):
    try:
        dg, x, cp, cl, lp, ll = prep_graph_data(g1, g2)
        if dg.empty: return ""
        b64_bar = create_bar_chart(dg, x, lp, ll, f"{title_prefix} Leads", "Panel", "LMS")
        b64_line = create_line_chart(dg, x, cp, cl, f"{title_prefix} CPL", "Panel", "LMS")
        return f'''<div class="graph-card">
            <img src="data:image/png;base64,{b64_bar}" class="responsive-img">
            <img src="data:image/png;base64,{b64_line}" class="responsive-img">
        </div>'''
    except Exception as e: 
        print(f"Graph error for {title_prefix}: {e}")
        return ""

dsa_graphs = get_graph_html(dsa_g1, dsa_g2, "DSA")
brand_graphs = get_graph_html(brand_g1, brand_g2, "Brand")
meta_graphs = get_graph_html(meta_g1, meta_g2, "Meta")

HTML_CONTENT = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<title>Degreefyd Dashboard</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; -webkit-tap-highlight-color:transparent; }}
body {{ background: #070b14; color: #f8fafc; font-family: -apple-system, sans-serif; font-size: 12px; padding: 5px; }}
.wrap {{ max-width: 1400px; margin: 0 auto; background: #0f172a; border-radius: 10px; border: 1px solid #1e293b; overflow: hidden; }}
.hdr {{ padding: 20px; text-align: center; border-bottom: 1px solid #1e293b; }}
.hdr h1 {{ font-size: 18px; color: #38bdf8; }}

input[type="radio"], input[type="checkbox"].h-cb {{ position: absolute; opacity: 0; pointer-events: none; }}
.tabs {{ display: flex; background: #0f172a; border-bottom: 1px solid #1e293b; }}
.tabs label {{ flex: 1; text-align: center; padding: 12px 5px; color: #64748b; font-weight: bold; border-bottom: 3px solid transparent; cursor: pointer; }}

#t1:checked ~ .wrap .lbl-t1, #t2:checked ~ .wrap .lbl-t2, #t3:checked ~ .wrap .lbl-t3, #t4:checked ~ .wrap .lbl-t4 {{ color: #38bdf8; border-bottom-color: #38bdf8; background: #1e293b; }}
.panel {{ display: none; padding: 10px; }}
#t1:checked ~ .wrap #p1, #t2:checked ~ .wrap #p2, #t3:checked ~ .wrap #p3, #t4:checked ~ .wrap #p4 {{ display: block; }}

.table-wrap {{ overflow-x: auto; margin-bottom: 15px; background: #020617; border-radius: 6px; }}
table {{ width: 100%; border-collapse: collapse; min-width: 800px; }}
th {{ background: #1e293b; color: #94a3b8; padding: 8px; font-size: 10px; text-transform: uppercase; text-align: right; border-bottom: 1px solid #334155; }}
td {{ padding: 10px 8px; border-bottom: 1px solid #1e293b; text-align: right; color: #f8fafc; white-space: nowrap; }}
.text-left {{ text-align: left; }}
.sticky-col {{ position: sticky; left: 0; background: inherit; z-index: 5; border-right: 1px solid #1e293b; }}

.account-row td {{ background: #1e293b !important; color: #f8fafc; font-weight: bold; }}
.exp-lbl {{ display: flex; align-items: center; cursor: pointer; width: 100%; font-size: 13px; }}
.chev {{ margin-right: 8px; transition: transform 0.2s; color: #38bdf8; }}
.camp-body {{ display: none; }}
.camp-row td {{ background: #070b14; color: #94a3b8; border-bottom: 0.5px solid #1e293b; }}
.num {{ font-family: monospace; }}
.warn {{ color: #f43f5e !important; }}

.graph-card {{ background: #020617; border-radius: 8px; padding: 10px; margin-bottom: 20px; border: 1px solid #1e293b; }}
.responsive-img {{ width: 100%; height: auto; display: block; margin-bottom: 10px; }}
.sec-title {{ font-size: 14px; margin: 20px 0 10px 0; color: #38bdf8; padding-bottom: 5px; border-bottom: 1px solid #1e293b; }}

.acc-card {{ background: #020617; border: 1px solid #1e293b; border-radius: 6px; margin-bottom: 8px; }}
.acc-summary {{ display: flex; align-items: center; justify-content: space-between; padding: 12px; cursor: pointer; list-style: none; font-weight: bold; }}
.acc-summary::before {{ content: "▶"; color: #38bdf8; margin-right: 10px; font-size: 10px; }}
details[open] > .acc-summary::before {{ transform: rotate(90deg); }}
.pill {{ background: #1e293b; padding: 2px 6px; border-radius: 4px; font-size: 10px; margin-left: 5px; }}
.camp-card {{ margin: 5px; background: #0f172a; border: 1px solid #334155; border-radius: 5px; }}
.camp-summary {{ padding: 10px; cursor: pointer; list-style: none; font-size: 11px; }}

{g_css}
</style>
</head>
<body>

{g_inputs}

<input type="radio" name="tabs" id="t1" checked>
<input type="radio" name="tabs" id="t2">
<input type="radio" name="tabs" id="t3">
<input type="radio" name="tabs" id="t4">

<div class="wrap">
  <div class="hdr"><h1>Degreefyd Executive Master Dashboard</h1></div>
  <div class="tabs">
    <label for="t1" class="lbl-t1">📊 SUMMARIES</label>
    <label for="t2" class="lbl-t2">🔷 DSA</label>
    <label for="t3" class="lbl-t3">🔶 BRAND</label>
    <label for="t4" class="lbl-t4">🟣 META</label>
  </div>
  
  <div id="p1" class="panel">
    <h3 class="sec-title">YEAR TO DATE (YTD)</h3>
    {y_ht}
    <h3 class="sec-title">MONTH TO DATE (MTD)</h3>
    {m_ht}
    <h3 class="sec-title">FORTNIGHT TO DATE (FTD)</h3>
    {f_ht}
  </div>

  <div id="p2" class="panel">
    {dsa_graphs}
    <h3 class="sec-title">DSA CAMPAIGN DRILLDOWN</h3>
    {generate_nested_drilldown(type_f="DSA")}
  </div>

  <div id="p3" class="panel">
    {brand_graphs}
    <h3 class="sec-title">BRAND CAMPAIGN DRILLDOWN</h3>
    {generate_nested_drilldown(type_f="Brand")}
  </div>

  <div id="p4" class="panel">
    {meta_graphs}
    <h3 class="sec-title">META CAMPAIGN DRILLDOWN</h3>
    {generate_nested_drilldown(plat_f="Meta")}
  </div>
</div>

</body>
</html>
"""

# SAVE & SEND
fpath = "/workspace/Degreefyd_Master_Fixed_V2.html"
with open(fpath, "w", encoding="utf-8") as f: f.write(HTML_CONTENT)

# SEND TO WHATSAPP
from dotenv import load_dotenv
load_dotenv("/workspace/.env")
WHAPI_TOKEN = os.getenv("WHAPI_TOKEN")
WHATSAPP_GROUP = os.getenv("WHATSAPP_GROUP")

with open(fpath, "rb") as f: b64 = base64.b64encode(f.read()).decode('utf-8')

payload = {
    "to": WHATSAPP_GROUP,
    "media": f"data:text/html;name=Degreefyd_Master_Fixed_V2.html;base64,{b64}",
    "caption": "✅ **REBUILT FROM RAW DATA**\n\nI fixed the hierarchy exactly as you wanted. \n\n1. **SUMMARIES TAB:** Now works like a pivot table. Click the **Account** (e.g. `Amity_Partner_001`) and it instantly shows all the **Campaigns** under it with their individual stats. \n2. **TRUE DATA:** I am now calculating the YTD/MTD/FTD stats directly from the raw `Day Wise CAC Report` to ensure every campaign is included.\n3. **DRILLDOWN TABS:** DSA, BRAND, and META still have the deep drilldown (Account -> Campaign -> Daily Table) with the graphs above them.\n\nEverything is grouped: **Platform > Account > Campaign**."
}

headers = {"accept": "application/json", "authorization": f"Bearer {WHAPI_TOKEN}", "content-type": "application/json"}
print(f"Sending to {WHATSAPP_GROUP}...")
resp = requests.post("https://gate.whapi.cloud/messages/document", headers=headers, json=payload)
print(resp.status_code, resp.text)
