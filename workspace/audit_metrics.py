
"""
Audit script: compare what's in the raw sheets vs what the latest report should have.
Check current data state and all key metrics.
"""
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import pandas as pd
from datetime import datetime, timedelta
import json

SHEET_ID = "1jzgnRxmmLIe_DAZ7nwHSRXeO6sI4CRxlTatc0T88ukY"

creds = Credentials.from_authorized_user_file('/home/hermeswebui/.hermes/google_token.json')
service = build('sheets', 'v4', credentials=creds)

# ─── 1. Load Day Wise CAC Report ───
print("Fetching Day Wise CAC Report...")
r = service.spreadsheets().values().get(
    spreadsheetId=SHEET_ID,
    range='Day Wise CAC Report!A1:S10000'
).execute()
rows = r.get('values', [])
headers = rows[1]  # row index 1 is actual header (row 0 is source labels)
data_rows = [r for r in rows[2:] if len(r) > 3 and r[0].strip() != '']
df = pd.DataFrame(data_rows, columns=headers[:len(data_rows[0])] if data_rows else headers)
print(f"Day Wise CAC Report: {len(df)} data rows")
print(f"Columns: {list(df.columns)}")

# Parse dates
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
df = df.dropna(subset=['Date'])
df = df[df['Date'] <= datetime.now()]

# Numeric cols
num_cols = ['Spends', 'Pannel_Lead', 'Lead_LMS', 'FFH', 'Adm', 'Invoicing_Var']
for c in num_cols:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

today = df['Date'].max()
print(f"\nLatest date in CAC sheet: {today.date()}")
mtd_start = today.replace(day=1)
print(f"MTD range: {mtd_start.date()} → {today.date()}")

# ─── 2. MTD from CAC Sheet ───
df_mtd = df[df['Date'] >= mtd_start]
print("\n=== MTD from Day Wise CAC Report ===")
print(f"  Spends:       ₹{df_mtd['Spends'].sum():,.2f}")
print(f"  Pannel Leads: {df_mtd['Pannel_Lead'].sum():,.0f}")
print(f"  LMS Leads:    {df_mtd['Lead_LMS'].sum():,.0f}")
print(f"  FFH (CAC):    {df_mtd['FFH'].sum():,.0f}")
print(f"  Adm (CAC):    {df_mtd['Adm'].sum():,.0f}")
print(f"  Inv_Var (CAC):₹{df_mtd['Invoicing_Var'].sum():,.2f}")

# ─── 3. Load FFH & Above ───
print("\nFetching FFH & Above sheet...")
r2 = service.spreadsheets().values().get(
    spreadsheetId=SHEET_ID,
    range='FFH & Above!A1:Z2000'
).execute()
rows2 = r2.get('values', [])
ffh_headers = rows2[0]
ffh_data = rows2[1:]
df_ffh = pd.DataFrame(ffh_data, columns=ffh_headers[:len(ffh_data[0])] if ffh_data else ffh_headers)
# Pad missing cols
for col in ffh_headers:
    if col not in df_ffh.columns:
        df_ffh[col] = ''
        
print(f"FFH & Above: {len(df_ffh)} rows")
print(f"Columns: {list(df_ffh.columns)}")

# Parse key dates
df_ffh['Form_Date_Parsed'] = pd.to_datetime(df_ffh['Form Date'], format='%d/%b/%Y', errors='coerce')
df_ffh['Adm_Date_Parsed'] = pd.to_datetime(df_ffh['Admission Date'], format='%d/%b/%Y', errors='coerce')

# MTD FFH (by Form Date)
df_ffh_mtd_form = df_ffh[df_ffh['Form_Date_Parsed'] >= mtd_start]
df_ffh_mtd_adm  = df_ffh[df_ffh['Adm_Date_Parsed'] >= mtd_start]

# FFH count
ffh_count = len(df_ffh_mtd_form)
adm_count = len(df_ffh_mtd_adm[df_ffh_mtd_adm['Admission Date'].str.strip() != ''])

# Invoicing
df_ffh['Inv_Var_Num'] = pd.to_numeric(df_ffh['Invoicing Variable'].astype(str).str.replace(',','').str.strip(), errors='coerce').fillna(0)
df_ffh_mtd_adm = df_ffh_mtd_adm.copy()
df_ffh_mtd_adm['Inv_Var_Num'] = df_ffh.loc[df_ffh_mtd_adm.index, 'Inv_Var_Num']
inv_mtd = df_ffh_mtd_adm['Inv_Var_Num'].sum()

print(f"\n=== MTD from FFH & Above (Activity-Based Attribution) ===")
print(f"  FFH (by Form Date):         {ffh_count}")
print(f"  Admissions (by Adm Date):   {adm_count}")
print(f"  Invoicing Var (by Adm Date):₹{inv_mtd:,.2f}")

# FTD
df_ffh_ftd_form = df_ffh[df_ffh['Form_Date_Parsed'].dt.date == today.date()]
df_ffh_ftd_adm  = df_ffh[(df_ffh['Adm_Date_Parsed'].dt.date == today.date()) & (df_ffh['Admission Date'].str.strip() != '')]
df_ffh_ftd_adm = df_ffh_ftd_adm.copy()
df_ffh_ftd_adm['Inv_Var_Num'] = df_ffh.loc[df_ffh_ftd_adm.index, 'Inv_Var_Num']
df_cac_ftd = df[df['Date'].dt.date == today.date()]

print(f"\n=== FTD ({today.date()}) ===")
print(f"  CAC - Spends:     ₹{df_cac_ftd['Spends'].sum():,.2f}")
print(f"  CAC - Pannel Lead:{df_cac_ftd['Pannel_Lead'].sum():,.0f}")
print(f"  CAC - LMS Lead:   {df_cac_ftd['Lead_LMS'].sum():,.0f}")
print(f"  FFH - FFH count:  {len(df_ffh_ftd_form)}")
print(f"  FFH - Adm count:  {len(df_ffh_ftd_adm)}")
print(f"  FFH - Inv Var:    ₹{df_ffh_ftd_adm['Inv_Var_Num'].sum():,.2f}")

# ─── 4. Derived Metrics ───
spends_mtd = df_mtd['Spends'].sum()
leads_lms_mtd = df_mtd['Lead_LMS'].sum()
leads_panel_mtd = df_mtd['Pannel_Lead'].sum()

cpl_panel = spends_mtd / leads_panel_mtd if leads_panel_mtd > 0 else 0
cpl_lms   = spends_mtd / leads_lms_mtd   if leads_lms_mtd > 0 else 0
cac_ffh   = spends_mtd / ffh_count if ffh_count > 0 else 0
cac_adm   = spends_mtd / adm_count if adm_count > 0 else 0
arpu      = inv_mtd / adm_count if adm_count > 0 else 0
cac_arpu  = cac_adm / arpu if arpu > 0 else 0
l2f       = ffh_count / leads_lms_mtd if leads_lms_mtd > 0 else 0
l2a       = adm_count / leads_lms_mtd if leads_lms_mtd > 0 else 0
f2a       = adm_count / ffh_count if ffh_count > 0 else 0

print(f"\n=== Derived Metrics MTD (what report SHOULD show) ===")
print(f"  Spends:     ₹{spends_mtd:,.2f}")
print(f"  Panel Leads:{leads_panel_mtd:.0f}")
print(f"  LMS Leads:  {leads_lms_mtd:.0f}")
print(f"  FFH:        {ffh_count}")
print(f"  Adm:        {adm_count}")
print(f"  Inv_Var:    ₹{inv_mtd:,.2f}")
print(f"  CPL Panel:  ₹{cpl_panel:,.2f}")
print(f"  CPL LMS:    ₹{cpl_lms:,.2f}")
print(f"  CAC FFH:    ₹{cac_ffh:,.2f}")
print(f"  CAC Adm:    ₹{cac_adm:,.2f}")
print(f"  ARPU:       ₹{arpu:,.2f}")
print(f"  CAC/ARPU:   {cac_arpu:.3f}")
print(f"  L2F:        {l2f*100:.1f}%")
print(f"  L2A:        {l2a*100:.1f}%")
print(f"  F2A:        {f2a*100:.1f}%")

# ─── 5. Platform breakdown MTD ───
print(f"\n=== Platform Breakdown MTD (Spends + Leads) ===")
platform_groups = df_mtd.groupby('Platform').agg(
    Spends=('Spends','sum'),
    Panel_Leads=('Pannel_Lead','sum'),
    LMS_Leads=('Lead_LMS','sum')
).reset_index()
print(platform_groups.to_string(index=False))

# ─── 6. Campaign Wise summary ───
print(f"\n=== Top 10 Campaigns by Spend MTD ===")
camp_groups = df_mtd.groupby('Campaign').agg(
    Spends=('Spends','sum'),
    Panel_Leads=('Pannel_Lead','sum'),
    LMS_Leads=('Lead_LMS','sum')
).sort_values('Spends', ascending=False).head(10)
print(camp_groups.to_string())
