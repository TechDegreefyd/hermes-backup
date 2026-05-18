
import pandas as pd
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

SHEET_ID_REGULAR = '1QQ_Z50FDAhuBbVX5ioCjfgyFjfhr3y0gMGbQqteQ1f8'
creds = Credentials.from_authorized_user_file('/home/hermeswebui/.hermes/google_token.json')
svc = build('sheets', 'v4', credentials=creds)

print("Fetching Regular Sheet FFH & Above...")
r = svc.spreadsheets().values().get(spreadsheetId=SHEET_ID_REGULAR, range="'FFH & Above'!A1:Z5000").execute()
rows = r.get('values',[])
df = pd.DataFrame(rows[1:], columns=[str(c).strip() for c in rows[0]])

# Parse dates and numeric values
df['Adm_Date']  = pd.to_datetime(df['Admission Date'], format='%d/%b/%Y', errors='coerce')
df['Form_Date'] = pd.to_datetime(df['Form Date'],       format='%d/%b/%Y', errors='coerce')
df['Inv'] = pd.to_numeric(df['Invoicing Variable'].astype(str).str.replace(',','').str.strip(), errors='coerce').fillna(0)

# Anchor today
may4 = pd.to_datetime('2026-05-04')

print("\n=== RAW DATA FOR 04/May/2026 (Regular Sheet) ===")

may4_forms = df[df['Form_Date'] == may4]
print(f"\n1. FORMS FILLED ON 04/May (Total: {len(may4_forms)})")
for _, r in may4_forms.iterrows():
    print(f"   {str(r.get('Student Name', '')):<25} | Form: {str(r.get('Form Date','')):<11} | Adm: {str(r.get('Admission Date','')):<11} | Inv: {r['Inv']}")

may4_adms = df[df['Adm_Date'] == may4]
print(f"\n2. ADMISSIONS ON 04/May (Total: {len(may4_adms)})")
for _, r in may4_adms.iterrows():
    print(f"   {str(r.get('Student Name', '')):<25} | Form: {str(r.get('Form Date','')):<11} | Adm: {str(r.get('Admission Date','')):<11} | Inv: {r['Inv']}")

print("\n=== MTD SUMMARY (May 1 - May 4) ===")
mtd_forms = df[df['Form_Date'] >= '2026-05-01']
mtd_adms  = df[df['Adm_Date'] >= '2026-05-01']
print(f"  MTD Forms:      {len(mtd_forms)}")
print(f"  MTD Admissions: {len(mtd_adms)}")
print(f"  MTD Inv Var:    ₹{mtd_adms['Inv'].sum():,.2f}")

