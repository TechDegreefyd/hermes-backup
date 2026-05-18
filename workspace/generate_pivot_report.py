import os
import json
import base64
import requests
import pandas as pd
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN_PATH = "/home/hermeswebui/.hermes/google_token.json"
creds = Credentials.from_authorized_user_file(TOKEN_PATH)
service = build("sheets", "v4", credentials=creds)
spreadsheet_id = "1jzgnRxmmLIe_DAZ7nwHSRXeO6sI4CRxlTatc0T88ukY"

ranges = [
    "'Campaign Wise - YTD'!A1:S300",
    "'Campaign Wise - MTD'!A1:S300",
    "'Campaign Wise - FTD'!A1:S300"
]

results = service.spreadsheets().values().batchGet(spreadsheetId=spreadsheet_id, ranges=ranges).execute()
data = {r["range"].split("!")[0].replace("'", ""): r.get("values", []) for r in results.get("valueRanges", [])}

def pnum(val):
    try: return float(str(val).replace(',', '').strip().replace('%', '').replace('₹', ''))
    except: return 0

def format_currency(val):
    if not val or str(val).strip() == '-': return "-"
    num = pnum(val)
    if "₹" in str(val) or num > 10: return f"₹{num:,.0f}"
    if num == 0 and "0" not in str(val): return str(val)
    return f"₹{num:,.0f}"

def format_pct(val):
    if not val or str(val).strip() == '-': return "-"
    num = pnum(val)
    return f"{num:.1f}%"

def format_num(val):
    if not val or str(val).strip() == '-': return "-"
    num = pnum(val)
    return f"{num:,.0f}"

def build_tree(rows):
    if not rows or len(rows) < 2: return {}
    
    tree = {}
    current_platform = None
    current_account = None
    
    grand_total = None
    
    for r in rows[1:]:
        if not r or len(r) < 4: continue
        
        c_plat = str(r[0]).strip()
        c_acct = str(r[1]).strip()
        c_camp = str(r[2]).strip() if len(r) > 2 else ""
        
        if c_plat == "Grand Total" or c_plat.endswith("Grand Total"):
            grand_total = r
            continue
            
        if c_plat and "Total" in c_plat:
            plat_name = c_plat.replace(" Total", "").strip()
            if plat_name not in tree: tree[plat_name] = {"data": r, "accounts": {}}
            else: tree[plat_name]["data"] = r
            current_platform = plat_name
            continue
        elif c_plat and not "Total" in c_plat:
            current_platform = c_plat
            if current_platform not in tree: tree[current_platform] = {"data": None, "accounts": {}}
            
        if c_acct and "Total" in c_acct:
            acct_name = c_acct.replace(" Total", "").strip()
            if current_platform:
                tree[current_platform]["accounts"][acct_name] = {"data": r, "campaigns": []}
                current_account = acct_name
            continue
            
        if c_camp:
            if current_platform and current_account:
                tree[current_platform]["accounts"][current_account]["campaigns"].append(r)
                
    return tree, grand_total

def generate_pivot_html(tree, grand_total, prefix):
    html = ""
    inputs = ""
    css = ""
    
    headers = [
        "Platform / Account / Campaign", "Spends", "Panel Leads", "LMS Leads", 
        "Dup %", "FFH", "ADM", "Inv_Var", "CPL Panel", "CPL LMS", 
        "CAC FFH", "CAC ADM", "ARPU", "CAC/ARPU", "L2F", "L2A", "F2A"
    ]
    
    html += '<div class="table-wrap"><table><thead><tr>'
    for h in headers:
        align = "text-left" if h == "Platform / Account / Campaign" else "num"
        html += f'<th class="{align}">{h}</th>'
    html += '</tr></thead><tbody>'
    
    p_idx = 0
    a_idx = 0
    
    for plat_name, plat_data in tree.items():
        p_idx += 1
        p_id = f"p-{prefix}-{p_idx}"
        
        inputs += f'<input type="checkbox" id="{p_id}" checked>\n'
        css += f"#{p_id}:checked ~ .wrap .child-of-{p_id} {{ display: table-row; }}\n"
        css += f"#{p_id}:checked ~ .wrap label[for='{p_id}'] .box::before {{ content: '-'; }}\n"
        
        tr = plat_data["data"]
        if not tr: tr = [""] * 18 
        def v(idx): return tr[idx] if len(tr) > idx else "0"
        
        icon = "🔵" if "Google" in plat_name else "🟣" if "Meta" in plat_name else ""
        
        html += f'''
        <tr class="plat-row">
            <td class="text-left">
                <label for="{p_id}" class="exp-lbl">
                    <span class="box"></span> {icon} <strong>{plat_name} Total</strong>
                </label>
            </td>
            <td class="num"><strong>{format_currency(v(3))}</strong></td>
            <td class="num"><strong>{format_num(v(4))}</strong></td>
            <td class="num"><strong>{format_num(v(5))}</strong></td>
            <td class="num"><strong>-</strong></td>
            <td class="num"><strong>{format_num(v(6))}</strong></td>
            <td class="num"><strong>{format_num(v(7))}</strong></td>
            <td class="num"><strong>{format_currency(v(8))}</strong></td>
            <td class="num"><strong>{format_currency(v(9))}</strong></td>
            <td class="num"><strong>{format_currency(v(10))}</strong></td>
            <td class="num"><strong>{get_val_currency(v(11))}</strong></td>
            <td class="num"><strong>{get_val_currency(v(12))}</strong></td>
            <td class="num"><strong>{get_val_currency(v(13))}</strong></td>
            <td class="num"><strong>{format_pct(v(14))}</strong></td>
            <td class="num"><strong>{format_pct(v(15))}</strong></td>
            <td class="num"><strong>{format_pct(v(16))}</strong></td>
            <td class="num"><strong>{format_pct(v(17))}</strong></td>
        </tr>
        '''
        
        for acct_name, acct_data in plat_data["accounts"].items():
            a_idx += 1
            a_id = f"a-{prefix}-{a_idx}"
            
            inputs += f'<input type="checkbox" id="{a_id}">\n'
            css += f"#{a_id}:checked ~ .wrap .child-of-{a_id} {{ display: table-row; }}\n"
            css += f"#{a_id}:checked ~ .wrap label[for='{a_id}'] .box::before {{ content: '-'; }}\n"
            
            ar = acct_data["data"]
            def av(idx): return ar[idx] if len(ar) > idx else "0"
            
            lp = pnum(av(4))
            ll = pnum(av(5))
            dup = ((lp - ll) / lp * 100) if lp > 0 else 0
            dup_cls = "warn" if dup > 20 else ""
            
            html += f'''
            <tr class="acct-row child-of-{p_id}">
                <td class="text-left" style="padding-left: 30px;">
                    <label for="{a_id}" class="exp-lbl">
                        <span class="box"></span> <strong>{acct_name} Total</strong>
                    </label>
                </td>
                <td class="num"><strong>{format_currency(av(3))}</strong></td>
                <td class="num"><strong>{format_num(av(4))}</strong></td>
                <td class="num"><strong>{format_num(av(5))}</strong></td>
                <td class="num {dup_cls}"><strong>{dup:.1f}%</strong></td>
                <td class="num"><strong>{format_num(av(6))}</strong></td>
                <td class="num"><strong>{format_num(av(7))}</strong></td>
                <td class="num"><strong>{format_currency(av(8))}</strong></td>
                <td class="num"><strong>{format_currency(av(9))}</strong></td>
                <td class="num"><strong>{format_currency(av(10))}</strong></td>
                <td class="num"><strong>{get_val_currency(av(11))}</strong></td>
                <td class="num"><strong>{get_val_currency(av(12))}</strong></td>
                <td class="num"><strong>{get_val_currency(av(13))}</strong></td>
                <td class="num"><strong>{format_pct(av(14))}</strong></td>
                <td class="num"><strong>{format_pct(av(15))}</strong></td>
                <td class="num"><strong>{format_pct(av(16))}</strong></td>
                <td class="num"><strong>{format_pct(av(17))}</strong></td>
            </tr>
            '''
            
            for cr in acct_data["campaigns"]:
                def cv(idx): return cr[idx] if len(cr) > idx else "0"
                c_name = cv(2).strip() if len(cr)>2 and cr[2].strip() else "Unknown Campaign"
                
                clp = pnum(cv(4))
                cll = pnum(cv(5))
                cdup = ((clp - cll) / clp * 100) if clp > 0 else 0
                cdup_cls = "warn" if cdup > 20 else ""
                
                html += f'''
                <tr class="camp-row child-of-{a_id}">
                    <td class="text-left" style="padding-left: 60px;">{c_name}</td>
                    <td class="num">{format_currency(cv(3))}</td>
                    <td class="num">{format_num(cv(4))}</td>
                    <td class="num">{format_num(cv(5))}</td>
                    <td class="num {cdup_cls}">{cdup:.1f}%</td>
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
                '''
                
    if grand_total:
        def gv(idx): return grand_total[idx] if len(grand_total) > idx else "0"
        html += f'''
        <tr class="grand-total">
            <td class="text-left"><strong>Grand Total</strong></td>
            <td class="num"><strong>{format_currency(gv(3))}</strong></td>
            <td class="num"><strong>{format_num(gv(4))}</strong></td>
            <td class="num"><strong>{format_num(gv(5))}</strong></td>
            <td class="num"><strong>-</strong></td>
            <td class="num"><strong>{format_num(gv(6))}</strong></td>
            <td class="num"><strong>{format_num(gv(7))}</strong></td>
            <td class="num"><strong>{format_currency(gv(8))}</strong></td>
            <td class="num"><strong>{format_currency(gv(9))}</strong></td>
            <td class="num"><strong>{format_currency(gv(10))}</strong></td>
            <td class="num"><strong>{get_val_currency(gv(11))}</strong></td>
            <td class="num"><strong>{get_val_currency(gv(12))}</strong></td>
            <td class="num"><strong>{get_val_currency(gv(13))}</strong></td>
            <td class="num"><strong>{format_pct(gv(14))}</strong></td>
            <td class="num"><strong>{format_pct(gv(15))}</strong></td>
            <td class="num"><strong>{format_pct(gv(16))}</strong></td>
            <td class="num"><strong>{format_pct(gv(17))}</strong></td>
        </tr>
        '''
        
    html += '</tbody></table></div>'
    return inputs, css, html

def get_val_currency(val):
    if not val or val == '-': return "-"
    if "₹" in str(val): return val
    return format_currency(val)

tree_ytd, gt_ytd = build_tree(data.get("Campaign Wise - YTD", []))
in_ytd, css_ytd, html_ytd = generate_pivot_html(tree_ytd, gt_ytd, "ytd")

tree_mtd, gt_mtd = build_tree(data.get("Campaign Wise - MTD", []))
in_mtd, css_mtd, html_mtd = generate_pivot_html(tree_mtd, gt_mtd, "mtd")

tree_ftd, gt_ftd = build_tree(data.get("Campaign Wise - FTD", []))
in_ftd, css_ftd, html_ftd = generate_pivot_html(tree_ftd, gt_ftd, "ftd")

HTML_TEMPLATE = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0"/>
<title>Degreefyd Pivot Dashboard</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; -webkit-tap-highlight-color:transparent; }}
body {{ background: #f8fafc; color: #0f172a; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 13px; line-height: 1.5; padding: 10px; }}
.wrap {{ max-width: 1400px; margin: 0 auto; background: #ffffff; border-radius: 8px; border: 1px solid #cbd5e1; box-shadow: 0 4px 15px rgba(0,0,0,0.05); overflow: hidden; }}

.hdr {{ background: #1e293b; padding: 16px 20px; text-align: left; }}
.hdr h1 {{ font-size: 20px; font-weight: 700; color: #f8fafc; margin-bottom: 4px; }}
.hdr p {{ font-size: 12px; color: #94a3b8; }}

/* TABS */
input[type="radio"], input[type="checkbox"] {{ position: absolute; opacity: 0; width: 0; height: 0; pointer-events: none; }}
.tabs {{ display: flex; flex-wrap: wrap; background: #f1f5f9; border-bottom: 1px solid #cbd5e1; }}
.tabs label {{ flex: 1 1 30%; text-align: center; padding: 14px; font-size: 13px; font-weight: 700; color: #475569; border-bottom: 3px solid transparent; cursor: pointer; transition: 0.2s; }}
#t1:checked ~ .wrap .lbl-t1, #t2:checked ~ .wrap .lbl-t2, #t3:checked ~ .wrap .lbl-t3 {{ color: #2563eb; border-bottom-color: #2563eb; background: #ffffff; }}

.panel {{ display: none; padding: 0; }}
#t1:checked ~ .wrap #p1, #t2:checked ~ .wrap #p2, #t3:checked ~ .wrap #p3 {{ display: block; }}

/* PIVOT TABLE STYLING */
.table-wrap {{ overflow-x: auto; }}
table {{ width: 100%; border-collapse: collapse; min-width: 1200px; border-bottom: 1px solid #cbd5e1; }}
th {{ background: #f1f5f9; color: #334155; font-size: 11px; text-transform: uppercase; font-weight: 800; padding: 10px 12px; border-bottom: 2px solid #cbd5e1; white-space: nowrap; position: sticky; top: 0; z-index: 10; border-right: 1px solid #e2e8f0; }}
td {{ padding: 10px 12px; border-bottom: 1px solid #e2e8f0; font-size: 12.5px; color: #0f172a; white-space: nowrap; border-right: 1px solid #e2e8f0; }}

/* ROW HIERARCHY */
.plat-row td {{ background: #f8fafc; border-top: 2px solid #cbd5e1; }}
.acct-row td {{ background: #ffffff; }}
.camp-row td {{ background: #ffffff; color: #475569; }}
.grand-total td {{ background: #e2e8f0; font-weight: 800; border-top: 2px solid #94a3b8; font-size: 14px; }}

.num {{ font-family: ui-monospace, SFMono-Regular, Consolas, monospace; text-align: right; }}
th.num {{ text-align: right; }}
.text-left {{ text-align: left; }}
.warn {{ color: #dc2626 !important; font-weight: bold; background: #fef2f2 !important; }}

/* EXPAND/COLLAPSE UI */
.exp-lbl {{ cursor: pointer; display: flex; align-items: center; user-select: none; touch-action: manipulation; }}
.box {{ display: inline-flex; align-items: center; justify-content: center; width: 14px; height: 14px; border: 1px solid #94a3b8; background: #fff; margin-right: 8px; font-weight: bold; font-family: monospace; font-size: 10px; color: #0f172a; border-radius: 2px; }}
.box::before {{ content: "+"; }}

/* HIDE CHILDREN BY DEFAULT */
.child-of-p-ytd-1, .child-of-p-ytd-2, .child-of-p-ytd-3, .child-of-p-ytd-4, .child-of-p-ytd-5,
.child-of-a-ytd-1, .child-of-a-ytd-2, .child-of-a-ytd-3, .child-of-a-ytd-4, .child-of-a-ytd-5, .child-of-a-ytd-6, .child-of-a-ytd-7, .child-of-a-ytd-8, .child-of-a-ytd-9, .child-of-a-ytd-10, .child-of-a-ytd-11, .child-of-a-ytd-12, .child-of-a-ytd-13, .child-of-a-ytd-14, .child-of-a-ytd-15,
.child-of-p-mtd-1, .child-of-p-mtd-2, .child-of-p-mtd-3, .child-of-p-mtd-4, .child-of-p-mtd-5,
.child-of-a-mtd-1, .child-of-a-mtd-2, .child-of-a-mtd-3, .child-of-a-mtd-4, .child-of-a-mtd-5, .child-of-a-mtd-6, .child-of-a-mtd-7, .child-of-a-mtd-8, .child-of-a-mtd-9, .child-of-a-mtd-10, .child-of-a-mtd-11, .child-of-a-mtd-12, .child-of-a-mtd-13, .child-of-a-mtd-14, .child-of-a-mtd-15,
.child-of-p-ftd-1, .child-of-p-ftd-2, .child-of-p-ftd-3, .child-of-p-ftd-4, .child-of-p-ftd-5,
.child-of-a-ftd-1, .child-of-a-ftd-2, .child-of-a-ftd-3, .child-of-a-ftd-4, .child-of-a-ftd-5, .child-of-a-ftd-6, .child-of-a-ftd-7, .child-of-a-ftd-8, .child-of-a-ftd-9, .child-of-a-ftd-10, .child-of-a-ftd-11, .child-of-a-ftd-12, .child-of-a-ftd-13, .child-of-a-ftd-14, .child-of-a-ftd-15 {{
    display: none;
}}

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
    <h1>Degreefyd Pivot Dashboard</h1>
    <p>Excel-Style Nested Hierarchy • Tap [+] to Expand</p>
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

file_path = "/workspace/Degreefyd_Pivot_Dashboard.html"
with open(file_path, "w", encoding="utf-8") as f: f.write(HTML_TEMPLATE)

from dotenv import load_dotenv
load_dotenv("/workspace/.env")
WHAPI_TOKEN = os.getenv("WHAPI_TOKEN")
WHATSAPP_GROUP = os.getenv("WHATSAPP_GROUP")

with open(file_path, "rb") as f: b64 = base64.b64encode(f.read()).decode('utf-8')

payload = {
    "to": WHATSAPP_GROUP,
    "media": f"data:text/html;name=Degreefyd_Pivot_Table.html;base64,{b64}",
    "caption": "📊 **Degreefyd Pivot Table (Exact Match)**\n\nI analyzed the screenshot you sent. You wanted the exact **Pivot Table UI** with the `[+]` and `[-]` expand/collapse boxes, nested indentations, and the exact column layout.\n\n✅ **Pivot Hierarchy:** `[+] Google Ads` -> `[+] Amity_Partner_001 Total` -> `Campaign Rows`.\n✅ **Tap the [+] Boxes:** Tap any `[+]` box in the first column to expand the rows beneath it. The box will turn into a `[-]`.\n✅ **Light Theme:** Used the clean, professional white/grey Excel aesthetic from your screenshot.\n✅ **Duplication & All Columns Included:** Includes the formula, ARPU, L2A, etc."
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
