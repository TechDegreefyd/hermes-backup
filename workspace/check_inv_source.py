
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

# All rows with Form Date = May 4
may4_form = df[df['Form_Date'].dt.strftime('%Y-%m-%d')=='2026-05-04'].copy()
# All rows with Adm Date = May 4
may4_adm  = df[df['Adm_Date'].dt.strftime('%Y-%m-%d')=='2026-05-04'].copy()

print("=== 8 ROWS WHERE FORM DATE = 04/May (FFH source) ===")
print(f"{'Student':<28} {'Form Date':<12} {'Adm Date':<12} {'Fee Sub':<10} {'Total Var':<12} {'Inv Var':<12} {'Has Adm?'}")
print("-"*100)
for _, r in may4_form.iterrows():
    has_adm = "YES ✅" if str(r.get('Admission Date','')).strip() != '' else "NO ❌"
    print(f"{str(r.get('Student Name','')):<28} {str(r.get('Form Date','')):<12} {str(r.get('Admission Date','')):<12} "
          f"{str(r.get('Fee Submitted','')):<10} {str(r.get('Total Variable','')):<12} "
          f"{str(r.get('Invoicing Variable','')):<12} {has_adm}")

print(f"\nFFH from Form Date=May4: {len(may4_form)}")
print(f"Of those, with Adm Date=May4: {len(may4_form[may4_form['Adm_Date'].dt.strftime('%Y-%m-%d')=='2026-05-04'])}")
print(f"Inv from THAT subset: Rs {may4_form[may4_form['Adm_Date'].dt.strftime('%Y-%m-%d')=='2026-05-04']['Inv'].sum():,.2f}")

print(f"\n=== ALL 12 ROWS WHERE ADM DATE = 04/May (Adm/Inv source) ===")
print(f"{'Student':<28} {'Form Date':<12} {'Adm Date':<12} {'Inv Var':<12} {'Form=Adm?'}")
print("-"*80)
for _, r in may4_adm.iterrows():
    same_day = "SAME DAY" if str(r.get('Form Date','')) == '04/May/2026' else f"DIFF ({r.get('Form Date','')})"
    print(f"{str(r.get('Student Name','')):<28} {str(r.get('Form Date','')):<12} {str(r.get('Admission Date','')):<12} "
          f"{str(r.get('Invoicing Variable','')):<12} {same_day}")

print(f"\nTotal Adm on May4: {len(may4_adm)}")
print(f"Total Inv on May4: Rs {may4_adm['Inv'].sum():,.2f}")
print(f"\nBreakdown:")
print(f"  Adm where Form Date also = May4: {len(may4_adm[may4_adm['Form_Date'].dt.strftime('%Y-%m-%d')=='2026-05-04'])}")
print(f"  Adm where Form Date DIFFERENT:   {len(may4_adm[may4_adm['Form_Date'].dt.strftime('%Y-%m-%d')!='2026-05-04'])}")
