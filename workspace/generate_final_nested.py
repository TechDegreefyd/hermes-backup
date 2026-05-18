import os
import json
import base64
import io
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import warnings
warnings.filterwarnings('ignore')

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

ranges = [
    "'Campaign Wise - YTD'!A1:S250",
    "'Campaign Wise - MTD'!A1:S250",
    "'Campaign Wise - FTD'!A1:S250",
    "'Day Wise CAC Report'!A1:S5000",
    "DSA_graph1!A1:F60",
    "DSA_graph2!A1:C60",
    "'Brand graph1'!A1:F60",
    "'Brand graph2'!A1:C60",
    "graph1!A1:F60",
    "graph2!A1:C60"
]

results = service.spreadsheets().values().batchGet(spreadsheetId=spreadsheet_id, ranges=ranges).execute()
data = {r["range"].split("!")[0].replace("'", ""): r.get("values", []) for r in results.get("valueRanges", [])}

def pnum(val):
    try: return float(str(val).replace(',', '').strip().replace('%', '').replace('₹', ''))
    except: return 0

def format_currency(val):
    num = pnum(val)
    if num == 0: return "0"
    return f"₹{num:,.0f}"

def format_pct(val):
    if not val or str(val).strip() == '-': return "-"
    num = pnum(val)
    return f"{num:.1f}%"

def format_num(val):
    num = pnum(val)
    if num == 0: return "0"
    return f"{num:,.0f}"

def make_df(rows):
    if not rows or len(rows) < 2: return pd.DataFrame()
    df = pd.DataFrame(rows[1:], columns=rows[0])
    df.columns = df.columns.str.strip()
    return df

# --- GRAPHS GENERATOR ---
def prep_graph_data(cpl_rows, lead_rows):
    df_cpl = make_df(cpl_rows)
    df_lead = make_df(lead_rows)
    if df_cpl.empty or df_lead.empty: return pd.DataFrame()
    
    x_col = df_cpl.columns[0]
    cpl_p = [c for c in df_cpl.columns if 'CPL' in c.upper() and 'PANNEL' in c.upper()][0]
    cpl_l = [c for c in df_cpl.columns if 'CPL' in c.upper() and 'LMS' in c.upper()][0]
    lead_p = [c for c in df_lead.columns if 'PANNEL' in c.upper()][0]
    lead_l = [c for c in df_lead.columns if 'LMS' in c.upper()][0]
    
    df = pd.merge(df_cpl[[x_col, cpl_p, cpl_l]], df_lead[[df_lead.columns[0], lead_p, lead_l]], left_on=x_col, right_on=df_lead.columns[0])
    for c in [cpl_p, cpl_l, lead_p, lead_l]:
        df[c] = pd.to_numeric(df[c].astype(str).str.replace(',', ''), errors='coerce')
    
    df[x_col] = pd.to_datetime(df[x_col], errors='coerce')
    df = df.sort_values(by=x_col).dropna(subset=[x_col])
    df[x_col] = df[x_col].dt.strftime('%b %d')
    return df, x_col, cpl_p, cpl_l, lead_p, lead_l

def create_bar_chart(df, x_col, y1_col, y2_col, title, label1, label2, color1="#38bdf8", color2="#8b5cf6"):
    if df.empty: return ""
    fig, ax = plt.subplots(figsize=(10, 3.5), dpi=150)
    x = np.arange(len(df[x_col]))
    width = 0.35
    ax.bar(x - width/2, df[y1_col], width, label=label1, color=color1)
    ax.bar(x + width/2, df[y2_col], width, label=label2, color=color2)
    ax.set_title(title, pad=15, fontweight='bold', color="#f8fafc", fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels(df[x_col], rotation=45, ha="right", fontsize=9)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.25), ncol=2, frameon=False)
    ax.grid(True, axis='y', linestyle='--', alpha=0.2)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches='tight')
    buf.seek(0)
    b64_img = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return f'<img src="data:image/png;base64,{b64_img}" alt="{title}" class="responsive-img" style="margin-bottom:20px;"/>'

def create_line_chart(df, x_col, y1_col, y2_col, title, label1, label2, color1="#f5a623", color2="#ff4d6d"):
    if df.empty: return ""
    fig, ax = plt.subplots(figsize=(10, 3.5), dpi=150)
    ax.plot(df[x_col], df[y1_col], marker='o', color=color1, label=label1, markersize=5, linewidth=2)
    ax.plot(df[x_col], df[y2_col], marker='s', color=color2, label=label2, markersize=5, linewidth=2)
    ax.set_title(title, pad=15, fontweight='bold', color="#f8fafc", fontsize=14)
    ax.set_xticks(range(len(df[x_col])))
    ax.set_xticklabels(df[x_col], rotation=45, ha="right", fontsize=9)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.25), ncol=2, frameon=False)
    ax.grid(True, axis='both', linestyle='--', alpha=0.2)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches='tight')
    buf.seek(0)
    b64_img = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return f'<img src="data:image/png;base64,{b64_img}" alt="{title}" class="responsive-img" style="margin-bottom:20px;"/>'

# --- YTD/MTD/FTD SUMMARY TABLES ---
def get_campaign_rows(sheet_name):
    raw_rows = data.get(sheet_name, [])
    if len(raw_rows) < 2: return []
    out = []
    for r in raw_rows[1:]:
        if not r or len(r) < 4: continue
        if str(r[0]).strip() == "Grand Total" or "Total" in str(r[0]): continue
        
        def v(idx): return r[idx] if len(r) > idx else "0"
        
        c_name = v(2).strip() if v(2).strip() else v(1).replace("Total","").strip()
        is_total = "Total" in str(r[1])
        if is_total: 
            c_name = f"<strong>{c_name} (Account Total)</strong>"
        else:
            c_name = f"<span style='padding-left:15px; color:#cbd5e1;'>↳ {c_name}</span>"
        
        lp = pnum(v(4))
        ll = pnum(v(5))
        dup = ((lp - ll) / lp * 100) if lp > 0 else 0
        dup_cls = "warn" if dup > 20 else ""
        
        out.append(f'''
        <tr class="{"total-row" if is_total else ""}">
            <td class="text-left">{c_name}</td>
            <td class="num">{format_currency(v(3))}</td>
            <td class="num">{format_num(v(4))}</td>
            <td class="num">{format_num(v(5))}</td>
            <td class="num {dup_cls}">{dup:.1f}%</td>
            <td class="num">{format_num(v(6))}</td>
            <td class="num">{format_num(v(7))}</td>
            <td class="num">{format_currency(v(8))}</td>
            <td class="num">{format_currency(v(9))}</td>
            <td class="num">{format_currency(v(10))}</td>
            <td class="num">{v(11) if "₹" in str(v(11)) else format_currency(v(11))}</td>
            <td class="num">{v(12) if "₹" in str(v(12)) else format_currency(v(12))}</td>
            <td class="num">{v(13)}</td>
            <td class="num">{v(14)}</td>
            <td class="num">{format_pct(v(15))}</td>
            <td class="num">{format_pct(v(16))}</td>
            <td class="num">{format_pct(v(17))}</td>
        </tr>
        ''')
    return "".join(out)

def make_summary_table(rows_html):
    if not rows_html: return "<p style='padding:20px; color:#94a3b8;'>No data available.</p>"
    return f'''
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th class="text-left sticky-col">Account / Campaign</th>
            <th class="num">Spends</th>
            <th class="num">Panel Leads</th>
            <th class="num">LMS Leads</th>
            <th class="num">Dup %</th>
            <th class="num">FFH</th>
            <th class="num">ADM</th>
            <th class="num">Inv_Var</th>
            <th class="num">CPL Panel</th>
            <th class="num">CPL LMS</th>
            <th class="num">CAC FFH</th>
            <th class="num">CAC ADM</th>
            <th class="num">ARPU</th>
            <th class="num">CAC/ARPU</th>
            <th class="num">L2F</th>
            <th class="num">L2A</th>
            <th class="num">F2A</th>
          </tr>
        </thead>
        <tbody>
          {rows_html}
        </tbody>
      </table>
    </div>
    '''

# --- NESTED ACCORDION LOGIC ---
res_cac = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range="'Day Wise CAC Report'!A1:S5000").execute()
rows_cac = res_cac.get('values', [])
raw_df = pd.DataFrame(rows_cac[2:], columns=[str(h).strip() for h in rows_cac[1]]) if len(rows_cac) > 2 else pd.DataFrame()

if not raw_df.empty:
    for c in ['Spends', 'Pannel_Lead', 'Lead_LMS', 'FFH', 'Adm', 'Invoicing_Var']:
        if c in raw_df.columns:
            raw_df[c] = pd.to_numeric(raw_df[c].astype(str).str.replace(',', '').replace('₹', '').replace('%', ''), errors='coerce').fillna(0)
    if 'Date' in raw_df.columns:
        raw_df['Date_Parsed'] = pd.to_datetime(raw_df['Date'], errors='coerce')

def generate_nested_drilldown(platform_filter=None, type_filter=None):
    if raw_df.empty: return "<p>No data found.</p>"
    
    df = raw_df.copy()
    if platform_filter: df = df[df['Platform'].str.contains(platform_filter, case=False, na=False)]
    if type_filter: df = df[df['Type'].str.contains(type_filter, case=False, na=False)]
    
    df = df[df['Account'].astype(str).str.strip() != '']
    df = df[df['Account'].astype(str).str.lower() != 'nan']
    if df.empty: return "<p style='padding:20px; color:#94a3b8;'>No data available for this filter.</p>"
    
    html = ""
    accounts = df['Account'].unique()
    
    for acct in accounts:
        acct_df = df[df['Account'] == acct]
        if acct_df.empty: continue
        
        a_spends = acct_df['Spends'].sum()
        a_pleads = acct_df['Pannel_Lead'].sum()
        a_lleads = acct_df['Lead_LMS'].sum()
        a_dup = ((a_pleads - a_lleads) / a_pleads * 100) if a_pleads > 0 else 0
        a_cpl_l = a_spends / a_lleads if a_lleads > 0 else 0
        a_dup_cls = "warn" if a_dup > 20 else ""
        
        html += f'''
        <details class="acc-card">
            <summary class="acc-summary">
                <div class="sum-left">{acct}</div>
                <div class="sum-right">
                    <span class="pill">Spends: {format_currency(a_spends)}</span>
                    <span class="pill">LMS Leads: {format_num(a_lleads)}</span>
                </div>
            </summary>
            <div class="acc-body">
        '''
        
        campaigns = acct_df['Campaign'].unique()
        for camp in campaigns:
            camp_df = acct_df[acct_df['Campaign'] == camp]
            c_name = camp if str(camp).strip() else "Generic / Unknown"
            
            c_spends = camp_df['Spends'].sum()
            c_pleads = camp_df['Pannel_Lead'].sum()
            c_lleads = camp_df['Lead_LMS'].sum()
            c_cpl_p = c_spends / c_pleads if c_pleads > 0 else 0
            c_cpl_l = c_spends / c_lleads if c_lleads > 0 else 0
            c_ffh = camp_df['FFH'].sum()
            c_adm = camp_df['Adm'].sum()
            c_inv = camp_df['Invoicing_Var'].sum()
            c_cac_f = c_spends / c_ffh if c_ffh > 0 else 0
            c_cac_a = c_spends / c_adm if c_adm > 0 else 0
            
            c_dup = ((c_pleads - c_lleads) / c_pleads * 100) if c_pleads > 0 else 0
            c_dup_cls = "warn" if c_dup > 20 else ""
            
            html += f'''
                <details class="camp-card">
                    <summary class="camp-summary">
                        <div class="camp-title">↳ {c_name}</div>
                        <div class="camp-stats">
                           <span class="c-pill">Spends: {format_currency(c_spends)}</span>
                           <span class="c-pill {c_dup_cls}">Dup%: {c_dup:.1f}%</span>
                           <span class="c-pill">CPL(L): {format_currency(c_cpl_l)}</span>
                        </div>
                    </summary>
                    <div class="camp-body">
                        <div class="table-wrap">
                            <table>
                                <thead>
                                    <tr>
                                        <th class="text-left sticky-col">Date</th>
                                        <th class="text-left">Ad Name</th>
                                        <th class="num">Spends</th>
                                        <th class="num">Panel Leads</th>
                                        <th class="num">LMS Leads</th>
                                        <th class="num">Dup %</th>
                                        <th class="num">FFH</th>
                                        <th class="num">ADM</th>
                                        <th class="num">Inv_Var</th>
                                        <th class="num">CPL Panel</th>
                                        <th class="num">CPL LMS</th>
                                        <th class="num">CAC FFH</th>
                                        <th class="num">CAC ADM</th>
                                    </tr>
                                </thead>
                                <tbody>
            '''
            
            camp_df = camp_df.sort_values(by='Date_Parsed', ascending=False)
            for _, row in camp_df.iterrows():
                rp = float(row.get('Pannel_Lead', 0))
                rl = float(row.get('Lead_LMS', 0))
                rdup = ((rp - rl) / rp * 100) if rp > 0 else 0
                rdup_cls = "warn" if rdup > 20 else ""
                
                rspends = float(row.get('Spends', 0))
                rffh = float(row.get('FFH', 0))
                radm = float(row.get('Adm', 0))
                
                rcpl_p = rspends / rp if rp > 0 else 0
                rcpl_l = rspends / rl if rl > 0 else 0
                rcac_f = rspends / rffh if rffh > 0 else 0
                rcac_a = rspends / radm if radm > 0 else 0
                
                html += f'''
                                    <tr>
                                        <td class="text-left sticky-col">{row.get('Date', '-')}</td>
                                        <td class="text-left" style="color: #cbd5e1; max-width:250px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="{row.get('Ad Name', '-')}">{row.get('Ad Name', '-')}</td>
                                        <td class="num">₹{rspends:,.0f}</td>
                                        <td class="num">{rp:,.0f}</td>
                                        <td class="num">{rl:,.0f}</td>
                                        <td class="num {rdup_cls}">{rdup:.1f}%</td>
                                        <td class="num">{rffh:,.0f}</td>
                                        <td class="num">{radm:,.0f}</td>
                                        <td class="num">₹{float(row.get('Invoicing_Var', 0)):,.0f}</td>
                                        <td class="num">₹{rcpl_p:,.0f}</td>
                                        <td class="num">₹{rcpl_l:,.0f}</td>
                                        <td class="num">₹{rcac_f:,.0f}</td>
                                        <td class="num">₹{rcac_a:,.0f}</td>
                                    </tr>
                '''
            html += '''
                                </tbody>
                            </table>
                        </div>
                    </div>
                </details>
            '''
        html += "</div></details>"
    return html


# --- GENERATE SECTIONS ---
sections = {}

# Tab 1: Full Campaign Data (YTD, MTD, FTD Tables)
sections['ytd'] = make_summary_table(get_campaign_rows("Campaign Wise - YTD"))
sections['mtd'] = make_summary_table(get_campaign_rows("Campaign Wise - MTD"))
sections['ftd'] = make_summary_table(get_campaign_rows("Campaign Wise - FTD"))

# Tab 2: DSA (Graphs + Nested Accordion)
try:
    df_dsa, x_dsa, cpl_p_dsa, cpl_l_dsa, lead_p_dsa, lead_l_dsa = prep_graph_data(data.get("DSA_graph1", []), data.get("DSA_graph2", []))
    sections['dsa'] = f"""
    <div class="graph-card">
        {create_bar_chart(df_dsa, x_dsa, lead_p_dsa, lead_l_dsa, "DSA Leads Trend", "Panel Leads", "LMS Leads", "#22d98a", "#a78bfa")}
        {create_line_chart(df_dsa, x_dsa, cpl_p_dsa, cpl_l_dsa, "DSA CPL Trend", "CPL Panel", "CPL LMS", "#f5a623", "#ff4d6d")}
    </div>
    <h2 class="sec-title">DSA Campaign Breakdown</h2>
    {generate_nested_drilldown(type_filter="DSA")}
    """
except Exception as e: sections['dsa'] = str(e)

# Tab 3: Brand (Graphs + Nested Accordion)
try:
    df_brand, x_brand, cpl_p_brand, cpl_l_brand, lead_p_brand, lead_l_brand = prep_graph_data(data.get("Brand graph1", []), data.get("Brand graph2", []))
    sections['brand'] = f"""
    <div class="graph-card">
        {create_bar_chart(df_brand, x_brand, lead_p_brand, lead_l_brand, "Brand Leads Trend", "Panel Leads", "LMS Leads", "#22d98a", "#a78bfa")}
        {create_line_chart(df_brand, x_brand, cpl_p_brand, cpl_l_brand, "Brand CPL Trend", "CPL Panel", "CPL LMS", "#f5a623", "#ff4d6d")}
    </div>
    <h2 class="sec-title">Brand Campaign Breakdown</h2>
    {generate_nested_drilldown(type_filter="Brand")}
    """
except Exception as e: sections['brand'] = str(e)

# Tab 4: Meta (Graphs + Nested Accordion)
try:
    df_meta, x_meta, cpl_p_meta, cpl_l_meta, lead_p_meta, lead_l_meta = prep_graph_data(data.get("graph1", []), data.get("graph2", []))
    sections['meta'] = f"""
    <div class="graph-card">
        {create_bar_chart(df_meta, x_meta, lead_p_meta, lead_l_meta, "Meta Leads Trend", "Panel Leads", "LMS Leads", "#22d98a", "#a78bfa")}
        {create_line_chart(df_meta, x_meta, cpl_p_meta, cpl_l_meta, "Meta CPL Trend", "CPL Panel", "CPL LMS", "#f5a623", "#ff4d6d")}
    </div>
    <h2 class="sec-title">Meta Campaign Breakdown</h2>
    {generate_nested_drilldown(platform_filter="Meta")}
    """
except Exception as e: sections['meta'] = str(e)

HTML_TEMPLATE = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0"/>
<title>Degreefyd Executive Dashboard</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; -webkit-tap-highlight-color:transparent; }}
body {{ background: #070b14; color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 13px; line-height: 1.5; padding: 10px; }}
.wrap {{ max-width: 1400px; margin: 0 auto; background: #0f172a; border-radius: 12px; overflow: hidden; border: 1px solid #1e293b; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }}
.hdr {{ background: #020617; padding: 24px 20px; text-align: center; border-bottom: 1px solid #1e293b; }}
.hdr h1 {{ font-size: 22px; font-weight: 800; margin-bottom: 6px; color: #f8fafc; letter-spacing: -0.5px; }}
.hdr p {{ font-size: 13px; color: #94a3b8; }}

/* TABS */
input[type="radio"] {{ display: none; }}
.tabs {{ display: flex; flex-wrap: wrap; background: #0f172a; border-bottom: 1px solid #1e293b; }}
.tabs label {{ flex: 1 1 45%; text-align: center; padding: 16px 8px; font-size: 14px; font-weight: 700; color: #64748b; border-bottom: 3px solid transparent; cursor: pointer; transition: 0.2s; white-space: nowrap; }}
#t1:checked ~ .wrap .lbl-t1, #t2:checked ~ .wrap .lbl-t2, #t3:checked ~ .wrap .lbl-t3, #t4:checked ~ .wrap .lbl-t4 {{ color: #38bdf8; border-bottom-color: #38bdf8; background: #1e293b; }}

.panel {{ display: none; padding: 15px; }}
#t1:checked ~ .wrap #p1, #t2:checked ~ .wrap #p2, #t3:checked ~ .wrap #p3, #t4:checked ~ .wrap #p4 {{ display: block; }}

/* GRAPHS */
.graph-card {{ background: #020617; border: 1px solid #1e293b; border-radius: 10px; margin-bottom: 24px; padding: 20px; }}
.responsive-img {{ width: 100%; height: auto; display: block; border-radius: 6px; margin-bottom: 20px; }}
.sec-title {{ font-size: 18px; font-weight: 800; color: #f8fafc; margin: 30px 0 16px 0; padding-bottom: 8px; border-bottom: 1px solid #334155; }}
.sec-title:first-child {{ margin-top: 0; }}

/* TABLES */
.table-wrap {{ overflow-x: auto; background: #020617; border-radius: 8px; border: 1px solid #334155; margin-bottom: 24px; }}
table {{ width: 100%; border-collapse: collapse; text-align: right; min-width: 1000px; }}
th {{ background: #1e293b; color: #cbd5e1; font-size: 11px; text-transform: uppercase; font-weight: 800; padding: 12px 14px; border-bottom: 2px solid #334155; white-space: nowrap; }}
td {{ padding: 12px 14px; border-bottom: 1px solid #1e293b; font-size: 13px; color: #f8fafc; white-space: nowrap; }}
tr:nth-child(even) td {{ background: #0f172a; }}

.sticky-col {{ position: sticky; left: 0; background: inherit; z-index: 5; border-right: 2px solid #1e293b; box-shadow: 2px 0 5px rgba(0,0,0,0.2); }}
th.sticky-col {{ z-index: 15; }}

.num {{ font-family: ui-monospace, SFMono-Regular, Consolas, monospace; color: #e2e8f0; }}
th.num {{ text-align: right; }}
.text-left {{ text-align: left; }}
.warn {{ color: #f43f5e !important; font-weight: bold; }}
.total-row td {{ background: #1e293b !important; font-weight: 700; border-top: 2px solid #334155; border-bottom: 2px solid #334155; color: #f8fafc; }}

/* NESTED ACCORDIONS */
.acc-card {{ background: #020617; border: 1px solid #1e293b; border-radius: 8px; margin-bottom: 12px; overflow: hidden; }}
.acc-summary {{ display: flex; align-items: center; justify-content: space-between; padding: 16px; font-weight: 700; cursor: pointer; color: #f8fafc; list-style: none; transition: background 0.2s; font-size: 15px; }}
.acc-summary:active {{ background: #0f172a; }}
.acc-summary::-webkit-details-marker {{ display: none; }}
.acc-summary::before {{ content: "▶"; color: #38bdf8; font-size: 12px; margin-right: 12px; transition: transform 0.2s; }}
details[open] > .acc-summary::before {{ transform: rotate(90deg); }}
details[open] > .acc-summary {{ border-bottom: 1px solid #1e293b; background: #0f172a; }}

.sum-left {{ display: flex; align-items: center; }}
.sum-right {{ display: flex; gap: 8px; font-size: 12px; font-weight: 600; }}
.pill {{ background: #1e293b; padding: 4px 10px; border-radius: 6px; border: 1px solid #334155; color: #cbd5e1; }}
.acc-body {{ padding: 10px; }}

.camp-card {{ background: #0f172a; border: 1px solid #334155; border-radius: 6px; margin-bottom: 8px; overflow: hidden; }}
.camp-summary {{ display: flex; align-items: center; justify-content: space-between; padding: 12px; font-weight: 600; cursor: pointer; color: #e2e8f0; list-style: none; transition: background 0.2s; font-size: 13px; }}
.camp-summary:active {{ background: #1e293b; }}
.camp-summary::-webkit-details-marker {{ display: none; }}
.camp-summary::before {{ content: "▶"; color: #a78bfa; font-size: 10px; margin-right: 10px; transition: transform 0.2s; }}
details[open] > .camp-summary::before {{ transform: rotate(90deg); }}
details[open] > .camp-summary {{ border-bottom: 1px solid #334155; background: #1e293b; }}

.camp-title {{ flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; padding-right: 10px; }}
.camp-stats {{ display: flex; gap: 8px; font-size: 11px; }}
.camp-stats span {{ background: #020617; padding: 2px 6px; border-radius: 4px; border: 1px solid #1e293b; }}
.camp-body {{ padding: 0; }}
.camp-body .table-wrap {{ margin-bottom: 0; border: none; border-radius: 0; }}
.camp-body th {{ background: #1e293b; border-bottom: 2px solid #334155; padding: 10px; font-size: 10px; }}
.camp-body td {{ padding: 10px; font-size: 12px; }}

</style>
</head>
<body>

<input type="radio" name="tabs" id="t1" checked>
<input type="radio" name="tabs" id="t2">
<input type="radio" name="tabs" id="t3">
<input type="radio" name="tabs" id="t4">

<div class="wrap">
  <div class="hdr">
    <h1>Degreefyd Complete Dashboard</h1>
    <p>Tabs • Graphs • Nested Campaign Dropdowns</p>
  </div>
  
  <div class="tabs">
    <label for="t1" class="lbl-t1">📊 Summaries</label>
    <label for="t2" class="lbl-t2">🔷 DSA</label>
    <label for="t3" class="lbl-t3">🔶 Brand</label>
    <label for="t4" class="lbl-t4">🟣 Meta</label>
  </div>
  
  <div id="p1" class="panel">
    <h2 class="sec-title">Year-To-Date Overview</h2>
    {sections['ytd']}
    <h2 class="sec-title">Month-To-Date Overview</h2>
    {sections['mtd']}
    <h2 class="sec-title">Fortnight-To-Date Overview</h2>
    {sections['ftd']}
  </div>
  
  <div id="p2" class="panel">
    {sections['dsa']}
  </div>
  
  <div id="p3" class="panel">
    {sections['brand']}
  </div>
  
  <div id="p4" class="panel">
    {sections['meta']}
  </div>

</div>

</body>
</html>
"""

file_path = "/workspace/Degreefyd_Dashboard_Complete.html"
with open(file_path, "w", encoding="utf-8") as f: f.write(HTML_TEMPLATE)

# --- SEND VIA WHAPI ---
from dotenv import load_dotenv
load_dotenv("/workspace/.env")
WHAPI_TOKEN = os.getenv("WHAPI_TOKEN")
WHATSAPP_GROUP = os.getenv("WHATSAPP_GROUP")

with open(file_path, "rb") as f: b64 = base64.b64encode(f.read()).decode('utf-8')

payload = {
    "to": WHATSAPP_GROUP,
    "media": f"data:text/html;name=Degreefyd_Dashboard_Complete.html;base64,{b64}",
    "caption": "🔥 **Degreefyd Ultimate (Nested Drilldown)**\n\n✅ **Tabs Are Kept:** Full Campaign Data (YTD/MTD), DSA, Brand, and Meta.\n✅ **Graphs Are Kept:** Lead Bar Charts and CPL Line Charts exactly where they were.\n✅ **The Nested Campaign Feature:** Under DSA, Brand, and Meta, you will see a list of Accounts. Tap the Account -> Tap the Campaign -> You will see the exact Daily Ads table nested inside! (`Date | Ad Name | Spends | Leads | Dup%`...)"
}

headers = {"accept": "application/json", "authorization": f"Bearer {WHAPI_TOKEN}", "content-type": "application/json"}

import time
for _ in range(3):
    try:
        resp = requests.post("https://gate.whapi.cloud/messages/document", headers=headers, json=payload, timeout=10)
        if resp.status_code == 200:
            print("Successfully sent to WhatsApp!")
            break
    except Exception as e:
        print("Failed, retrying...", e)
        time.sleep(2)
