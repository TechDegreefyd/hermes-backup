
import pandas as pd
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

svc = build('sheets', 'v4', credentials=Credentials.from_authorized_user_file('/home/hermeswebui/.hermes/google_token.json'))
r = svc.spreadsheets().values().get(spreadsheetId='1jzgnRxmmLIe_DAZ7nwHSRXeO6sI4CRxlTatc0T88ukY', range="'FFH & Above'!A1:Z1000").execute()
df = pd.DataFrame(r['values'][1:], columns=[str(c).strip() for c in r['values'][0]])
df.columns = [c.strip() for c in df.columns]

def parse_date(v):
    for fmt in ('%d/%b/%Y', '%d-%b-%Y', '%Y-%m-%d'):
        try: return pd.to_datetime(v, format=fmt)
        except: continue
    return pd.to_datetime(v, errors='coerce')

df['Adm_D'] = df['Admission Date'].apply(parse_date)
may_adms = df[df['Adm_D'] >= '2026-05-01']
print(f"Online May Admissions count: {len(may_adms)}")
print(may_adms[['Student Name', 'Form Date', 'Admission Date', 'Invoicing Variable']].to_string())
print(f"Total Inv in May: {pd.to_numeric(may_adms['Invoicing Variable'].astype(str).str.replace(',',''), errors='coerce').sum()}")
