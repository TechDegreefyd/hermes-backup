import os
import json
import base64
import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# --- FETCH DATA ---
TOKEN_PATH = "/home/hermeswebui/.hermes/google_token.json"
creds = Credentials.from_authorized_user_file(TOKEN_PATH)
service = build("sheets", "v4", credentials=creds)
spreadsheet_id = "1oOJMZqfq31_2DrdEUKsNeforXlikOodyKUJoAgTKsCw"

ranges = [
    "'Campaign Wise - YTD'!A1:K30",
    "'Campaign Wise - MTD'!A1:K30",
    "'Campaign Wise - FTD'!A1:K30",
    "DSA_graph1!A1:F30",
    "DSA_graph2!A1:C30",
    "'Brand graph1'!A1:F30",
    "'Brand graph2'!A1:C30",
    "graph1!A1:F30",
    "graph2!A1:C30"
]

results = service.spreadsheets().values().batchGet(
    spreadsheetId=spreadsheet_id,
    ranges=ranges
).execute()

data = {r["range"].split("!")[0].replace("'", ""): r.get("values", []) for r in results.get("valueRanges", [])}

def pnum(val):
    try:
        return float(str(val).replace(',', '').strip())
    except:
        return 0

def make_table_html(headers, rows, max_val_col_idx=None, highlight_cpl=False):
    if not rows:
        return "<p style='padding:15px; color:#64748b;'>No data available.</p>"
    
    html = '<div class="table-wrap"><table><thead><tr>'
    for h in headers:
        html += f'<th>{h}</th>'
    html += '</tr></thead><tbody>'
    
    # Calculate max value for data bars if requested
    max_val = 1
    if max_val_col_idx is not None and rows:
        max_val = max([pnum(r[max_val_col_idx]) if len(r) > max_val_col_idx else 0 for r in rows]) or 1

    for row in rows:
        if not any(str(c).strip() for c in row): continue # skip empty rows
        html += '<tr>'
        for i, cell in enumerate(row):
            # Fill missing cells
            val = cell if i < len(row) else ""
            
            # Highlight CPL
            if highlight_cpl and "CPL" in str(headers[i]).upper():
                html += f'<td><strong>{val}</strong></td>'
            # Add Data Bar
            elif i == max_val_col_idx:
                num = pnum(val)
                pct = min((num / max_val) * 100, 100)
                html += f'<td><div class="val-num">{val}</div><div class="bar-bg"><div class="bar-fill" style="width:{pct}%"></div></div></td>'
            else:
                html += f'<td>{val}</td>'
        
        # Pad remaining columns
        for _ in range(len(headers) - len(row)):
            html += '<td></td>'
        html += '</tr>'
    
    html += '</tbody></table></div>'
    return html

# 1. Summary Tables
html_ytd = make_table_html(
    ["Platform", "Account", "Spends", "Leads(P)", "Leads(L)", "CPL(P)", "CPL(L)"],
    [[r[0], r[1], r[3], r[4], r[5], r[9], r[10]] for r in data.get("Campaign Wise - YTD", [])[1:] if len(r) > 10],
    max_val_col_idx=2, highlight_cpl=True
)

html_mtd = make_table_html(
    ["Platform", "Account", "Spends", "Leads(P)", "Leads(L)", "CPL(P)", "CPL(L)"],
    [[r[0], r[1], r[3], r[4], r[5], r[9], r[10]] for r in data.get("Campaign Wise - MTD", [])[1:] if len(r) > 10],
    max_val_col_idx=2, highlight_cpl=True
)

html_ftd = make_table_html(
    ["Platform", "Account", "Spends", "Leads(P)", "Leads(L)", "CPL(P)", "CPL(L)"],
    [[r[0], r[1], r[3], r[4], r[5], r[9], r[10]] for r in data.get("Campaign Wise - FTD", [])[1:] if len(r) > 10],
    max_val_col_idx=2, highlight_cpl=True
)

# 2. DSA Data
html_dsa_cpl = make_table_html(["Date", "Spends", "Lead(P)", "Lead(L)", "CPL(P)", "CPL(L)"], data.get("DSA_graph1", [])[1:], max_val_col_idx=1, highlight_cpl=True)
html_dsa_lead = make_table_html(["Date", "Pannel Lead", "LMS Lead"], data.get("DSA_graph2", [])[1:], max_val_col_idx=1)

# 3. Brand Data
html_brand_cpl = make_table_html(["Date", "Spends", "Lead(P)", "Lead(L)", "CPL(P)", "CPL(L)"], data.get("Brand graph1", [])[1:], max_val_col_idx=1, highlight_cpl=True)
html_brand_lead = make_table_html(["Date", "Pannel Lead", "LMS Lead"], data.get("Brand graph2", [])[1:], max_val_col_idx=1)

# 4. Meta Data
html_meta_cpl = make_table_html(["Date", "Spends", "Lead(P)", "Lead(L)", "CPL(P)", "CPL(L)"], data.get("graph1", [])[1:], max_val_col_idx=1, highlight_cpl=True)
html_meta_lead = make_table_html(["Date", "Pannel Lead", "LMS Lead"], data.get("graph2", [])[1:], max_val_col_idx=1)


HTML_TEMPLATE = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0"/>
<title>Degreefyd Data Report</title>
<style>
/* ── STRICT WHATSAPP RULES APPLIED: NO JS, NATIVE SCROLL, CSS TABS ── */
* {{ margin:0; padding:0; box-sizing:border-box; -webkit-tap-highlight-color:transparent; }}
body {{ 
  background: #f4f5f7; color: #1e293b; 
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  font-size: 13px; line-height: 1.5; padding: 15px;
}}

input[type="radio"] {{ position: absolute; opacity: 0; width: 0; height: 0; pointer-events: none; }}
label {{ cursor: pointer; touch-action: manipulation; user-select: none; display: inline-block; }}

.wrap {{ max-width: 900px; margin: 0 auto; background: #ffffff; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); overflow: hidden; }}
.hdr {{ background: #0f172a; color: #fff; padding: 20px; text-align: center; }}
.hdr h1 {{ font-size: 20px; font-weight: 700; margin-bottom: 5px; letter-spacing: -0.5px; }}
.hdr p {{ font-size: 12px; color: #94a3b8; }}

/* ── TABS ── */
.tabs {{ display: flex; background: #f8fafc; border-bottom: 1px solid #e2e8f0; overflow-x: auto; white-space: nowrap; }}
.tabs label {{ flex: 1; text-align: center; padding: 16px 12px; font-size: 13px; font-weight: 600; color: #64748b; border-bottom: 3px solid transparent; transition: all 0.2s; }}

#t1:checked ~ .wrap .lbl-t1,
#t2:checked ~ .wrap .lbl-t2,
#t3:checked ~ .wrap .lbl-t3,
#t4:checked ~ .wrap .lbl-t4 {{
  color: #2563eb; border-bottom-color: #2563eb; background: #eff6ff;
}}

.panel {{ display: none; padding: 20px; }}
#t1:checked ~ .wrap #p1,
#t2:checked ~ .wrap #p2,
#t3:checked ~ .wrap #p3,
#t4:checked ~ .wrap #p4 {{ display: block; }}

/* ── TABLES ── */
.section-title {{ font-size: 16px; font-weight: 700; color: #0f172a; margin: 0 0 15px 0; padding-bottom: 8px; border-bottom: 2px solid #e2e8f0; }}
.table-wrap {{ overflow-x: auto; margin-bottom: 30px; border-radius: 8px; border: 1px solid #e2e8f0; }}
table {{ width: 100%; border-collapse: collapse; text-align: left; min-width: 600px; }}
th {{ background: #f8fafc; color: #475569; font-size: 11px; text-transform: uppercase; font-weight: 700; padding: 12px 16px; border-bottom: 1px solid #e2e8f0; white-space: nowrap; }}
td {{ padding: 12px 16px; border-bottom: 1px solid #f1f5f9; font-size: 13px; color: #334155; white-space: nowrap; }}
tr:nth-child(even) td {{ background: #fafafc; }}

/* ── DATA BARS ── */
.val-num {{ margin-bottom: 4px; font-weight: 600; font-family: ui-monospace, monospace; font-size: 12px; }}
.bar-bg {{ width: 100%; height: 6px; background: #e2e8f0; border-radius: 3px; overflow: hidden; }}
.bar-fill {{ height: 100%; background: #3b82f6; border-radius: 3px; }}

strong {{ color: #0f172a; font-weight: 700; font-family: ui-monospace, monospace; font-size: 12px; }}
</style>
</head>
<body>

<input type="radio" name="tabs" id="t1" checked>
<input type="radio" name="tabs" id="t2">
<input type="radio" name="tabs" id="t3">
<input type="radio" name="tabs" id="t4">

<div class="wrap">
  <div class="hdr">
    <h1>Degreefyd Detailed Data</h1>
    <p>Comprehensive Tables • CSS-Only Tabs • No Overlapping Images</p>
  </div>

  <div class="tabs">
    <label for="t1" class="lbl-t1">📊 Summaries</label>
    <label for="t2" class="lbl-t2">🔷 DSA</label>
    <label for="t3" class="lbl-t3">🔶 Brand</label>
    <label for="t4" class="lbl-t4">🟣 Meta Ads</label>
  </div>

  <div id="p1" class="panel">
    <h2 class="section-title">YTD Overview</h2>
    {html_ytd}
    <h2 class="section-title">MTD Overview</h2>
    {html_mtd}
    <h2 class="section-title">FTD Overview</h2>
    {html_ftd}
  </div>

  <div id="p2" class="panel">
    <h2 class="section-title">DSA Campaigns: Spend & CPL Trends</h2>
    {html_dsa_cpl}
    <h2 class="section-title">DSA Campaigns: Lead Volumes</h2>
    {html_dsa_lead}
  </div>

  <div id="p3" class="panel">
    <h2 class="section-title">Brand Campaigns: Spend & CPL Trends</h2>
    {html_brand_cpl}
    <h2 class="section-title">Brand Campaigns: Lead Volumes</h2>
    {html_brand_lead}
  </div>

  <div id="p4" class="panel">
    <h2 class="section-title">Meta Ads: Spend & CPL Trends</h2>
    {html_meta_cpl}
    <h2 class="section-title">Meta Ads: Lead Volumes</h2>
    {html_meta_lead}
  </div>
</div>

</body>
</html>
"""

# Save Report
file_path = "/workspace/Degreefyd_Detailed_Tables_Report.html"
with open(file_path, "w", encoding="utf-8") as f:
    f.write(HTML_TEMPLATE)
print("Report created.")

# Send via WHAPI
from dotenv import load_dotenv
load_dotenv("/workspace/.env")
WHAPI_TOKEN = os.getenv("WHAPI_TOKEN")
WHATSAPP_GROUP = os.getenv("WHATSAPP_GROUP")

with open(file_path, "rb") as f:
    b64 = base64.b64encode(f.read()).decode('utf-8')

payload = {
    "to": WHATSAPP_GROUP,
    "media": f"data:text/html;name=Degreefyd_Detailed_Tables.html;base64,{b64}",
    "caption": "📊 Degreefyd Full Detailed Data Report\n\n✅ Beautifully spaced tables instead of overlapping graphs.\n✅ CSS Tabs (Summaries, DSA, Brand, Meta).\n✅ Inline visual data bars for quick analysis.\n✅ Flawless rendering inside WhatsApp Mobile."
}

headers = {
    "accept": "application/json",
    "authorization": f"Bearer {WHAPI_TOKEN}",
    "content-type": "application/json"
}

resp = requests.post("https://gate.whapi.cloud/messages/document", headers=headers, json=payload)
print(f"Sent: {resp.status_code == 200}")
