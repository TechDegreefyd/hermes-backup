import os
import json
import base64
import requests
import pandas as pd
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import warnings
warnings.filterwarnings('ignore')

TOKEN_PATH = "/home/hermeswebui/.hermes/google_token.json"
creds = Credentials.from_authorized_user_file(TOKEN_PATH)
service = build("sheets", "v4", credentials=creds)
spreadsheet_id = "1jzgnRxmmLIe_DAZ7nwHSRXeO6sI4CRxlTatc0T88ukY"

print("Fetching data...")
res = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range="'Day Wise CAC Report'!A1:S10000").execute()
rows = res.get('values', [])

# Parse headers correctly from row index 1
headers = [str(h).strip() for h in rows[1]]
df = pd.DataFrame(rows[2:], columns=headers)

# Clean numeric columns
num_cols = ['Spends', 'Pannel_Lead', 'Lead_LMS', 'FFH', 'Adm', 'Invoicing_Var']
for c in num_cols:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c].astype(str).str.replace(',', '').replace('₹', '').replace('%', ''), errors='coerce').fillna(0)

# Filter empty rows
df = df[df['Account'].astype(str).str.strip() != '']
df = df[df['Account'].astype(str).str.lower() != 'nan']
df = df[df['Platform'].astype(str).str.strip() != '']
df = df[df['Platform'].astype(str).str.lower() != 'nan']

print(f"Dataframe loaded. Total valid rows: {len(df)}")

html_content = ""

# 1. Section for Platforms
platforms = df['Platform'].unique()
for plat in sorted(platforms, reverse=True): # Usually puts Meta Ads before Google Ads
    plat_df = df[df['Platform'] == plat]
    p_icon = "🟣" if "Meta" in plat else "🔵" if "Google" in plat else "⚪"
    
    html_content += f'<h2 class="sec-title">{p_icon} {plat}</h2>\n'
    
    # 2. Account Accordions
    accounts = plat_df['Account'].unique()
    for acct in accounts:
        acct_df = plat_df[plat_df['Account'] == acct]
        
        # Account Totals
        a_spends = acct_df['Spends'].sum()
        a_pleads = acct_df['Pannel_Lead'].sum()
        a_lleads = acct_df['Lead_LMS'].sum()
        
        html_content += f'''
        <details class="acc-card">
            <summary class="acc-summary">
                <div class="sum-left">
                    <span class="p-icon">{p_icon}</span>
                    <span class="acc-name">{acct}</span>
                </div>
                <div class="sum-right">
                    <span class="pill">Spends: ₹{a_spends:,.0f}</span>
                    <span class="pill">LMS Leads: {a_lleads:,.0f}</span>
                </div>
            </summary>
            <div class="table-wrap">
                <table>
                    <thead>
                        <tr>
                            <th class="text-left sticky-col">Campaign / Date</th>
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
        
        # 3. Campaign Groups
        campaigns = acct_df['Campaign'].unique()
        for camp in campaigns:
            camp_df = acct_df[acct_df['Campaign'] == camp]
            camp_name = camp if str(camp).strip() else "Generic / Unknown"
            
            # Campaign Totals
            c_spends = camp_df['Spends'].sum()
            c_pleads = camp_df['Pannel_Lead'].sum()
            c_lleads = camp_df['Lead_LMS'].sum()
            c_ffh = camp_df['FFH'].sum()
            c_adm = camp_df['Adm'].sum()
            c_inv = camp_df['Invoicing_Var'].sum()
            
            c_dup = ((c_pleads - c_lleads) / c_pleads * 100) if c_pleads > 0 else 0
            c_cpl_p = c_spends / c_pleads if c_pleads > 0 else 0
            c_cpl_l = c_spends / c_lleads if c_lleads > 0 else 0
            c_cac_f = c_spends / c_ffh if c_ffh > 0 else 0
            c_cac_a = c_spends / c_adm if c_adm > 0 else 0
            c_dup_cls = "warn" if c_dup > 20 else ""
            
            html_content += f'''
                    <tr class="total-row">
                        <td class="text-left sticky-col" style="white-space:normal; min-width:250px;"><strong>{camp_name}</strong></td>
                        <td class="text-left"><strong>(Campaign Total)</strong></td>
                        <td class="num"><strong>₹{c_spends:,.0f}</strong></td>
                        <td class="num"><strong>{c_pleads:,.0f}</strong></td>
                        <td class="num"><strong>{c_lleads:,.0f}</strong></td>
                        <td class="num {c_dup_cls}"><strong>{c_dup:.1f}%</strong></td>
                        <td class="num"><strong>{c_ffh:,.0f}</strong></td>
                        <td class="num"><strong>{c_adm:,.0f}</strong></td>
                        <td class="num"><strong>₹{c_inv:,.0f}</strong></td>
                        <td class="num"><strong>₹{c_cpl_p:,.0f}</strong></td>
                        <td class="num"><strong>₹{c_cpl_l:,.0f}</strong></td>
                        <td class="num"><strong>₹{c_cac_f:,.0f}</strong></td>
                        <td class="num"><strong>₹{c_cac_a:,.0f}</strong></td>
                    </tr>
            '''
            
            # 4. Daily Ad Rows
            camp_df['Date_Parsed'] = pd.to_datetime(camp_df['Date'], errors='coerce')
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
                
                html_content += f'''
                    <tr>
                        <td class="text-left sticky-col" style="padding-left: 30px; color: #94a3b8;">↳ {row.get('Date', '-')}</td>
                        <td class="text-left" style="color: #cbd5e1; white-space:normal; min-width:250px;">{row.get('Ad Name', '-')}</td>
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
                
        html_content += '''
                    </tbody>
                </table>
            </div>
        </details>
        '''

HTML_TEMPLATE = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0"/>
<title>Degreefyd Structured Tracker</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; -webkit-tap-highlight-color:transparent; }}
body {{ background: #070b14; color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 13px; line-height: 1.5; padding: 15px; }}
.wrap {{ max-width: 1600px; margin: 0 auto; }}
.hdr {{ text-align: center; margin-bottom: 30px; }}
.hdr h1 {{ font-size: 26px; font-weight: 800; color: #f8fafc; margin-bottom: 5px; }}
.hdr p {{ color: #94a3b8; }}

.sec-title {{ font-size: 22px; font-weight: 800; color: #f8fafc; margin: 40px 0 16px 0; padding-bottom: 10px; border-bottom: 2px solid #1e293b; display: flex; align-items: center; gap: 10px; }}

.acc-card {{ background: #0f172a; border: 1px solid #1e293b; border-radius: 10px; margin-bottom: 16px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }}
.acc-summary {{ display: flex; align-items: center; justify-content: space-between; padding: 18px 20px; font-weight: 600; cursor: pointer; color: #f8fafc; list-style: none; transition: background 0.2s; }}
.acc-summary:active {{ background: #1e293b; }}
.acc-summary::-webkit-details-marker {{ display: none; }}
.acc-summary::after {{ content: "▼"; color: #64748b; font-size: 12px; margin-left: 15px; }}
details[open] .acc-summary::after {{ content: "▲"; }}
details[open] .acc-summary {{ border-bottom: 1px solid #1e293b; background: #020617; }}

.sum-left {{ display: flex; align-items: center; gap: 12px; font-size: 16px; font-weight: 800; letter-spacing: -0.3px; }}
.sum-right {{ display: flex; gap: 10px; font-size: 12px; }}
.pill {{ background: #1e293b; padding: 6px 12px; border-radius: 6px; border: 1px solid #334155; color: #cbd5e1; font-weight: 700; }}

.table-wrap {{ overflow-x: auto; background: #020617; }}
table {{ width: 100%; border-collapse: collapse; text-align: right; min-width: 1400px; }}
th {{ background: #0f172a; color: #94a3b8; font-size: 11px; text-transform: uppercase; font-weight: 800; padding: 14px; border-bottom: 2px solid #1e293b; white-space: nowrap; position: sticky; top: 0; z-index: 10; }}
td {{ padding: 14px; border-bottom: 1px solid #1e293b; font-size: 13px; color: #f8fafc; white-space: nowrap; }}
tr:nth-child(even) td {{ background: #0b1120; }}

.total-row td {{ background: #1e293b !important; font-weight: 700; border-top: 2px solid #334155; border-bottom: 2px solid #334155; color: #f8fafc; font-size: 14px; }}
.sticky-col {{ position: sticky; left: 0; background: inherit; z-index: 5; border-right: 2px solid #1e293b; box-shadow: 2px 0 5px rgba(0,0,0,0.2); }}
th.sticky-col {{ z-index: 15; }}

.num {{ font-family: ui-monospace, SFMono-Regular, Consolas, monospace; color: #38bdf8; text-align: right; }}
th.num {{ text-align: right; }}
.text-left {{ text-align: left; }}
.warn {{ color: #f43f5e !important; font-weight: bold; }}

</style>
</head>
<body>
<div class="wrap">
  <div class="hdr">
    <h1>Degreefyd Campaign Master Tracker</h1>
    <p>Platform ➔ Account ➔ Campaign ➔ Ad Name Breakdown</p>
  </div>
  {html_content}
</div>
</body>
</html>
"""

file_path = "/workspace/Degreefyd_Campaign_Tracker.html"
with open(file_path, "w", encoding="utf-8") as f: f.write(HTML_TEMPLATE)
print("HTML Generated!")

# --- SEND VIA WHAPI ---
from dotenv import load_dotenv
load_dotenv("/workspace/.env")
WHAPI_TOKEN = os.getenv("WHAPI_TOKEN")
WHATSAPP_GROUP = os.getenv("WHATSAPP_GROUP")

with open(file_path, "rb") as f: b64 = base64.b64encode(f.read()).decode('utf-8')

payload = {
    "to": WHATSAPP_GROUP,
    "media": f"data:text/html;name=Degreefyd_Campaign_Tracker.html;base64,{b64}",
    "caption": "👑 **Degreefyd Campaign Master Tracker**\n\nI perfectly understood your requirement: **Sections for Platforms -> Accounts -> Campaigns -> Daily Ad rows**.\n\n✅ **Structure Fixed:** There is now a major section header for `🟣 Meta Ads` and `🔵 Google Ads`.\n✅ **Account Accordions:** Each account is a clickable card (as requested, taking inspiration from the uploaded HTML).\n✅ **Campaign Calculations:** When you open an account, you see a **Bold Campaign Total Row** showing the calculated totals (Spends, Leads, CPL) specifically for that campaign.\n✅ **Daily Ad Breakdown:** Immediately under the Campaign Total row, you see the exact daily ad performance rows (Date & Ad Name), indented neatly.\n✅ **The Columns:** Extracted exactly from the raw data sheet (`Spends`, `Pannel`, `LMS`, `Dup%`, `CPL`, `CAC`, etc.)"
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