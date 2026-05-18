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
from dotenv import load_dotenv
import warnings

warnings.filterwarnings('ignore')

# --- CONFIG & AUTH ---
BG_COLOR = "#ffffff"
TEXT_COLOR = "#0f172a"
SECONDARY_TEXT = "#475569"
BORDER_COLOR = "#cbd5e1"
ACCENT_BLUE = "#2563eb"
ACCENT_PURPLE = "#7c3aed"
ACCENT_GREEN = "#059669"
ACCENT_RED = "#dc2626"
ACCENT_ORANGE = "#d97706"

plt.rcParams.update({
    "axes.facecolor": BG_COLOR,
    "figure.facecolor": BG_COLOR,
    "grid.color": "#f1f5f9",
    "axes.edgecolor": "#cbd5e1",
    "text.color": TEXT_COLOR,
    "axes.labelcolor": TEXT_COLOR,
    "xtick.color": SECONDARY_TEXT,
    "ytick.color": SECONDARY_TEXT,
    "font.family": "sans-serif",
    "font.size": 10,
})

TOKEN_PATH="/home/mohit/.hermes/google_token.json"
creds = Credentials.from_authorized_user_file(TOKEN_PATH)
service = build("sheets", "v4", credentials=creds)
spreadsheet_id = "1jzgnRxmmLIe_DAZ7nwHSRXeO6sI4CRxlTatc0T88ukY"

# --- UTILS ---
def pnum(v):
    try:
        s = str(v).replace(',', '').strip().replace('%', '').replace('₹', '')
        if s == '-' or s == '': return 0.0
        return float(s)
    except: return 0.0

def format_currency(v): return f"₹{v:,.0f}"
def format_pct(v): return f"{v:.1f}%"
def format_num(v): return f"{v:,.0f}"

def rats(v):
    sp, lp, ll, ff, ad, iv = v['Spends'], v['Pannel_Lead'], v['Lead_LMS'], v['FFH'], v['Adm'], v['Invoicing_Var']
    cpl_p = sp/lp if lp > 0 else 0
    cpl_l = sp/ll if ll > 0 else 0
    cac_f = sp/ff if ff > 0 else 0
    cac_a = sp/ad if ad > 0 else 0
    arpu = iv/ad if ad > 0 else 0
    cac_arpu = (cac_a / arpu) if arpu > 0 else 0
    l2f = (ff / ll * 100) if ll > 0 else 0
    l2a = (ad / ll * 100) if ll > 0 else 0
    f2a = (ad / ff * 100) if ff > 0 else 0
    return cpl_p, cpl_l, cac_f, cac_a, arpu, cac_arpu, l2f, l2a, f2a

# --- FETCH DATA ---
print("Fetching data...")
ranges = ["'Day Wise CAC Report'!A1:S10000", "DSA_graph1!A1:F60", "DSA_graph2!A1:C60", "'Brand graph1'!A1:F60", "'Brand graph2'!A1:C60", "graph1!A1:F60", "graph2!A1:C60"]
results = service.spreadsheets().values().batchGet(spreadsheetId=spreadsheet_id, ranges=ranges).execute()
v_ranges = [r.get("values", []) for r in results.get("valueRanges", [])]
raw_cac = v_ranges[0]

# --- PROCESS DATA ---
df_headers = [c.strip() for c in raw_cac[1]]
df = pd.DataFrame(raw_cac[2:], columns=df_headers)
df['Platform'] = df['Platform'].fillna('').str.strip()
df['Type'] = df['Type'].fillna('').str.strip()
df['Account'] = df['Account'].fillna('').str.strip()
df['Campaign'] = df['Campaign'].fillna('').str.strip()
for c in ['Spends', 'Pannel_Lead', 'Lead_LMS', 'FFH', 'Adm', 'Invoicing_Var']:
    if c in df.columns: df[c] = df[c].apply(pnum)
df['Date_Parsed'] = pd.to_datetime(df['Date'], errors='coerce')
df = df.dropna(subset=['Date_Parsed'])
today = df['Date_Parsed'].max()
ytd_start, mtd_start, ftd_start = datetime(today.year, 1, 1), datetime(today.year, today.month, 1), today

# --- INTELLIGENCE (ANALYTICS) ---
def get_intelligence():
    # Last 7 days vs today
    last_7 = today - timedelta(days=7)
    recent_mask = (df['Date_Parsed'] >= last_7) & (df['Date_Parsed'] < today)
    today_mask = df['Date_Parsed'] == today
    
    recent_df = df[recent_mask]
    today_df = df[today_mask]
    
    if today_df.empty: return "No data for today yet."
    
    avg_cpl = (recent_df['Spends'].sum() / recent_df['Lead_LMS'].sum()) if recent_df['Lead_LMS'].sum() > 0 else 0
    today_cpl = (today_df['Spends'].sum() / today_df['Lead_LMS'].sum()) if today_df['Lead_LMS'].sum() > 0 else 0
    
    cpl_change = ((today_cpl - avg_cpl) / avg_cpl * 100) if avg_cpl > 0 else 0
    cpl_status = "increased" if cpl_change > 0 else "decreased"
    cpl_color = ACCENT_RED if cpl_change > 10 else ACCENT_GREEN
    
    # Best campaign by ADM today
    best_camp = today_df.sort_values('Adm', ascending=False).iloc[0]
    
    return f"""
    <div class="intel-card">
        <h3>AI Intelligence & Insights</h3>
        <div class="intel-grid">
            <div class="intel-item">
                <span class="intel-label">CPL Trend (Today vs 7D Avg)</span>
                <span class="intel-value" style="color:{cpl_color};">{format_pct(abs(cpl_change))} {cpl_status}</span>
            </div>
            <div class="intel-item">
                <span class="intel-label">Daily Lead Flow</span>
                <span class="intel-value">{format_num(today_df['Lead_LMS'].sum())} LMS Leads</span>
            </div>
            <div class="intel-item">
                <span class="intel-label">Top Performer</span>
                <span class="intel-value">{best_camp['Campaign']} ({format_num(best_camp['Adm'])} Adms)</span>
            </div>
        </div>
    </div>
    """

def aggregate(start, end):
    mask = (df['Date_Parsed'] >= start) & (df['Date_Parsed'] <= end)
    f = df[mask].copy()
    h = {}
    for plat in sorted(f['Platform'].unique()):
        if not plat: continue
        h[plat] = {}
        for acct in sorted(f[f['Platform']==plat]['Account'].unique()):
            if not acct: continue
            a_df = f[(f['Platform']==plat) & (f['Account']==acct)]
            h[plat][acct] = {
                'stats': {c: a_df[c].sum() for c in ['Spends', 'Pannel_Lead', 'Lead_LMS', 'FFH', 'Adm', 'Invoicing_Var']},
                'campaigns': []
            }
            for camp in sorted(a_df['Campaign'].unique()):
                c_df = a_df[a_df['Campaign']==camp]
                h[plat][acct]['campaigns'].append({
                    'Campaign': camp, 
                    'Spends': c_df['Spends'].sum(), 
                    'Pannel_Lead': c_df['Pannel_Lead'].sum(), 
                    'Lead_LMS': c_df['Lead_LMS'].sum(), 
                    'FFH': c_df['FFH'].sum(), 
                    'Adm': c_df['Adm'].sum(), 
                    'Invoicing_Var': c_df['Invoicing_Var'].sum(),
                    'rows': c_df.sort_values('Date_Parsed', ascending=False)
                })
    return h

ytd_all = aggregate(ytd_start, today)
mtd_all = aggregate(mtd_start, today)
ftd_all = aggregate(ftd_start, today)

# --- COMPONENTS ---
def render_tr(label, data, is_account=False, is_camp=False, is_daily=False, cid=None, pi="", indent=0, custom_bg=None, custom_co=None):
    s = data
    cpl_p, cpl_l, cac_f, cac_a, arpu, cac_arpu, l2f, l2a, f2a = rats(s)
    cls = ""
    if is_account: cls = "account-row"
    elif is_camp: cls = "camp-row"
    elif is_daily: cls = "daily-row"
    style = f' style="background:{custom_bg}; color:{custom_co if custom_co else "inherit"}; font-weight:bold;"' if custom_bg else ""
    lbl_content = f"<strong>{label}</strong>"
    if is_account: lbl_content = f'<label for="{cid}" class="exp-lbl"><span class="chev">▶</span> {pi} <strong>{label}</strong></label>'
    elif is_camp: lbl_content = f'<label for="{cid}" class="exp-lbl" style="padding-left:{indent}px;"><span class="chev">▶</span> ↳ {label}</label>'
    elif is_daily: lbl_content = f'<span style="padding-left:{indent}px;">{label}</span>'
    td_style = f' style="background:{custom_bg};"' if custom_bg else ""
    return f"""<tr class="{cls}"{style}>
        <td class="text-left sticky-col"{td_style}>{lbl_content}</td>
        <td class="num">{format_currency(s['Spends'])}</td><td class="num">{format_num(s['Pannel_Lead'])}</td><td class="num">{format_num(s['Lead_LMS'])}</td>
        <td class="num">{format_num(s['FFH'])}</td><td class="num">{format_num(s['Adm'])}</td><td class="num">{format_currency(s['Invoicing_Var'])}</td>
        <td class="num">{format_currency(cpl_p)}</td><td class="num">{format_currency(cpl_l)}</td><td class="num">{format_currency(cac_f)}</td>
        <td class="num">{format_currency(cac_a)}</td><td class="num">{format_currency(arpu)}</td><td class="num">{format_pct(cac_arpu*100)}</td>
        <td class="num">{format_pct(l2f)}</td><td class="num">{format_pct(l2a)}</td><td class="num">{format_pct(f2a)}</td>
    </tr>"""

def build_hierarchy_table(h, pref):
    ins, css, idx = "", "", 0
    html = '<div class="table-wrap"><table><thead><tr><th class="text-left sticky-col">Account / Campaign / Date</th><th class="num">Spends</th><th class="num">Pannel_Leads</th><th class="num">Leads_LMS</th><th class="num">FFH</th><th class="num">ADM</th><th class="num">Inv_Var</th><th class="num">CPL_Pannel</th><th class="num">CPL_LMS</th><th class="num">CAC_FFH</th><th class="num">CAC_Adm</th><th class="num">ARPU</th><th class="num">CAC/ARPU</th><th class="num">L2F</th><th class="num">L2A</th><th class="num">F2A</th></tr></thead>'
    for plat, accs in h.items():
        pi = "🔵" if "Google" in plat else "🟣" if "Meta" in plat else "⚪"
        for acct, data in accs.items():
            idx += 1
            cid = f"cb-{pref}-{idx}"
            ins += f'<input type="checkbox" id="{cid}" class="h-cb">\n'
            css += f"#{cid}:checked ~ .wrap #body-{cid} {{ display: table-row-group; }}\n#{cid}:checked ~ .wrap label[for='{cid}'] .chev {{ transform: rotate(90deg); }}\n"
            html += f'<tbody>{render_tr(acct, data["stats"], is_account=True, cid=cid, pi=pi)}</tbody>'
            html += f'<tbody class="camp-body" id="body-{cid}">'
            for ci, c in enumerate(data['campaigns']):
                iid = f"{cid}-c-{ci}"
                ins += f'<input type="checkbox" id="{iid}" class="h-cb">\n'
                css += f"#{iid}:checked ~ .wrap .daily-{iid} {{ display: table-row; }}\n#{iid}:checked ~ .wrap label[for='{iid}'] .chev {{ transform: rotate(90deg); }}\n"
                html += render_tr(c["Campaign"], c, is_camp=True, cid=iid, indent=25)
                html += f'<tr class="daily-hdr daily-{iid}"><th colspan="16" style="text-align:left; padding-left:50px; background:#f8fafc;">Daily (Last 5 Days)</th></tr>'
                for _, r in c['rows'].head(5).iterrows():
                    r_data = {col: r[col] for col in ['Spends', 'Pannel_Lead', 'Lead_LMS', 'FFH', 'Adm', 'Invoicing_Var']}
                    html += render_tr(f"{r['Date']} - {r['Ad Name']}", r_data, is_daily=True, indent=50).replace('<tr class="daily-row">', f'<tr class="daily-row daily-{iid}">')
            html += '</tbody>'
    return ins, css, html + '</table></div>'

def build_overall_cac(start, end):
    rows = []
    for l, p, t in [("META ADS", "Meta", None), ("Google Ads - Brand", "Google", "Brand"), ("Google Ads - DSA", "Google", "DSA"), ("Google Ads - Generic", "Google", "Generic")]:
        mask = (df['Date_Parsed'] >= start) & (df['Date_Parsed'] <= end)
        f = df[mask].copy()
        if p: f = f[f['Platform'].str.contains(p, case=False, na=False)]
        if t: f = f[f['Type'].str.contains(t, case=False, na=False)]
        s = {c: f[c].sum() for c in ['Spends', 'Pannel_Lead', 'Lead_LMS', 'FFH', 'Adm', 'Invoicing_Var']}
        rows.append((l, s))
    mask = (df['Date_Parsed'] >= start) & (df['Date_Parsed'] <= end)
    ov = {c: df[mask][c].sum() for c in ['Spends', 'Pannel_Lead', 'Lead_LMS', 'FFH', 'Adm', 'Invoicing_Var']}
    rows.append(("OVERALL TOTAL", ov))
    h = '<div class="table-wrap"><table class="overall-table"><thead><tr><th class="text-left sticky-col">Platform</th><th class="num">Spends</th><th class="num">Pannel_Leads</th><th class="num">Leads_LMS</th><th class="num">FFH</th><th class="num">ADM</th><th class="num">Inv_Var</th><th class="num">CPL_Pannel</th><th class="num">CPL_LMS</th><th class="num">CAC_FFH</th><th class="num">CAC_Adm</th><th class="num">ARPU</th><th class="num">CAC/ARPU</th><th class="num">L2F</th><th class="num">L2A</th><th class="num">F2A</th></tr></thead><tbody>'
    for label, s in rows:
        bg = "#f8fafc" if label == "OVERALL TOTAL" else "#ffffff"
        h += render_tr(label, s, custom_bg=bg)
    return h + '</tbody></table></div>'

# --- GRAPHS ---
def prep_g_fuzzy(g1_vals, g2_vals):
    if not g1_vals or not g2_vals or len(g1_vals) < 2: return pd.DataFrame(), "", "", "", "", ""
    d1, d2 = pd.DataFrame(g1_vals[1:], columns=[str(c).strip() for c in g1_vals[0]]), pd.DataFrame(g2_vals[1:], columns=[str(c).strip() for c in g2_vals[0]])
    x1, x2 = d1.columns[0], d2.columns[0]
    def fc(df, p):
        for c in df.columns:
            if p.upper() in str(c).upper().replace(' ', '').replace('_', ''): return c
        return None
    sp_col, lp_col = fc(d1, 'SPEND'), fc(d1, 'PANNEL')
    lp2_col, ll_col = fc(d2, 'PANNEL'), fc(d2, 'LMS')
    if not sp_col or not lp_col or not ll_col: return pd.DataFrame(), "", "", "", "", ""
    d1_sub = d1[[x1, sp_col, lp_col]].copy(); d1_sub.columns = ['Date_Shared', 'Spends_Internal', 'Pannel_Internal']
    d2_sub = d2[[x2, ll_col]].copy(); d2_sub.columns = ['Date_Shared', 'LMS_Internal']
    m = pd.merge(d1_sub, d2_sub, on='Date_Shared')
    for c in ['Spends_Internal', 'Pannel_Internal', 'LMS_Internal']: m[c] = m[c].apply(pnum)
    m['CPL_P'], m['CPL_L'] = m['Spends_Internal']/m['Pannel_Internal'], m['Spends_Internal']/m['LMS_Internal']
    m.replace([np.inf, -np.inf], 0, inplace=True); m.fillna(0, inplace=True)
    m['Date_Parsed'] = pd.to_datetime(m['Date_Shared'], errors='coerce')
    m = m.sort_values(by='Date_Parsed').dropna(subset=['Date_Parsed'])
    m['X'] = m['Date_Parsed'].dt.strftime('%b %d')
    return m, 'X', 'CPL_P', 'CPL_L', 'Pannel_Internal', 'LMS_Internal'

def create_line_chart(dfg, x, y1, y2, t, l1, l2, color1, color2, is_cpl=False):
    fig, ax = plt.subplots(figsize=(12, 5), dpi=150)
    ax.plot(dfg[x], dfg[y1], marker='o', color=color1, label=l1, linewidth=2.5, markersize=6)
    ax.plot(dfg[x], dfg[y2], marker='s', color=color2, label=l2, linewidth=2.5, markersize=6)
    for i, v in enumerate(dfg[y1]):
        lbl = f"₹{v:,.0f}" if is_cpl else f"{v:,.0f}"
        ax.text(i, v, lbl, ha='center', va='bottom', fontweight='bold', color=color1, fontsize=9, bbox=dict(facecolor='white', alpha=0.6, edgecolor='none', pad=1))
    for i, v in enumerate(dfg[y2]):
        lbl = f"₹{v:,.0f}" if is_cpl else f"{v:,.0f}"
        ax.text(i, v, lbl, ha='center', va='top', fontweight='bold', color=color2, fontsize=9, bbox=dict(facecolor='white', alpha=0.6, edgecolor='none', pad=1))
    ax.set_title(t, pad=20, fontweight='bold', fontsize=14)
    ax.set_xticks(range(len(dfg[x]))); ax.set_xticklabels(dfg[x], rotation=45, ha="right")
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=2, frameon=False)
    fig.tight_layout()
    buf = io.BytesIO(); fig.savefig(buf, format="png"); plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode('utf-8')

# --- FINAL BUILD ---
print("Generating HTML components...")
intel_html = get_intelligence()
y_in, y_cs, y_ht = build_hierarchy_table(ytd_all, "ytd")
m_in, m_cs, m_ht = build_hierarchy_table(mtd_all, "mtd")
f_in, f_cs, f_ht = build_hierarchy_table(ftd_all, "ftd")

HTML = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=5,user-scalable=yes"><style>
*{{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent;}}
body{{background:#f1f5f9;color:{TEXT_COLOR};font-family:'Inter',sans-serif;font-size:12px;padding:5px;}}
.wrap{{max-width:1400px;margin:0 auto;background:#fff;border-radius:12px;border:1px solid {BORDER_COLOR};overflow:hidden;box-shadow:0 20px 25px -5px rgba(0,0,0,0.1);}}
.hdr{{padding:35px 20px;text-align:center;border-bottom:1px solid {BORDER_COLOR};background:linear-gradient(135deg,#fff 0%,#f8fafc 100%);}}
.hdr h1{{font-size:26px;font-weight:800;color:#1e293b;}}
input[type="radio"],input[type="checkbox"].h-cb{{position:absolute;opacity:0;pointer-events:none;}}
.tabs{{display:flex;background:#fff;border-bottom:1px solid {BORDER_COLOR};overflow-x:auto;scrollbar-width:none;}}
.tabs label{{flex:1;min-width:120px;text-align:center;padding:18px 5px;color:{SECONDARY_TEXT};font-weight:800;border-bottom:4px solid transparent;cursor:pointer;font-size:12px;}}
#t1:checked~.wrap .lbl-t1,#t2:checked~.wrap .lbl-t2,#t3:checked~.wrap .lbl-t3,#t4:checked~.wrap .lbl-t4{{color:{ACCENT_BLUE};border-bottom-color:{ACCENT_BLUE};background:#f0f7ff;}}
.panel{{display:none;padding:15px;}}
#t1:checked~.wrap #p1,#t2:checked~.wrap #p2,#t3:checked~.wrap #p3,#t4:checked~.wrap #p4{{display:block;}}
.table-wrap{{overflow-x:auto;margin-bottom:30px;background:#fff;border-radius:10px;border:1px solid {BORDER_COLOR};}}
table{{width:100%;border-collapse:collapse;min-width:1100px;}}
th{{background:#f8fafc;color:{SECONDARY_TEXT};padding:12px 8px;font-size:10px;text-transform:uppercase;font-weight:800;text-align:right;border-bottom:2px solid {BORDER_COLOR};}}
td{{padding:12px 8px;border-bottom:1px solid #f1f5f9;text-align:right;color:{TEXT_COLOR};white-space:nowrap;}}
.text-left{{text-align:left!important;}}
.sticky-col{{position:sticky;left:0;background:inherit;z-index:5;border-right:2px solid #cbd5e1;}}
.account-row td{{background:#f8fafc!important;font-weight:800;border-bottom:2px solid {BORDER_COLOR};}}
.exp-lbl{{display:flex;align-items:center;cursor:pointer;width:100%;user-select:none;}}
.chev{{margin-right:12px;transition:transform .25s;color:{ACCENT_BLUE};font-size:11px;}}
.camp-body, .daily-hdr, .daily-row {{ display: none; }}
.camp-row td{{background:#fff;color:{SECONDARY_TEXT};font-weight:600;border-bottom: 1px dashed {BORDER_COLOR};}}
.daily-row td{{background:#fdfdfd;font-size:11px;color:#64748b;}}
.num{{font-family:'JetBrains Mono',monospace;}}
.graph-card{{background:#fff;border-radius:16px;padding:25px;margin-bottom:35px;border:1px solid {BORDER_COLOR};}}
.responsive-img{{width:100%;height:auto;display:block;margin-bottom:40px;border-radius:10px;}}
.sec-title{{font-size:20px;font-weight:800;margin:35px 0 20px 0;color:#1e293b;padding-bottom:12px;border-bottom:3px solid {ACCENT_BLUE};display:inline-block;}}
.graph-title{{font-size:14px;font-weight:700;margin-bottom:10px;color:#475569;text-transform:uppercase;}}
.intel-card{{background:#f8fafc;border:2px solid {ACCENT_BLUE};border-radius:12px;padding:20px;margin-bottom:25px;}}
.intel-card h3{{font-size:16px;font-weight:800;color:{ACCENT_BLUE};margin-bottom:15px;text-transform:uppercase;}}
.intel-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px;}}
.intel-item{{display:flex;flex-direction:column;}}
.intel-label{{font-size:11px;color:{SECONDARY_TEXT};font-weight:700;text-transform:uppercase;margin-bottom:4px;}}
.intel-value{{font-size:18px;font-weight:800;color:{TEXT_COLOR};}}
thead th {{ position: sticky; top: 0; z-index: 10; background: #f8fafc; }}
thead th.sticky-col {{ position: sticky; left: 0; top: 0; z-index: 20; background: #f8fafc !important; }}
{y_cs}{m_cs}{f_cs}
</style></head><body>
{y_in}{m_in}{f_in}
<input type="radio" name="tabs" id="t1" checked><input type="radio" name="tabs" id="t2"><input type="radio" name="tabs" id="t3"><input type="radio" name="tabs" id="t4">
<div class="wrap"><div class="hdr"><h1>Degreefyd Master Dashboard</h1><p>Intelligence • {today.strftime('%d %b %Y')}</p></div>
<div class="tabs"><label for="t1" class="lbl-t1">📊 SUMMARIES</label><label for="t2" class="lbl-t2">🔷 DSA</label><label for="t3" class="lbl-t3">🔶 BRAND</label><label for="t4" class="lbl-t4">🟣 META ADS</label></div>
<div id="p1" class="panel">
    {intel_html}
    <h3 class="sec-title">DETAILED DRILLDOWN (FTD)</h3>{f_ht}<h3 class="sec-title">Overall CAC (FTD)</h3>{build_overall_cac(ftd_start, today)}
    <h3 class="sec-title">DETAILED DRILLDOWN (MTD)</h3>{m_ht}<h3 class="sec-title">Overall CAC (MTD)</h3>{build_overall_cac(mtd_start, today)}
    <h3 class="sec-title">DETAILED DRILLDOWN (YTD)</h3>{y_ht}<h3 class="sec-title">Overall CAC (YTD)</h3>{build_overall_cac(ytd_start, today)}
</div>
<div id="p2" class="panel">
    <div class="graph-card">
        <h4 class="graph-title">Degreefyd Online Google ads DSA campaign lead pannel and lead lms</h4>
        <img src="data:image/png;base64,{create_line_chart(prep_g_fuzzy(v_ranges[1], v_ranges[2])[0], 'X', 'Pannel_Internal', 'LMS_Internal', 'Leads', 'Panel', 'LMS', ACCENT_GREEN, ACCENT_PURPLE)}" class="responsive-img">
        <h4 class="graph-title">Degreefyd Online Google ads DSA campaign cpl pannel and cpl lms</h4>
        <img src="data:image/png;base64,{create_line_chart(prep_g_fuzzy(v_ranges[1], v_ranges[2])[0], 'X', 'CPL_P', 'CPL_L', 'CPL', 'Panel', 'LMS', ACCENT_ORANGE, ACCENT_RED, True)}" class="responsive-img">
    </div>
</div>
<div id="p3" class="panel">
    <div class="graph-card">
        <h4 class="graph-title">Degreefyd Online Google ads Brand campaign lead pannel and lead lms</h4>
        <img src="data:image/png;base64,{create_line_chart(prep_g_fuzzy(v_ranges[3], v_ranges[4])[0], 'X', 'Pannel_Internal', 'LMS_Internal', 'Leads', 'Panel', 'LMS', ACCENT_GREEN, ACCENT_PURPLE)}" class="responsive-img">
        <h4 class="graph-title">Degreefyd Online Google ads Brand campaign cpl pannel and cpl lms</h4>
        <img src="data:image/png;base64,{create_line_chart(prep_g_fuzzy(v_ranges[3], v_ranges[4])[0], 'X', 'CPL_P', 'CPL_L', 'CPL', 'Panel', 'LMS', ACCENT_ORANGE, ACCENT_RED, True)}" class="responsive-img">
    </div>
</div>
<div id="p4" class="panel">
    <div class="graph-card">
        <h4 class="graph-title">Degreefyd Online META ads lead pannel and lead lms</h4>
        <img src="data:image/png;base64,{create_line_chart(prep_g_fuzzy(v_ranges[5], v_ranges[6])[0], 'X', 'Pannel_Internal', 'LMS_Internal', 'Leads', 'Panel', 'LMS', ACCENT_GREEN, ACCENT_PURPLE)}" class="responsive-img">
        <h4 class="graph-title">Degreefyd Online META ads cpl pannel and cpl lms</h4>
        <img src="data:image/png;base64,{create_line_chart(prep_g_fuzzy(v_ranges[5], v_ranges[6])[0], 'X', 'CPL_P', 'CPL_L', 'CPL', 'Panel', 'LMS', ACCENT_ORANGE, ACCENT_RED, True)}" class="responsive-img">
    </div>
</div>
</div></body></html>"""

with open("/workspace/Degreefyd_Final_Master_White.html", "w", encoding="utf-8") as f: f.write(HTML)

load_dotenv("/workspace/.env")
WHAPI_TOKEN, WHATSAPP_GROUP = os.getenv("WHAPI_TOKEN"), os.getenv("WHATSAPP_GROUP")
with open("/workspace/Degreefyd_Final_Master_White.html", "rb") as f: b64 = base64.b64encode(f.read()).decode('utf-8')
payload = {"to": WHATSAPP_GROUP, "media": f"data:text/html;name=Degreefyd_Final_Master_White.html;base64,{b64}", "caption": "🏆 **EXECUTIVE DASHBOARD - V3 INTELLIGENCE**\n\n✅ **AI Insights:** Dynamic performance summary added to top of report.\n✅ **Everything Collapsed:** Fixed state, all levels fully hidden by default.\n✅ **Summaries Moved:** Overall CAC tables now at bottom as requested.\n✅ **6 Exact Graphs:** Line charts with labels and exact naming.\n✅ **15 Columns Standard:** Full metrics set across all drilldown and summary views."}
requests.post("https://gate.whapi.cloud/messages/document", headers={"accept": "application/json", "authorization": f"Bearer {WHAPI_TOKEN}", "content-type": "application/json"}, json=payload)
print("Delivered.")
