import os
import json
import base64
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN_PATH = "/home/hermeswebui/.hermes/google_token.json"
creds = Credentials.from_authorized_user_file(TOKEN_PATH)
service = build("sheets", "v4", credentials=creds)
spreadsheet_id = "1jzgnRxmmLIe_DAZ7nwHSRXeO6sI4CRxlTatc0T88ukY"

res = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range="'Day Wise CAC Report'!A1:S5000").execute()
rows = res.get('values', [])

headers = rows[1]
data = rows[2:]
df = pd.DataFrame(data, columns=headers)

def clean_num(x):
    try: return float(str(x).replace(',', '').replace('₹', '').replace('%', '').strip())
    except: return 0.0

num_cols = ['Spends', 'Pannel_Lead', 'Lead_LMS', 'FFH', 'Adm', 'Invoicing_Var']
for c in num_cols:
    if c in df.columns:
        df[c] = df[c].apply(clean_num)

df = df[df['Account'].astype(str).str.strip() != '']
df = df[df['Date'].astype(str).str.strip() != '']

df['Date_Parsed'] = pd.to_datetime(df['Date'], errors='coerce')
max_date = df['Date_Parsed'].max()
if pd.notnull(max_date):
    df = df[df['Date_Parsed'] >= (max_date - timedelta(days=14))]

df = df.sort_values(by=['Account', 'Date_Parsed'], ascending=[True, False])

html_accounts = ""
inputs_html = ""
css_rules = ""

acc_idx = 0
accounts = df['Account'].unique()

for acct in accounts:
    acct_df = df[df['Account'] == acct]
    if acct_df.empty: continue
    
    acc_idx += 1
    cb_id = f"acc-{acc_idx}"
    
    t_spends = acct_df['Spends'].sum()
    t_pleads = acct_df['Pannel_Lead'].sum()
    t_lleads = acct_df['Lead_LMS'].sum()
    t_ffh = acct_df['FFH'].sum()
    t_adm = acct_df['Adm'].sum()
    t_inv = acct_df['Invoicing_Var'].sum()
    
    t_dup = ((t_pleads - t_lleads) / t_pleads * 100) if t_pleads > 0 else 0
    t_cpl_p = t_spends / t_pleads if t_pleads > 0 else 0
    t_cpl_l = t_spends / t_lleads if t_lleads > 0 else 0
    t_cac_f = t_spends / t_ffh if t_ffh > 0 else 0
    t_cac_a = t_spends / t_adm if t_adm > 0 else 0
    
    dup_cls = "warn" if t_dup > 20 else ""
    
    plat = acct_df['Platform'].iloc[0]
    p_badge = '<span class="plat-g">🔵 Google Ads</span>' if "Google" in str(plat) else '<span class="plat-m">🟣 Meta Ads</span>' if "Meta" in str(plat) else ''
    
    inputs_html += f'<input type="checkbox" id="{cb_id}">\n'
    css_rules += f"#{cb_id}:checked ~ .wrap #body-{cb_id} {{ display: table-row-group; }}\n"
    css_rules += f"#{cb_id}:checked ~ .wrap label[for='{cb_id}'] .chev {{ transform: rotate(90deg); }}\n"
    
    html_accounts += f'''
    <tbody>
      <tr class="account-row">
        <td class="text-left" colspan="4">
          <label for="{cb_id}" class="exp-lbl">
            <span class="chev">▶</span> {p_badge} <strong>{acct} (Total - Last 15 Days)</strong>
          </label>
        </td>
        <td class="num"><strong>₹{t_spends:,.0f}</strong></td>
        <td class="num"><strong>{t_pleads:,.0f}</strong></td>
        <td class="num"><strong>{t_lleads:,.0f}</strong></td>
        <td class="num {dup_cls}"><strong>{t_dup:.1f}%</strong></td>
        <td class="num"><strong>{t_ffh:,.0f}</strong></td>
        <td class="num"><strong>{t_adm:,.0f}</strong></td>
        <td class="num"><strong>₹{t_inv:,.0f}</strong></td>
        <td class="num"><strong>₹{t_cpl_p:,.0f}</strong></td>
        <td class="num"><strong>₹{t_cpl_l:,.0f}</strong></td>
        <td class="num"><strong>₹{t_cac_f:,.0f}</strong></td>
        <td class="num"><strong>₹{t_cac_a:,.0f}</strong></td>
      </tr>
    </tbody>
    <tbody class="camp-body" id="body-{cb_id}">
    '''
    
    for _, row in acct_df.iterrows():
        rp = clean_num(row.get('Pannel_Lead', 0))
        rl = clean_num(row.get('Lead_LMS', 0))
        rdup = ((rp - rl) / rp * 100) if rp > 0 else 0
        rdup_cls = "warn" if rdup > 20 else ""
        
        rspends = clean_num(row.get('Spends', 0))
        rcpl_p = rspends / rp if rp > 0 else 0
        rcpl_l = rspends / rl if rl > 0 else 0
        
        rffh = clean_num(row.get('FFH', 0))
        radm = clean_num(row.get('Adm', 0))
        rinv = clean_num(row.get('Invoicing_Var', 0))
        
        rcac_f = rspends / rffh if rffh > 0 else 0
        rcac_a = rspends / radm if radm > 0 else 0
        
        html_accounts += f'''
        <tr class="camp-row">
          <td class="text-center">{row.get('Date', '-')}</td>
          <td class="text-center">{row.get('Type', '-')}</td>
          <td class="text-left camp-name">{row.get('Campaign', '-')}</td>
          <td class="text-left camp-name" style="padding-left:10px;">{row.get('Ad Name', '-')}</td>
          <td class="num">₹{rspends:,.0f}</td>
          <td class="num">{rp:,.0f}</td>
          <td class="num">{rl:,.0f}</td>
          <td class="num {rdup_cls}">{rdup:.1f}%</td>
          <td class="num">{rffh:,.0f}</td>
          <td class="num">{radm:,.0f}</td>
          <td class="num">₹{rinv:,.0f}</td>
          <td class="num">₹{rcpl_p:,.0f}</td>
          <td class="num">₹{rcpl_l:,.0f}</td>
          <td class="num">₹{rcac_f:,.0f}</td>
          <td class="num">₹{rcac_a:,.0f}</td>
        </tr>
        '''
        
    html_accounts += "</tbody>\n"

HTML_TEMPLATE = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0"/>
<title>Degreefyd Deep Drilldown</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; -webkit-tap-highlight-color:transparent; }}
body {{ background: #070b14; color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 13px; line-height: 1.5; padding: 10px; }}
.wrap {{ max-width: 1600px; margin: 0 auto; background: #0f172a; border-radius: 12px; overflow: hidden; border: 1px solid #1e293b; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }}
.hdr {{ background: #020617; padding: 24px 20px; text-align: center; border-bottom: 1px solid #1e293b; }}
.hdr h1 {{ font-size: 22px; font-weight: 800; margin-bottom: 6px; color: #f8fafc; letter-spacing: -0.5px; }}
.hdr p {{ font-size: 13px; color: #94a3b8; }}

input[type="checkbox"] {{ position: absolute; opacity: 0; width: 0; height: 0; pointer-events: none; }}

.table-wrap {{ overflow-x: auto; background: #020617; }}
table {{ width: 100%; border-collapse: collapse; text-align: right; min-width: 1400px; }}
th {{ background: #0f172a; color: #94a3b8; font-size: 11px; text-transform: uppercase; font-weight: 800; padding: 14px 12px; border-bottom: 2px solid #1e293b; white-space: nowrap; position: sticky; top: 0; z-index: 10; }}
td {{ padding: 12px; border-bottom: 1px solid #1e293b; font-size: 12.5px; color: #f8fafc; white-space: nowrap; }}

.num {{ font-family: ui-monospace, SFMono-Regular, Consolas, monospace; color: #e2e8f0; }}
th.num {{ text-align: right; }}
.text-left {{ text-align: left; }}
.text-center {{ text-align: center; }}
.warn {{ color: #f43f5e !important; font-weight: bold; }}

.account-row td {{ background: #1e293b !important; font-weight: 700; border-top: 3px solid #334155; border-bottom: 3px solid #334155; color: #f8fafc; }}
.acc-lbl {{ display: flex; align-items: center; cursor: pointer; font-size: 14px; width: 100%; touch-action: manipulation; user-select: none; }}
.chev {{ display: inline-block; margin-right: 12px; font-size: 12px; color: #94a3b8; transition: transform 0.2s; }}

.plat-g {{ background: rgba(56,189,248,0.15); color: #38bdf8; border: 1px solid rgba(56,189,248,0.3); padding: 4px 8px; border-radius: 6px; font-size: 11px; margin-right: 12px; font-weight: 800; }}
.plat-m {{ background: rgba(167,139,250,0.15); color: #a78bfa; border: 1px solid rgba(167,139,250,0.3); padding: 4px 8px; border-radius: 6px; font-size: 11px; margin-right: 12px; font-weight: 800; }}

.camp-body {{ display: none; }}
.camp-row td {{ background: #0b1120; color: #94a3b8; border-bottom: 1px solid #1e293b; }}
.camp-name {{ color: #cbd5e1; font-size: 12.5px; }}

{css_rules}

</style>
</head>
<body>

{inputs_html}

<div class="wrap">
  <div class="hdr">
    <h1>Degreefyd Deep Drilldown</h1>
    <p>Daily Campaign & Ad Name Breakdown (Last 15 Days)</p>
  </div>
  
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th class="text-center">Date</th>
          <th class="text-center">Type</th>
          <th class="text-left">Campaign</th>
          <th class="text-left">Ad Name / Ad ID</th>
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
      {html_accounts}
    </table>
  </div>
</div>

</body>
</html>
"""

file_path = "/workspace/Degreefyd_Deep_Drilldown.html"
with open(file_path, "w", encoding="utf-8") as f: f.write(HTML_TEMPLATE)

from dotenv import load_dotenv
load_dotenv("/workspace/.env")
WHAPI_TOKEN = os.getenv("WHAPI_TOKEN")
WHATSAPP_GROUP = os.getenv("WHATSAPP_GROUP")

with open(file_path, "rb") as f: b64 = base64.b64encode(f.read()).decode('utf-8')

payload = {
    "to": WHATSAPP_GROUP,
    "media": f"data:text/html;name=Degreefyd_Deep_Drilldown.html;base64,{b64}",
    "caption": "🔥 **Degreefyd Deep Drilldown (Exact Daily Ad Match)**\n\nI understand exactly what you meant now. You didn't want the rolled-up YTD/MTD sheets. You wanted the **Raw Daily Data** perfectly nested inside the Accounts.\n\n✅ **Click the Account Name:** It will instantly expand to show the **Date, Type, Campaign, and Ad Name / Ad ID** exactly like the lines you pasted.\n✅ **Data Source:** Pulling directly from the `Day Wise CAC Report` (Filtered to the latest 15 days to keep it lightning fast on mobile).\n✅ **Platform Intensifiers:** Huge **🔵 Google Ads** and **🟣 Meta Ads** badges next to the account names so you know instantly what you're looking at.\n✅ **Clean UI:** No graphs, just pure data, beautifully formatted and collapsible."
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
