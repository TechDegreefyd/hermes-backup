
import pandas as pd
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

SHEET_ID = '1jzgnRxmmLIe_DAZ7nwHSRXeO6sI4CRxlTatc0T88ukY'
creds = Credentials.from_authorized_user_file('/home/hermeswebui/.hermes/google_token.json')
svc = build('sheets','v4',credentials=creds)

r = svc.spreadsheets().values().get(spreadsheetId=SHEET_ID, range="'FFH & Above'!A1:Z2000").execute()
rows = r.get('values',[])
df = pd.DataFrame(rows[1:], columns=rows[0])
df['Adm_Date']  = pd.to_datetime(df['Admission Date'], format='%d/%b/%Y', errors='coerce')
df['Form_Date'] = pd.to_datetime(df['Form Date'],       format='%d/%b/%Y', errors='coerce')
df['Inv'] = pd.to_numeric(df['Invoicing Variable'].astype(str).str.replace(',','').str.strip(), errors='coerce').fillna(0)

may4_adm  = df[df['Adm_Date'].dt.strftime('%Y-%m-%d')=='2026-05-04']
may4_form = df[df['Form_Date'].dt.strftime('%Y-%m-%d')=='2026-05-04']
mtd_adm   = df[df['Adm_Date']  >= '2026-05-01']
mtd_form  = df[df['Form_Date'] >= '2026-05-01']

print("=== RAW SHEET vs REPORT VERIFICATION ===")
print(f"FTD FFH  (Form Date=May4):   {len(may4_form)}   → report shows: 8")
print(f"FTD Adm  (Adm  Date=May4):   {len(may4_adm)}   → report shows: 12")
print(f"FTD Inv  (Adm  Date=May4):   Rs {may4_adm['Inv'].sum():,.2f}  → report shows: Rs 352,801")
print(f"  Values: {may4_adm['Inv'].tolist()}")
print()
print(f"MTD FFH  (Form Date>=May1):  {len(mtd_form)}   → report shows: 20")
print(f"MTD Adm  (Adm  Date>=May1):  {len(mtd_adm)}   → report shows: 17")
print(f"MTD Inv  (Adm  Date>=May1):  Rs {mtd_adm['Inv'].sum():,.2f}  → report shows: Rs 480,825")
