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

plt.style.use('dark_background')
BG_COLOR = "#0f172a"
plt.rcParams.update({
    "axes.facecolor": BG_COLOR,
    "figure.facecolor": BG_COLOR,
    "grid.color": "#334155",
    "axes.edgecolor": "#334155",
    "text.color": "#f8fafc",
    "axes.labelcolor": "#f8fafc",
    "xtick.color": "#94a3b8",
    "ytick.color": "#94a3b8",
    "font.family": "sans-serif",
    "font.size": 12,
})

TOKEN_PATH = "/home/hermeswebui/.hermes/google_token.json"
creds = Credentials.from_authorized_user_file(TOKEN_PATH)
service = build("sheets", "v4", credentials=creds)
spreadsheet_id = "1jzgnRxmmLIe_DAZ7nwHSRXeO6sI4CRxlTatc0T88ukY"

ranges = [
    "'Campaign Wise - YTD'!A1:S250",
    "'Campaign Wise - MTD'!A1:S250",
    "'Campaign Wise - FTD'!A1:S250",
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

def make_df(rows):
    if not rows or len(rows) < 2: return pd.DataFrame()
    return pd.DataFrame(rows[1:], columns=rows[0])

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
    
    # Sort by date (assuming YYYY-MM-DD or similar)
    df[x_col] = pd.to_datetime(df[x_col], errors='coerce')
    df = df.sort_values(by=x_col).dropna(subset=[x_col])
    df[x_col] = df[x_col].dt.strftime('%b %d')
    return df, x_col, cpl_p, cpl_l, lead_p, lead_l

def create_bar_chart(df, x_col, y1_col, y2_col, title, label1, label2, color1="#38bdf8", color2="#8b5cf6"):
    if df.empty: return ""
    fig, ax = plt.subplots(figsize=(9, 4), dpi=200)
    
    x = np.arange(len(df[x_col]))
    width = 0.35
    
    ax.bar(x - width/2, df[y1_col], width, label=label1, color=color1)
    ax.bar(x + width/2, df[y2_col], width, label=label2, color=color2)
    
    ax.set_title(title, pad=15, fontweight='bold', color="#f8fafc")
    ax.set_xticks(x)
    ax.set_xticklabels(df[x_col], rotation=45, ha="right")
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=2, frameon=False)
    ax.grid(True, axis='y', linestyle='--', alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches='tight')
    buf.seek(0)
    b64_img = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return f'<img src="data:image/png;base64,{b64_img}" alt="{title}" class="responsive-img" style="margin-bottom:15px;"/>'

def format_currency(val):
    if not val: return "-"
    num = pnum(val)
    if num == 0 and "0" not in str(val): return str(val)
    return f"₹{num:,.0f}"

def format_pct(val):
    if not val: return "-"
    num = pnum(val)
    return f"{num:.1f}%"

def format_num(val):
    if not val: return "-"
    num = pnum(val)
    return f"{num:,.0f}"

# --- ACCORDION GENERATOR ---
def process_hierarchy(raw_rows):
    if len(raw_rows) < 2: return {}
    hierarchy = {}
    current_platform = "Unknown"
    current_account = "Unknown"
    
    for r in raw_rows[1:]:
        if not r or len(r) < 4: continue
        if str(r[0]).strip() == "Grand Total": continue
        
        # Determine hierarchy
        if str(r[0]).strip() and "Total" not in str(r[0]):
            current_platform = str(r[0]).strip()
        
        is_account_total = "Total" in str(r[1])
        is_platform_total = "Total" in str(r[0])
        
        if is_platform_total: continue
        
        if is_account_total:
            current_account = str(r[1]).replace("Total", "").strip()
            if current_platform not in hierarchy:
                hierarchy[current_platform] = {}
            hierarchy[current_platform][current_account] = {
                "is_total": True,
                "data": r,
                "campaigns": []
            }
        else:
            # It's a campaign row
            camp_name = str(r[2]).strip()
            if not camp_name: camp_name = "Generic/Unknown Campaign"
            if current_platform in hierarchy and current_account in hierarchy[current_platform]:
                hierarchy[current_platform][current_account]["campaigns"].append(r)
                
    return hierarchy

def generate_accordion_html(hierarchy, unique_id_prefix):
    html = ""
    acc_idx = 0
    
    for platform, accounts in hierarchy.items():
        platform_icon = "🔵 Google Ads" if "Google" in platform else "🟣 Meta Ads" if "Meta" in platform else "⚪ " + platform
        platform_class = "g-badge" if "Google" in platform else "m-badge" if "Meta" in platform else ""
        
        for account, acct_data in accounts.items():
            acc_idx += 1
            cb_id = f"acc-{unique_id_prefix}-{acc_idx}"
            
            tr = acct_data["data"]
            def v(idx): return tr[idx] if len(tr) > idx else "0"
            
            a_spends = format_currency(v(3))
            a_lp = format_num(v(4))
            a_ll = format_num(v(5))
            
            lp_num = pnum(v(4))
            ll_num = pnum(v(5))
            a_dup = f"{((lp_num - ll_num) / lp_num * 100):.1f}%" if lp_num > 0 else "0%"
            dup_class = "warn" if pnum(a_dup) > 20 else ""
            
            a_ffh = format_num(v(6))
            a_adm = format_num(v(7))
            a_inv = format_currency(v(8))
            a_cpl_p = format_currency(v(9))
            a_cpl_l = format_currency(v(10))
            a_cac_ffh = format_currency(v(11))
            a_cac_adm = format_currency(v(12))
            a_arpu = format_currency(v(13))
            
            html += f"""
            <div class="acc-group" id="grp-{cb_id}">
              <label for="{cb_id}" class="acc-header">
                <div class="acc-title">
                  <div>
                    <span class="plat-badge {platform_class}">{platform_icon}</span>
                    <strong>{account}</strong>
                  </div>
                  <span class="chevron"></span>
                </div>
                <div class="acc-summary">
                  <span>💰 {a_spends}</span>
                  <span>🎯 {a_ll} Leads</span>
                  <span class="{dup_class}">⚠️ {a_dup} Dup</span>
                  <span>🎓 {a_adm} Adm</span>
                  <span>🔖 {a_cpl_l} CPL</span>
                </div>
              </label>
              
              <div class="acc-body">
                <div class="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Campaign Name</th>
                        <th class="num">Spends</th>
                        <th class="num">Lead(P)</th>
                        <th class="num">Lead(L)</th>
                        <th class="num">Dup %</th>
                        <th class="num">FFH</th>
                        <th class="num">ADM</th>
                        <th class="num">Inv_Var</th>
                        <th class="num">CPL(P)</th>
                        <th class="num">CPL(L)</th>
                        <th class="num">CAC FFH</th>
                        <th class="num">CAC ADM</th>
                        <th class="num">ARPU</th>
                        <th class="num">L2F</th>
                        <th class="num">L2A</th>
                        <th class="num">F2A</th>
                      </tr>
                    </thead>
                    <tbody>
            """
            
            # Account Total Row (Highlighted)
            html += f"""
                      <tr class="total-row">
                        <td><strong>{account} (Total)</strong></td>
                        <td class="num">{a_spends}</td>
                        <td class="num">{a_lp}</td>
                        <td class="num">{a_ll}</td>
                        <td class="num {dup_class}">{a_dup}</td>
                        <td class="num">{a_ffh}</td>
                        <td class="num">{a_adm}</td>
                        <td class="num">{a_inv}</td>
                        <td class="num">{a_cpl_p}</td>
                        <td class="num">{a_cpl_l}</td>
                        <td class="num">{a_cac_ffh}</td>
                        <td class="num">{a_cac_adm}</td>
                        <td class="num">{a_arpu}</td>
                        <td class="num">{format_pct(v(15))}</td>
                        <td class="num">{format_pct(v(16))}</td>
                        <td class="num">{format_pct(v(17))}</td>
                      </tr>
            """
            
            # Campaigns inside Account
            for cr in acct_data["campaigns"]:
                def cv(idx): return cr[idx] if len(cr) > idx else "0"
                
                c_name = cv(2).strip()
                if not c_name: c_name = "Generic/Unknown"
                
                c_lp_num = pnum(cv(4))
                c_ll_num = pnum(cv(5))
                c_dup = f"{((c_lp_num - c_ll_num) / c_lp_num * 100):.1f}%" if c_lp_num > 0 else "0%"
                c_dup_class = "warn" if pnum(c_dup) > 20 else ""
                
                html += f"""
                      <tr>
                        <td>{c_name}</td>
                        <td class="num">{format_currency(cv(3))}</td>
                        <td class="num">{format_num(cv(4))}</td>
                        <td class="num">{format_num(cv(5))}</td>
                        <td class="num {c_dup_class}">{c_dup}</td>
                        <td class="num">{format_num(cv(6))}</td>
                        <td class="num">{format_num(cv(7))}</td>
                        <td class="num">{format_currency(cv(8))}</td>
                        <td class="num">{format_currency(cv(9))}</td>
                        <td class="num">{format_currency(cv(10))}</td>
                        <td class="num">{format_currency(cv(11))}</td>
                        <td class="num">{format_currency(cv(12))}</td>
                        <td class="num">{format_currency(cv(13))}</td>
                        <td class="num">{format_pct(cv(15))}</td>
                        <td class="num">{format_pct(cv(16))}</td>
                        <td class="num">{format_pct(cv(17))}</td>
                      </tr>
                """
                
            html += """
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
            """
    return html, acc_idx

h_ytd = process_hierarchy(data.get("Campaign Wise - YTD", []))
html_ytd, max_acc_ytd = generate_accordion_html(h_ytd, "ytd")

h_mtd = process_hierarchy(data.get("Campaign Wise - MTD", []))
html_mtd, max_acc_mtd = generate_accordion_html(h_mtd, "mtd")

h_ftd = process_hierarchy(data.get("Campaign Wise - FTD", []))
html_ftd, max_acc_ftd = generate_accordion_html(h_ftd, "ftd")


# --- GENERATE CHECKBOX INPUTS ---
checkboxes_html = ""
for i in range(1, max_acc_ytd + 1): checkboxes_html += f'<input type="checkbox" id="acc-ytd-{i}">\n'
for i in range(1, max_acc_mtd + 1): checkboxes_html += f'<input type="checkbox" id="acc-mtd-{i}">\n'
for i in range(1, max_acc_ftd + 1): checkboxes_html += f'<input type="checkbox" id="acc-ftd-{i}">\n'


# --- DAILY TABLES ---
def make_daily_table(df, x_col, cpl_p, cpl_l, lead_p, lead_l):
    if df.empty: return "<p>No daily data.</p>"
    headers = ["Date", "Lead(P)", "Lead(L)", "Dup %", "CPL(P)", "CPL(L)"]
    html = '<div class="table-wrap"><table><thead><tr>'
    for h in headers: html += f'<th>{h}</th>'
    html += '</tr></thead><tbody>'
    
    for _, row in df.iterrows():
        lp = pnum(row[lead_p])
        ll = pnum(row[lead_l])
        dup = f"{((lp - ll) / lp * 100):.1f}%" if lp > 0 else "0%"
        dup_class = "warn" if pnum(dup) > 20 else ""
        
        html += f"""
        <tr>
          <td>{row[x_col]}</td>
          <td class="num">{lp:g}</td>
          <td class="num">{ll:g}</td>
          <td class="num {dup_class}">{dup}</td>
          <td class="num">₹{pnum(row[cpl_p]):,.0f}</td>
          <td class="num">₹{pnum(row[cpl_l]):,.0f}</td>
        </tr>
        """
    html += '</tbody></table></div>'
    return html

sections = {}

try:
    df_dsa, x_dsa, cpl_p_dsa, cpl_l_dsa, lead_p_dsa, lead_l_dsa = prep_graph_data(data.get("DSA_graph1", []), data.get("DSA_graph2", []))
    sections['dsa'] = f"""
    <div class="card">{create_bar_chart(df_dsa, x_dsa, lead_p_dsa, lead_l_dsa, "DSA Leads Trend", "Panel Leads", "LMS Leads", "#22d98a", "#a78bfa")}</div>
    <div class="card">{create_bar_chart(df_dsa, x_dsa, cpl_p_dsa, cpl_l_dsa, "DSA CPL Trend", "CPL Panel", "CPL LMS", "#f5a623", "#ff4d6d")}</div>
    <h2 class="sec-title">DSA Daily Raw Data</h2>
    {make_daily_table(df_dsa, x_dsa, cpl_p_dsa, cpl_l_dsa, lead_p_dsa, lead_l_dsa)}
    """
except Exception as e: sections['dsa'] = str(e)

try:
    df_brand, x_brand, cpl_p_brand, cpl_l_brand, lead_p_brand, lead_l_brand = prep_graph_data(data.get("Brand graph1", []), data.get("Brand graph2", []))
    sections['brand'] = f"""
    <div class="card">{create_bar_chart(df_brand, x_brand, lead_p_brand, lead_l_brand, "Brand Leads Trend", "Panel Leads", "LMS Leads", "#22d98a", "#a78bfa")}</div>
    <div class="card">{create_bar_chart(df_brand, x_brand, cpl_p_brand, cpl_l_brand, "Brand CPL Trend", "CPL Panel", "CPL LMS", "#f5a623", "#ff4d6d")}</div>
    <h2 class="sec-title">Brand Daily Raw Data</h2>
    {make_daily_table(df_brand, x_brand, cpl_p_brand, cpl_l_brand, lead_p_brand, lead_l_brand)}
    """
except Exception as e: sections['brand'] = str(e)

try:
    df_meta, x_meta, cpl_p_meta, cpl_l_meta, lead_p_meta, lead_l_meta = prep_graph_data(data.get("graph1", []), data.get("graph2", []))
    sections['meta'] = f"""
    <div class="card">{create_bar_chart(df_meta, x_meta, lead_p_meta, lead_l_meta, "Meta Leads Trend", "Panel Leads", "LMS Leads", "#22d98a", "#a78bfa")}</div>
    <div class="card">{create_bar_chart(df_meta, x_meta, cpl_p_meta, cpl_l_meta, "Meta CPL Trend", "CPL Panel", "CPL LMS", "#f5a623", "#ff4d6d")}</div>
    <h2 class="sec-title">Meta Daily Raw Data</h2>
    {make_daily_table(df_meta, x_meta, cpl_p_meta, cpl_l_meta, lead_p_meta, lead_l_meta)}
    """
except Exception as e: sections['meta'] = str(e)


# --- HTML TEMPLATE ---
HTML_TEMPLATE = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0"/>
<title>Degreefyd Pro Dashboard</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; -webkit-tap-highlight-color:transparent; }}
body {{ background: #070b14; color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 13px; line-height: 1.5; padding: 10px; }}
.wrap {{ max-width: 1200px; margin: 0 auto; background: #0f172a; border-radius: 12px; overflow: hidden; border: 1px solid #1e293b; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }}
.hdr {{ background: #020617; padding: 24px 20px; text-align: center; border-bottom: 1px solid #1e293b; }}
.hdr h1 {{ font-size: 22px; font-weight: 800; margin-bottom: 6px; color: #f8fafc; letter-spacing: -0.5px; }}
.hdr p {{ font-size: 13px; color: #94a3b8; }}

/* ── UI TABS ── */
input[type="radio"], input[type="checkbox"] {{ position: absolute; opacity: 0; width: 0; height: 0; pointer-events: none; }}
.tabs {{ display: flex; flex-wrap: wrap; background: #0f172a; border-bottom: 1px solid #1e293b; }}
.tabs label {{ flex: 1 1 20%; text-align: center; padding: 16px 8px; font-size: 13px; font-weight: 700; color: #64748b; border-bottom: 3px solid transparent; cursor: pointer; transition: 0.2s; white-space: nowrap; }}
#t1:checked ~ .wrap .lbl-t1, #t2:checked ~ .wrap .lbl-t2, #t3:checked ~ .wrap .lbl-t3, #t4:checked ~ .wrap .lbl-t4, #t5:checked ~ .wrap .lbl-t5 {{ color: #38bdf8; border-bottom-color: #38bdf8; background: #1e293b; }}

.panel {{ display: none; padding: 15px; }}
#t1:checked ~ .wrap #p1, #t2:checked ~ .wrap #p2, #t3:checked ~ .wrap #p3, #t4:checked ~ .wrap #p4, #t5:checked ~ .wrap #p5 {{ display: block; }}

/* ── ACCORDION (CSS ONLY) ── */
.acc-group {{ background: #020617; border: 1px solid #1e293b; border-radius: 8px; margin-bottom: 12px; overflow: hidden; }}
.acc-header {{ display: block; padding: 16px; cursor: pointer; user-select: none; transition: background 0.2s; }}
.acc-header:active {{ background: #0f172a; }}
.acc-title {{ display: flex; align-items: center; justify-content: space-between; font-size: 15px; font-weight: 700; margin-bottom: 10px; color: #e2e8f0; }}
.acc-summary {{ display: flex; flex-wrap: wrap; gap: 10px; font-size: 11px; color: #94a3b8; }}
.acc-summary span {{ background: #0f172a; padding: 4px 8px; border-radius: 4px; border: 1px solid #1e293b; }}

.plat-badge {{ font-size: 10px; padding: 3px 8px; border-radius: 12px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; margin-right: 8px; }}
.g-badge {{ background: rgba(56,189,248,0.1); color: #38bdf8; border: 1px solid rgba(56,189,248,0.2); }}
.m-badge {{ background: rgba(167,139,250,0.1); color: #a78bfa; border: 1px solid rgba(167,139,250,0.2); }}

.chevron::before {{ content: "▼"; font-size: 10px; color: #64748b; float: right; transition: 0.3s; }}
.acc-body {{ display: none; padding: 0; border-top: 1px solid #1e293b; }}

/* Dynamic Accordion Targeting */
{"".join([f"#acc-ytd-{i}:checked ~ .wrap #grp-acc-ytd-{i} .acc-body {{ display: block; }}\n#acc-ytd-{i}:checked ~ .wrap #grp-acc-ytd-{i} .chevron::before {{ content: '▲'; }}\n" for i in range(1, max_acc_ytd + 1)])}
{"".join([f"#acc-mtd-{i}:checked ~ .wrap #grp-acc-mtd-{i} .acc-body {{ display: block; }}\n#acc-mtd-{i}:checked ~ .wrap #grp-acc-mtd-{i} .chevron::before {{ content: '▲'; }}\n" for i in range(1, max_acc_mtd + 1)])}
{"".join([f"#acc-ftd-{i}:checked ~ .wrap #grp-acc-ftd-{i} .acc-body {{ display: block; }}\n#acc-ftd-{i}:checked ~ .wrap #grp-acc-ftd-{i} .chevron::before {{ content: '▲'; }}\n" for i in range(1, max_acc_ftd + 1)])}

/* ── TABLES & CARDS ── */
.card {{ background: #020617; border: 1px solid #1e293b; border-radius: 10px; margin-bottom: 24px; padding: 10px; }}
.sec-title {{ font-size: 18px; font-weight: 800; color: #f8fafc; margin: 30px 0 16px 0; padding-bottom: 8px; border-bottom: 1px solid #334155; }}
.table-wrap {{ overflow-x: auto; background: #020617; }}
table {{ width: 100%; border-collapse: collapse; text-align: left; }}
th {{ background: #0f172a; color: #94a3b8; font-size: 10px; text-transform: uppercase; font-weight: 800; padding: 12px; border-bottom: 2px solid #1e293b; white-space: nowrap; }}
td {{ padding: 12px; border-bottom: 1px solid #1e293b; font-size: 12px; color: #f8fafc; white-space: nowrap; }}
tr:nth-child(even) td {{ background: #0b1120; }}
.total-row td {{ background: #1e293b !important; font-weight: 700; border-top: 2px solid #334155; }}

.num {{ font-family: ui-monospace, SFMono-Regular, Consolas, monospace; color: #38bdf8; text-align: right; }}
th.num {{ text-align: right; }}
.warn {{ color: #f43f5e; font-weight: bold; }}
</style>
</head>
<body>

<!-- Hidden Radios for Main Tabs -->
<input type="radio" name="tabs" id="t1" checked>
<input type="radio" name="tabs" id="t2">
<input type="radio" name="tabs" id="t3">
<input type="radio" name="tabs" id="t4">

<!-- Hidden Checkboxes for Accordions -->
{checkboxes_html}

<div class="wrap">
  <div class="hdr">
    <h1>Degreefyd Insights Pro</h1>
    <p>Account Drilldowns • Grouped Bar Charts • 100% Native</p>
  </div>
  <div class="tabs">
    <label for="t1" class="lbl-t1">YTD Data</label>
    <label for="t2" class="lbl-t2">MTD Data</label>
    <label for="t3" class="lbl-t3">FTD Data</label>
    <label for="t4" class="lbl-t4">Daily Trends</label>
  </div>
  
  <div id="p1" class="panel">
    <h2 class="sec-title">Year-To-Date (Account Drilldown)</h2>
    {html_ytd}
  </div>
  
  <div id="p2" class="panel">
    <h2 class="sec-title">Month-To-Date (Account Drilldown)</h2>
    {html_mtd}
  </div>
  
  <div id="p3" class="panel">
    <h2 class="sec-title">Fortnight-To-Date (Account Drilldown)</h2>
    {html_ftd}
  </div>
  
  <div id="p4" class="panel">
    <h2 class="sec-title" style="color:#38bdf8; margin-top:0;">Google DSA Campaigns</h2>
    {sections['dsa']}
    <h2 class="sec-title" style="color:#f5a623; margin-top:40px;">Google Brand Campaigns</h2>
    {sections['brand']}
    <h2 class="sec-title" style="color:#a78bfa; margin-top:40px;">Meta Ads</h2>
    {sections['meta']}
  </div>

</div>
</body>
</html>
"""

file_path = "/workspace/Degreefyd_Accordian_Dashboard.html"
with open(file_path, "w", encoding="utf-8") as f: f.write(HTML_TEMPLATE)

# --- SEND VIA WHAPI ---
from dotenv import load_dotenv
load_dotenv("/workspace/.env")
WHAPI_TOKEN = os.getenv("WHAPI_TOKEN")
WHATSAPP_GROUP = os.getenv("WHATSAPP_GROUP")

with open(file_path, "rb") as f: b64 = base64.b64encode(f.read()).decode('utf-8')

payload = {
    "to": WHATSAPP_GROUP,
    "media": f"data:text/html;name=Degreefyd_Insights_Pro.html;base64,{b64}",
    "caption": "📊 **Degreefyd Insights Pro (The Final Polish)**\n\n✅ **Interactive Account Drilldowns:** You can now tap ANY Account name, and it smoothly expands to reveal every Campaign underneath it! All done in pure CSS for WhatsApp Mobile.\n✅ **Platform Badges:** Added crisp `Google Ads` and `Meta Ads` badges to every account card.\n✅ **Bar Charts Replacing Lines:** Switched all the daily trend graphs from messy crossing lines to **Grouped Bar Charts**. It is now mathematically impossible for them to overlap, and trends are crystal clear.\n✅ **Quick Metrics:** Each collapsed Account card shows a snapshot of Spends, Leads, and CPL before you even open it."
}

headers = {"accept": "application/json", "authorization": f"Bearer {WHAPI_TOKEN}", "content-type": "application/json"}

import time
for _ in range(3):
    try:
        resp = requests.post("https://gate.whapi.cloud/messages/document", headers=headers, json=payload, timeout=10)
        print(f"Sent: {resp.status_code == 200}")
        break
    except Exception as e:
        print("Failed, retrying...", e)
        time.sleep(2)
