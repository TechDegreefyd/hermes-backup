
"""
Full FTD audit: what the report computes vs what it should show.
FTD = today (latest date in CAC sheet = 2026-05-04)
"""
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import pandas as pd
from datetime import datetime

SHEET_ID = "1jzgnRxmmLIe_DAZ7nwHSRXeO6sI4CRxlTatc0T88ukY"
creds = Credentials.from_authorized_user_file('/home/hermeswebui/.hermes/google_token.json')
service = build('sheets', 'v4', credentials=creds)

# ─── Load CAC sheet ───
r = service.spreadsheets().values().get(
    spreadsheetId=SHEET_ID, range='Day Wise CAC Report!A1:S10000'
).execute()
rows = r.get('values', [])
headers = rows[1]
data_rows = [row for row in rows[2:] if len(row) > 3 and row[0].strip() != '']
df = pd.DataFrame(data_rows, columns=headers[:len(data_rows[0])] if data_rows else headers)
for c in ['Spends','Pannel_Lead','Lead_LMS','FFH','Adm','Invoicing_Var']:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
df['Date_Parsed'] = pd.to_datetime(df['Date'], errors='coerce')
df = df.dropna(subset=['Date_Parsed'])
# Anchor today strictly from CAC sheet before any CRM data
df = df[df['Date_Parsed'] <= datetime.now()]
today = df['Date_Parsed'].max()

print(f"FTD date anchor: {today.date()}")

# ─── FTD from CAC sheet (what report currently shows) ───
df_ftd = df[df['Date_Parsed'].dt.date == today.date()]
print(f"\n=== FTD from CAC Sheet ONLY (what report shows NOW) ===")
print(f"  Spends:       ₹{df_ftd['Spends'].sum():,.2f}")
print(f"  Panel Leads:  {int(df_ftd['Pannel_Lead'].sum())}")
print(f"  LMS Leads:    {int(df_ftd['Lead_LMS'].sum())}")
print(f"  FFH:          {int(df_ftd['FFH'].sum())}  ← from CAC sheet (wrong)")
print(f"  Adm:          {int(df_ftd['Adm'].sum())}  ← from CAC sheet (wrong)")
print(f"  Inv_Var:      ₹{df_ftd['Invoicing_Var'].sum():,.2f}  ← from CAC sheet (wrong)")

# Derived
sp = df_ftd['Spends'].sum()
pl = df_ftd['Pannel_Lead'].sum()
ll = df_ftd['Lead_LMS'].sum()
ff_cac = df_ftd['FFH'].sum()
ad_cac = df_ftd['Adm'].sum()
iv_cac = df_ftd['Invoicing_Var'].sum()
print(f"  CPL Panel:    ₹{sp/pl if pl else 0:,.2f}")
print(f"  CPL LMS:      ₹{sp/ll if ll else 0:,.2f}")
print(f"  CAC FFH:      ₹{sp/ff_cac if ff_cac else 0:,.2f}  (div by {ff_cac:.0f})")
print(f"  CAC Adm:      ₹{sp/ad_cac if ad_cac else 0:,.2f}  (div by {ad_cac:.0f})")
print(f"  ARPU:         ₹{iv_cac/ad_cac if ad_cac else 0:,.2f}")

# ─── Load FFH & Above ───
r2 = service.spreadsheets().values().get(
    spreadsheetId=SHEET_ID, range='FFH & Above!A1:Z2000'
).execute()
rows2 = r2.get('values', [])
df_ffh = pd.DataFrame(rows2[1:], columns=rows2[0])
df_ffh['Form_Date_Parsed'] = pd.to_datetime(df_ffh['Form Date'], format='%d/%b/%Y', errors='coerce')
df_ffh['Adm_Date_Parsed']  = pd.to_datetime(df_ffh['Admission Date'], format='%d/%b/%Y', errors='coerce')
df_ffh['Inv_Var_Num'] = pd.to_numeric(
    df_ffh['Invoicing Variable'].astype(str).str.replace(',','').str.strip(), errors='coerce'
).fillna(0)

# FTD FFH (Form Date = today)
ftd_ffh_rows = df_ffh[df_ffh['Form_Date_Parsed'].dt.date == today.date()]
# FTD Adm (Admission Date = today, non-empty)
ftd_adm_rows = df_ffh[
    (df_ffh['Adm_Date_Parsed'].dt.date == today.date()) &
    (df_ffh['Admission Date'].str.strip() != '')
]
ffh_ftd = len(ftd_ffh_rows)
adm_ftd = len(ftd_adm_rows)
inv_ftd = ftd_adm_rows['Inv_Var_Num'].sum()

print(f"\n=== FTD from FFH & Above (correct source) ===")
print(f"  FFH (Form Date={today.date()}):      {ffh_ftd}")
print(f"  Adm (Adm Date={today.date()}):       {adm_ftd}")
print(f"  Inv_Var (Adm Date={today.date()}):   ₹{inv_ftd:,.2f}")

# Correct derived FTD
cac_ffh_c  = sp / ffh_ftd if ffh_ftd else 0
cac_adm_c  = sp / adm_ftd if adm_ftd else 0
arpu_c     = inv_ftd / adm_ftd if adm_ftd else 0
cac_arpu_c = cac_adm_c / arpu_c if arpu_c else 0
l2f_c      = ffh_ftd / ll if ll else 0
l2a_c      = adm_ftd / ll if ll else 0
f2a_c      = adm_ftd / ffh_ftd if ffh_ftd else 0

print(f"\n=== Correct FTD Derived Metrics ===")
print(f"  Spends:       ₹{sp:,.2f}")
print(f"  Panel Leads:  {int(pl)}")
print(f"  LMS Leads:    {int(ll)}")
print(f"  FFH:          {ffh_ftd}")
print(f"  Adm:          {adm_ftd}")
print(f"  Inv_Var:      ₹{inv_ftd:,.2f}")
print(f"  CPL Panel:    ₹{sp/pl if pl else 0:,.2f}")
print(f"  CPL LMS:      ₹{sp/ll if ll else 0:,.2f}")
print(f"  CAC FFH:      ₹{cac_ffh_c:,.2f}")
print(f"  CAC Adm:      ₹{cac_adm_c:,.2f}")
print(f"  ARPU:         ₹{arpu_c:,.2f}")
print(f"  CAC/ARPU:     {cac_arpu_c:.3f}")
print(f"  L2F:          {l2f_c*100:.1f}%")
print(f"  L2A:          {l2a_c*100:.1f}%")
print(f"  F2A:          {f2a_c*100:.1f}%")

# ─── Side-by-side diff ───
print(f"\n{'='*55}")
print(f"{'Metric':<20} {'Report Shows':>15} {'Should Be':>15} {'Status':>6}")
print(f"{'='*55}")
rows_check = [
    ("Spends",      f"₹{sp:,.0f}",        f"₹{sp:,.0f}",        "✅"),
    ("Panel Leads", str(int(pl)),          str(int(pl)),          "✅"),
    ("LMS Leads",   str(int(ll)),          str(int(ll)),          "✅"),
    ("FFH",         str(int(ff_cac)),      str(ffh_ftd),         "❌" if int(ff_cac) != ffh_ftd else "✅"),
    ("Adm",         str(int(ad_cac)),      str(adm_ftd),         "❌" if int(ad_cac) != adm_ftd else "✅"),
    ("Inv_Var",     f"₹{iv_cac:,.0f}",    f"₹{inv_ftd:,.0f}",  "❌" if abs(iv_cac-inv_ftd) > 1 else "✅"),
    ("CAC FFH",     f"₹{sp/ff_cac if ff_cac else 0:,.0f}", f"₹{cac_ffh_c:,.0f}", "❌" if abs((sp/ff_cac if ff_cac else 0)-cac_ffh_c) > 1 else "✅"),
    ("CAC Adm",     f"₹{sp/ad_cac if ad_cac else 0:,.0f}", f"₹{cac_adm_c:,.0f}", "❌" if abs((sp/ad_cac if ad_cac else 0)-cac_adm_c) > 1 else "✅"),
    ("ARPU",        f"₹{iv_cac/ad_cac if ad_cac else 0:,.0f}", f"₹{arpu_c:,.0f}", "❌" if abs((iv_cac/ad_cac if ad_cac else 0)-arpu_c) > 1 else "✅"),
    ("CAC/ARPU",    f"{(sp/ad_cac if ad_cac else 0)/(iv_cac/ad_cac if ad_cac else 1):.3f}", f"{cac_arpu_c:.3f}", "?"),
    ("L2F",         f"{ff_cac/ll*100 if ll else 0:.1f}%", f"{l2f_c*100:.1f}%", "❌" if abs(ff_cac/ll*100 if ll else 0 - l2f_c*100) > 0.1 else "✅"),
    ("L2A",         f"{ad_cac/ll*100 if ll else 0:.1f}%", f"{l2a_c*100:.1f}%", "❌" if abs(ad_cac/ll*100 if ll else 0 - l2a_c*100) > 0.1 else "✅"),
    ("F2A",         f"{ad_cac/ff_cac*100 if ff_cac else 0:.1f}%", f"{f2a_c*100:.1f}%", "❌" if abs(ad_cac/ff_cac*100 if ff_cac else 0 - f2a_c*100) > 0.1 else "✅"),
]
for metric, current, correct, status in rows_check:
    print(f"{metric:<20} {current:>15} {correct:>15} {status:>6}")

# ─── Show actual FFH entries for today ───
print(f"\n=== FFH entries with Form Date = {today.date()} ===")
for _, row in ftd_ffh_rows.iterrows():
    print(f"  {row.get('Student Name','')} | Camp: {row.get('Campaign Name','')} | Form: {row.get('Form Date','')}")

print(f"\n=== Admission entries with Adm Date = {today.date()} ===")
for _, row in ftd_adm_rows.iterrows():
    print(f"  {row.get('Student Name','')} | Camp: {row.get('Campaign Name','')} | Adm: {row.get('Admission Date','')} | Inv: ₹{row['Inv_Var_Num']:,.0f}")
