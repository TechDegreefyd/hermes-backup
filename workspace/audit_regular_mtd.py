
import pandas as pd
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

SHEET_ID_REGULAR = '1QQ_Z50FDAhuBbVX5ioCjfgyFjfhr3y0gMGbQqteQ1f8'
creds = Credentials.from_authorized_user_file('/home/hermeswebui/.hermes/google_token.json')
svc = build('sheets', 'v4', credentials=creds)

print("Fetching Regular Sheet 'FFH & Above'...")
r = svc.spreadsheets().values().get(spreadsheetId=SHEET_ID_REGULAR, range="'FFH & Above'!A1:Z5000").execute()
rows = r.get('values',[])
df = pd.DataFrame(rows[1:], columns=[str(c).strip() for c in rows[0]])
df.columns = [c.strip() for c in df.columns]

# Parse dates and numeric values
def parse_date(v):
    for fmt in ('%d/%b/%Y', '%d-%b-%Y', '%Y-%m-%d'):
        try: return pd.to_datetime(v, format=fmt)
        except: continue
    return pd.to_datetime(v, errors='coerce')

df['Adm_D']  = df['Admission Date'].apply(parse_date)
df['Form_D'] = df['Form Date'].apply(parse_date)
df['Inv'] = pd.to_numeric(df['Invoicing Variable'].astype(str).str.replace(',','').str.strip(), errors='coerce').fillna(0)

# Filter for May 2026 Admissions
may_start = pd.to_datetime('2026-05-01')
may_adms = df[df['Adm_D'] >= may_start].sort_values('Adm_D')

print(f"\n=== REGULAR ADMISSIONS IN MAY (Total: {len(may_adms)}) ===")
print(f"{'Student Name':<25} | {'Adm Date':<11} | {'Form Date':<11} | {'Inv Var':<10} | {'Campaign ID'}")
print("-" * 80)
for _, r in may_adms.iterrows():
    print(f"{str(r.get('Student Name', '')):<25} | {str(r.get('Admission Date','')):<11} | {str(r.get('Form Date','')):<11} | {r['Inv']:<10} | {r.get('Campaign ID','')}")

print(f"\nMTD Total Admissions: {len(may_adms)}")
print(f"MTD Total Inv Var:    ₹{may_adms['Inv'].sum():,.2f}")

# Check for Forms in May
may_forms = df[df['Form_D'] >= may_start]
print(f"\nMTD Total Forms:      {len(may_forms)}")
