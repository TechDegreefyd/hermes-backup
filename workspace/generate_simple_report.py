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

# --- FLAT TABLE GENERATOR ---
def make_flat_table(headers, rows):
    if not rows: return "<p style='padding:20px; color:#94a3b8;'>No data available.</p>"
    
    html = '<div class="table-wrap"><table><thead><tr>'
    for h in headers:
        html += f'<th>{h}</th>'
    html += '</tr></thead><tbody>'
    
    for row in rows:
        if not any(str(c).strip() for c in row): continue
        is_total_row = "Total" in str(row[0]) or "Total" in str(row[1])
        row_class = "total-row" if is_total_row else ""
        
        html += f'<tr class="{row_class}">'
        for i, cell in enumerate(row):
            val = cell if i < len(row) else "-"
            # Identify columns that should be numbers right-aligned
            is_num_col = i > 0 # everything after Campaign/Account name
            css_class = "num" if is_num_col else ""
            
            # Warn on Dup %
            if i == 4 and "%" in str(val) and pnum(val) > 20: 
                css_class += " warn"
                
            html += f'<td class="{css_class}">{val}</td>'
        
        for _ in range(len(headers) - len(row)):
            html += '<td>-</td>'
        html += '</tr>'
    
    html += '</tbody></table></div>'
    return html

def get_campaign_rows_flat(sheet_name):
    raw_rows = data.get(sheet_name, [])
    if len(raw_rows) < 2: return []
    out = []
    
    current_platform = ""
    for r in raw_rows[1:]:
        if not r or len(r) < 4: continue
        if str(r[0]).strip() == "Grand Total": continue
        
        # Track platform to add badges
        if str(r[0]).strip() and "Total" not in str(r[0]):
            current_platform = str(r[0]).strip()
            
        if "Total" in str(r[0]): continue # Skip platform totals
            
        def get_val(idx): return r[idx] if len(r) > idx else "0"
        
        is_account_total = "Total" in str(r[1])
        
        # Build Name Field
        if is_account_total:
            name_text = str(r[1]).strip()
            badge = "🔵" if "Google" in current_platform else "🟣" if "Meta" in current_platform else "⚪"
            display_name = f"{badge} <strong>{name_text}</strong>"
        else:
            camp_name = str(r[2]).strip()
            if not camp_name: camp_name = "Generic/Unknown"
            display_name = f"&nbsp;&nbsp;↳ {camp_name}"
        
        pannel_leads = pnum(get_val(4))
        lms_leads = pnum(get_val(5))
        dup_pct = ((pannel_leads - lms_leads) / pannel_leads * 100) if pannel_leads > 0 else 0
        
        row_data = [
            display_name,                    # Campaign Name
            format_currency(get_val(3)),     # Spends
            format_num(get_val(4)),          # Pannel_Leads
            format_num(get_val(5)),          # Leads_LMS
            f"{dup_pct:.1f}%",               # Dup %
            format_num(get_val(6)),          # FFH
            format_num(get_val(7)),          # ADM
            format_currency(get_val(8)),     # Inv_Var
            format_currency(get_val(9)),     # CPL_Pannel
            format_currency(get_val(10)),    # CPL_LMS
            get_val(11) if "₹" in str(get_val(11)) else format_currency(get_val(11)), # CAC_FFH
            get_val(12) if "₹" in str(get_val(12)) else format_currency(get_val(12)), # CAC_Adm
            get_val(13) if "₹" in str(get_val(13)) else format_currency(get_val(13)), # ARPU
            format_pct(get_val(14)),         # CAC/ARPU
            format_pct(get_val(15)),         # L2F
            format_pct(get_val(16)),         # L2A
            format_pct(get_val(17))          # F2A
        ]
        out.append(row_data)
    return out

full_headers = ["Campaign / Account", "Spends", "Panel Leads", "LMS Leads", "Dup %", "FFH", "ADM", "Inv_Var", "CPL Panel", "CPL LMS", "CAC FFH", "CAC ADM", "ARPU", "CAC/ARPU", "L2F", "L2A", "F2A"]

sections = {}
sections['summary'] = f"""
<h2 class="sec-title">Year-To-Date (YTD)</h2>
{make_flat_table(full_headers, get_campaign_rows_flat("Campaign Wise - YTD"))}
<h2 class="sec-title">Month-To-Date (MTD)</h2>
{make_flat_table(full_headers, get_campaign_rows_flat("Campaign Wise - MTD"))}
<h2 class="sec-title">Fortnight-To-Date (FTD)</h2>
{make_flat_table(full_headers, get_campaign_rows_flat("Campaign Wise - FTD"))}
"""

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
.wrap {{ max-width: 1400px; margin: 0 auto; background: #0f172a; border-radius: 12px; overflow: hidden; border: 1px solid #1e293b; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }}
.hdr {{ background: #020617; padding: 24px 20px; text-align: center; border-bottom: 1px solid #1e293b; }}
.hdr h1 {{ font-size: 22px; font-weight: 800; margin-bottom: 6px; color: #f8fafc; letter-spacing: -0.5px; }}
.hdr p {{ font-size: 13px; color: #94a3b8; }}

input[type="radio"] {{ display: none; }}
.tabs {{ display: flex; flex-wrap: wrap; background: #0f172a; border-bottom: 1px solid #1e293b; }}
.tabs label {{ flex: 1 1 20%; text-align: center; padding: 16px 8px; font-size: 13px; font-weight: 700; color: #64748b; border-bottom: 3px solid transparent; cursor: pointer; transition: 0.2s; white-space: nowrap; }}
#t1:checked ~ .wrap .lbl-t1, #t2:checked ~ .wrap .lbl-t2, #t3:checked ~ .wrap .lbl-t3, #t4:checked ~ .wrap .lbl-t4 {{ color: #38bdf8; border-bottom-color: #38bdf8; background: #1e293b; }}

.panel {{ display: none; padding: 15px; }}
#t1:checked ~ .wrap #p1, #t2:checked ~ .wrap #p2, #t3:checked ~ .wrap #p3, #t4:checked ~ .wrap #p4 {{ display: block; }}

.card {{ background: #020617; border: 1px solid #1e293b; border-radius: 10px; margin-bottom: 24px; padding: 10px; }}
.responsive-img {{ width: 100%; height: auto; display: block; border-radius: 6px; }}

.sec-title {{ font-size: 18px; font-weight: 800; color: #f8fafc; margin: 30px 0 16px 0; padding-bottom: 8px; border-bottom: 1px solid #334155; }}
.table-wrap {{ overflow-x: auto; background: #020617; border: 1px solid #334155; border-radius: 8px; }}
table {{ width: 100%; border-collapse: collapse; text-align: left; min-width: 1000px; }}
th {{ background: #0f172a; color: #94a3b8; font-size: 10px; text-transform: uppercase; font-weight: 800; padding: 12px; border-bottom: 2px solid #1e293b; white-space: nowrap; }}
td {{ padding: 12px; border-bottom: 1px solid #1e293b; font-size: 12px; color: #f8fafc; white-space: nowrap; }}
tr:nth-child(even) td {{ background: #0b1120; }}
.total-row td {{ background: #1e293b !important; font-weight: 700; border-top: 2px solid #334155; color: #e2e8f0; }}

.num {{ font-family: ui-monospace, SFMono-Regular, Consolas, monospace; color: #38bdf8; text-align: right; }}
th.num {{ text-align: right; }}
.warn {{ color: #f43f5e !important; font-weight: bold; }}
</style>
</head>
<body>
<input type="radio" name="tabs" id="t1" checked>
<input type="radio" name="tabs" id="t2">
<input type="radio" name="tabs" id="t3">
<input type="radio" name="tabs" id="t4">

<div class="wrap">
  <div class="hdr">
    <h1>Degreefyd Performance Hub</h1>
    <p>Flat Tables • Exact Columns • Grouped Bar Charts</p>
  </div>
  <div class="tabs">
    <label for="t1" class="lbl-t1">📊 Full Campaign Data</label>
    <label for="t2" class="lbl-t2">🔷 DSA</label>
    <label for="t3" class="lbl-t3">🔶 Brand</label>
    <label for="t4" class="lbl-t4">🟣 Meta</label>
  </div>
  <div id="p1" class="panel">{sections['summary']}</div>
  <div id="p2" class="panel">{sections['dsa']}</div>
  <div id="p3" class="panel">{sections['brand']}</div>
  <div id="p4" class="panel">{sections['meta']}</div>
</div>
</body>
</html>
"""

file_path = "/workspace/Degreefyd_Flat_Dashboard.html"
with open(file_path, "w", encoding="utf-8") as f: f.write(HTML_TEMPLATE)

# --- SEND VIA WHAPI ---
from dotenv import load_dotenv
load_dotenv("/workspace/.env")
WHAPI_TOKEN = os.getenv("WHAPI_TOKEN")
WHATSAPP_GROUP = os.getenv("WHATSAPP_GROUP")

with open(file_path, "rb") as f: b64 = base64.b64encode(f.read()).decode('utf-8')

payload = {
    "to": WHATSAPP_GROUP,
    "media": f"data:text/html;name=Degreefyd_Flat_Tables.html;base64,{b64}",
    "caption": "📊 **Degreefyd Dashboard (Flat Tables)**\n\nI removed the hidden accordion toggles. \n\n✅ **Flat Structure:** The table now exactly mimics your text snippet. Accounts are listed as totals (highlighted in grey with 🔵 Google/🟣 Meta dots), followed directly underneath by their specific indented campaigns (↳).\n✅ **All Columns Visible:** Spends, Panel Leads, LMS Leads, Dup %, FFH, ADM, Inv_Var, CPL Panel, CPL LMS, CAC FFH, CAC ADM, ARPU, CAC/ARPU, L2F, L2A, F2A are right there as you requested.\n✅ **Bar Charts Included:** The clean, non-overlapping grouped bar charts remain for the daily trend tabs."
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
