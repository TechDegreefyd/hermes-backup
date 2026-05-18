import os
import json
import base64
import requests
import pandas as pd
import numpy as np
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN_PATH = "/home/hermeswebui/.hermes/google_token.json"
creds = Credentials.from_authorized_user_file(TOKEN_PATH)
service = build("sheets", "v4", credentials=creds)
spreadsheet_id = "1jzgnRxmmLIe_DAZ7nwHSRXeO6sI4CRxlTatc0T88ukY"

ranges = [
    "'Campaign Wise - YTD'!A1:S250",
    "'Campaign Wise - MTD'!A1:S250",
    "'Campaign Wise - FTD'!A1:S250"
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

# Process Hierarchy
def process_hierarchy(raw_rows):
    if len(raw_rows) < 2: return {}
    hierarchy = {}
    current_platform = "Unknown"
    
    for r in raw_rows[1:]:
        if not r or len(r) < 4: continue
        if str(r[0]).strip() == "Grand Total": continue
        
        if str(r[0]).strip() and "Total" not in str(r[0]):
            current_platform = str(r[0]).strip()
        
        is_account_total = "Total" in str(r[1])
        is_platform_total = "Total" in str(r[0])
        
        if is_platform_total: continue
        
        if is_account_total:
            current_account = str(r[1]).replace("Total", "").strip()
            if current_platform not in hierarchy: hierarchy[current_platform] = {}
            hierarchy[current_platform][current_account] = {"data": r, "campaigns": []}
        else:
            if current_platform in hierarchy and current_account in hierarchy[current_platform]:
                hierarchy[current_platform][current_account]["campaigns"].append(r)
    return hierarchy

def get_val_currency(val):
    if not val or val == '-': return "-"
    if "₹" in str(val): return val
    return format_currency(val)

def generate_accordion_table(hierarchy, prefix):
    html = ""
    acc_idx = 0
    inputs_html = ""
    css_rules = ""
    
    table_content = f"""
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th class="text-left">Campaign</th>
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
    """
    
    for platform, accounts in hierarchy.items():
        p_badge = '<span class="plat-g">G</span>' if "Google" in platform else '<span class="plat-m">M</span>' if "Meta" in platform else ''
        
        for account, acct_data in accounts.items():
            acc_idx += 1
            cb_id = f"{prefix}-{acc_idx}"
            
            inputs_html += f'<input type="checkbox" id="{cb_id}">\n'
            css_rules += f"#{cb_id}:checked ~ .wrap #body-{cb_id} {{ display: table-row-group; }}\n"
            css_rules += f"#{cb_id}:checked ~ .wrap label[for='{cb_id}'] .chev {{ transform: rotate(90deg); }}\n"
            
            tr = acct_data["data"]
            def v(idx): return tr[idx] if len(tr) > idx else "0"
            
            lp = pnum(v(4))
            ll = pnum(v(5))
            dup = ((lp - ll) / lp * 100) if lp > 0 else 0
            dup_str = f"{dup:.1f}%"
            dup_cls = "warn" if dup > 20 else ""
            
            # Master Account Row
            table_content += f"""
            <tbody>
              <tr class="account-row">
                <td class="text-left">
                  <label for="{cb_id}" class="acc-lbl">
                    <span class="chev">▶</span> {p_badge} {account} (Total)
                  </label>
                </td>
                <td class="num">{format_currency(v(3))}</td>
                <td class="num">{format_num(v(4))}</td>
                <td class="num">{format_num(v(5))}</td>
                <td class="num {dup_cls}">{dup_str}</td>
                <td class="num">{format_num(v(6))}</td>
                <td class="num">{format_num(v(7))}</td>
                <td class="num">{format_currency(v(8))}</td>
                <td class="num">{format_currency(v(9))}</td>
                <td class="num">{format_currency(v(10))}</td>
                <td class="num">{get_val_currency(v(11))}</td>
                <td class="num">{get_val_currency(v(12))}</td>
                <td class="num">{get_val_currency(v(13))}</td>
                <td class="num">{format_pct(v(14))}</td>
                <td class="num">{format_pct(v(15))}</td>
                <td class="num">{format_pct(v(16))}</td>
                <td class="num">{format_pct(v(17))}</td>
              </tr>
            </tbody>
            <tbody class="camp-body" id="body-{cb_id}">
            """
            
            # Child Campaign Rows
            for cr in acct_data["campaigns"]:
                def cv(idx): return cr[idx] if len(cr) > idx else "0"
                c_name = cv(2).strip()
                if not c_name: c_name = "Generic / Unknown"
                
                clp = pnum(cv(4))
                cll = pnum(cv(5))
                cdup = ((clp - cll) / clp * 100) if clp > 0 else 0
                cdup_str = f"{cdup:.1f}%"
                cdup_cls = "warn" if cdup > 20 else ""
                
                table_content += f"""
                <tr class="camp-row">
                  <td class="text-left camp-name">↳ {c_name}</td>
                  <td class="num">{format_currency(cv(3))}</td>
                  <td class="num">{format_num(cv(4))}</td>
                  <td class="num">{format_num(cv(5))}</td>
                  <td class="num {cdup_cls}">{cdup_str}</td>
                  <td class="num">{format_num(cv(6))}</td>
                  <td class="num">{format_num(cv(7))}</td>
                  <td class="num">{format_currency(cv(8))}</td>
                  <td class="num">{format_currency(cv(9))}</td>
                  <td class="num">{format_currency(cv(10))}</td>
                  <td class="num">{get_val_currency(cv(11))}</td>
                  <td class="num">{get_val_currency(cv(12))}</td>
                  <td class="num">{get_val_currency(cv(13))}</td>
                  <td class="num">{format_pct(cv(14))}</td>
                  <td class="num">{format_pct(cv(15))}</td>
                  <td class="num">{format_pct(cv(16))}</td>
                  <td class="num">{format_pct(cv(17))}</td>
                </tr>
                """
            table_content += "</tbody>\n"
            
    table_content += "</table></div>"
    return inputs_html, css_rules, table_content


# Generate Sections
in_ytd, css_ytd, html_ytd = generate_accordion_table(process_hierarchy(data.get("Campaign Wise - YTD", [])), "ytd")
in_mtd, css_mtd, html_mtd = generate_accordion_table(process_hierarchy(data.get("Campaign Wise - MTD", [])), "mtd")
in_ftd, css_ftd, html_ftd = generate_accordion_table(process_hierarchy(data.get("Campaign Wise - FTD", [])), "ftd")


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
input[type="radio"], input[type="checkbox"] {{ position: absolute; opacity: 0; width: 0; height: 0; pointer-events: none; }}
.tabs {{ display: flex; flex-wrap: wrap; background: #0f172a; border-bottom: 1px solid #1e293b; }}
.tabs label {{ flex: 1 1 30%; text-align: center; padding: 16px 8px; font-size: 14px; font-weight: 700; color: #64748b; border-bottom: 3px solid transparent; cursor: pointer; transition: 0.2s; white-space: nowrap; }}
#t1:checked ~ .wrap .lbl-t1, #t2:checked ~ .wrap .lbl-t2, #t3:checked ~ .wrap .lbl-t3 {{ color: #38bdf8; border-bottom-color: #38bdf8; background: #1e293b; }}
.panel {{ display: none; padding: 15px; }}
#t1:checked ~ .wrap #p1, #t2:checked ~ .wrap #p2, #t3:checked ~ .wrap #p3 {{ display: block; }}

/* TABLES */
.table-wrap {{ overflow-x: auto; background: #020617; border: 1px solid #334155; border-radius: 8px; }}
table {{ width: 100%; border-collapse: collapse; text-align: right; min-width: 1400px; }}
th {{ background: #0f172a; color: #94a3b8; font-size: 11px; text-transform: uppercase; font-weight: 800; padding: 14px 12px; border-bottom: 2px solid #1e293b; white-space: nowrap; position: sticky; top: 0; z-index: 10; }}
td {{ padding: 12px; border-bottom: 1px solid #1e293b; font-size: 12.5px; color: #f8fafc; white-space: nowrap; }}

/* TYPOGRAPHY */
.num {{ font-family: ui-monospace, SFMono-Regular, Consolas, monospace; color: #e2e8f0; }}
th.num {{ text-align: right; }}
.text-left {{ text-align: left; }}
.warn {{ color: #f43f5e !important; font-weight: bold; }}

/* ACCOUNT ROW (CLICKABLE) */
.account-row td {{ background: #1e293b !important; font-weight: 700; border-top: 3px solid #334155; border-bottom: 3px solid #334155; color: #f8fafc; }}
.acc-lbl {{ display: flex; align-items: center; cursor: pointer; font-size: 13.5px; width: 100%; touch-action: manipulation; user-select: none; }}
.chev {{ display: inline-block; margin-right: 8px; font-size: 10px; color: #94a3b8; transition: transform 0.2s; }}

/* PLATFORM INTENSIFIERS */
.plat-g {{ background: rgba(56,189,248,0.15); color: #38bdf8; border: 1px solid rgba(56,189,248,0.3); padding: 2px 6px; border-radius: 4px; font-size: 10px; margin-right: 8px; }}
.plat-m {{ background: rgba(167,139,250,0.15); color: #a78bfa; border: 1px solid rgba(167,139,250,0.3); padding: 2px 6px; border-radius: 4px; font-size: 10px; margin-right: 8px; }}

/* CAMPAIGN ROW (HIDDEN BY DEFAULT) */
.camp-body {{ display: none; }}
.camp-row td {{ background: #0b1120; color: #94a3b8; border-bottom: 1px solid #1e293b; }}
.camp-name {{ padding-left: 30px !important; color: #cbd5e1; font-size: 12px; }}

/* DYNAMIC EXPAND LOGIC */
{css_ytd}
{css_mtd}
{css_ftd}

</style>
</head>
<body>

<input type="radio" name="tabs" id="t1" checked>
<input type="radio" name="tabs" id="t2">
<input type="radio" name="tabs" id="t3">

{in_ytd}
{in_mtd}
{in_ftd}

<div class="wrap">
  <div class="hdr">
    <h1>Degreefyd Performance Hub</h1>
    <p>Tap Account Names to Expand Campaigns</p>
  </div>
  <div class="tabs">
    <label for="t1" class="lbl-t1">📊 YTD Drilldown</label>
    <label for="t2" class="lbl-t2">📊 MTD Drilldown</label>
    <label for="t3" class="lbl-t3">📊 FTD Drilldown</label>
  </div>
  
  <div id="p1" class="panel">{html_ytd}</div>
  <div id="p2" class="panel">{html_mtd}</div>
  <div id="p3" class="panel">{html_ftd}</div>
</div>

</body>
</html>
"""

file_path = "/workspace/Degreefyd_Perfect_Accordion.html"
with open(file_path, "w", encoding="utf-8") as f: f.write(HTML_TEMPLATE)

# --- SEND VIA WHAPI ---
from dotenv import load_dotenv
load_dotenv("/workspace/.env")
WHAPI_TOKEN = os.getenv("WHAPI_TOKEN")
WHATSAPP_GROUP = os.getenv("WHATSAPP_GROUP")

with open(file_path, "rb") as f: b64 = base64.b64encode(f.read()).decode('utf-8')

payload = {
    "to": WHATSAPP_GROUP,
    "media": f"data:text/html;name=Degreefyd_Perfect_Drilldown.html;base64,{b64}",
    "caption": "💎 **Degreefyd Perfect Drilldown (Final UI)**\n\n✅ **Single Beautiful Table:** The headers align perfectly. It looks EXACTLY like the text you pasted.\n✅ **Tap to Expand:** The Account rows (highlighted with G for Google and M for Meta) are clickable! Tap 'Amity_Partner_001 Total' and it will instantly slide open its campaigns directly underneath it inside the table.\n✅ **No Messy Graphs:** I completely removed the daily trend graphs to keep the UI exclusively focused on your high-precision campaign data.\n✅ **Duplication Formula:** `[(Panel - LMS)/Panel]*100` turns red automatically if it breaches 20%."
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
