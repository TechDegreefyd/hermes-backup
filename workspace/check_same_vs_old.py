
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import pandas as pd

SHEET_ID = '1jzgnRxmmLIe_DAZ7nwHSRXeO6sI4CRxlTatc0T88ukY'
creds = Credentials.from_authorized_user_file('/home/hermeswebui/.hermes/google_token.json')
svc = build('sheets','v4',credentials=creds)

r = svc.spreadsheets().values().get(spreadsheetId=SHEET_ID, range="'FFH & Above'!A1:Z2000").execute()
rows = r.get('values',[])
df = pd.DataFrame(rows[1:], columns=rows[0])
df['Adm_Date']  = pd.to_datetime(df['Admission Date'], format='%d/%b/%Y', errors='coerce')
df['Form_Date'] = pd.to_datetime(df['Form Date'],       format='%d/%b/%Y', errors='coerce')
df['Inv'] = pd.to_numeric(df['Invoicing Variable'].astype(str).str.replace(',','').str.strip(), errors='coerce').fillna(0)
df['Camp_Name'] = df['Campaign Name'].astype(str).str.strip()

# All rows with Adm Date = May 4
may4_adm = df[df['Adm_Date'].dt.strftime('%Y-%m-%d')=='2026-05-04'].copy()

print("=== May4 Adm rows — same-day vs old-pipeline ===")
same = may4_adm[may4_adm['Form_Date'].notna() & (may4_adm['Form_Date'] == may4_adm['Adm_Date'])]
old  = may4_adm[may4_adm['Form_Date'].isna()  | (may4_adm['Form_Date'] != may4_adm['Adm_Date'])]

print(f"\nSame-day (Form=Adm=May4): {len(same)}")
for _, r in same.iterrows():
    print(f"  {r['Student Name']:<28} Inv=₹{r['Inv']:,.0f}")
print(f"  Subtotal Inv: ₹{same['Inv'].sum():,.2f}")

print(f"\nOld-pipeline (Form != May4, Adm=May4): {len(old)}")
for _, r in old.iterrows():
    print(f"  {r['Student Name']:<28} Form={r.get('Form Date','?'):<12} Inv=₹{r['Inv']:,.0f}")
print(f"  Subtotal Inv: ₹{old['Inv'].sum():,.2f}")

print(f"\n=== CORRECT FTD SHOULD BE ===")
print(f"  FFH: 8  (all Form Date=May4)")
print(f"  Adm: {len(same)}  (only same-day: Form=Adm=May4)")
print(f"  Inv: ₹{same['Inv'].sum():,.2f}")
print(f"\n=== CORRECT MTD SHOULD BE ===")
mtd_adm = df[df['Adm_Date'] >= '2026-05-01']
print(f"  Adm: {len(mtd_adm)}")
print(f"  Inv: ₹{mtd_adm['Inv'].sum():,.2f}")
