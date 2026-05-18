
import pandas as pd
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

def audit_dates(sheet_id, label):
    creds = Credentials.from_authorized_user_file('/home/hermeswebui/.hermes/google_token.json')
    svc = build('sheets', 'v4', credentials=creds)
    r = svc.spreadsheets().values().get(spreadsheetId=sheet_id, range="'FFH & Above'!A1:Z5000").execute()
    rows = r.get('values', [])
    df = pd.DataFrame(rows[1:], columns=[str(c).strip() for c in rows[0]])
    
    def parse_date(v):
        for fmt in ('%d/%b/%Y', '%d-%b-%Y', '%Y-%m-%d'):
            try: return pd.to_datetime(v, format=fmt)
            except: continue
        return pd.to_datetime(v, errors='coerce')

    df['Lead_D'] = df['Lead Date'].apply(parse_date)
    df['Form_D'] = df['Form Date'].apply(parse_date)
    df['Adm_D']  = df['Admission Date'].apply(parse_date)
    
    target = pd.to_datetime('2026-05-04')
    
    print(f"\n--- {label} Date Check ---")
    l_today = df[df['Lead_D'] == target]
    f_today = df[df['Form_D'] == target]
    a_today = df[df['Adm_D'] == target]
    
    print(f"Leads on May 4: {len(l_today)}")
    print(f"Forms on May 4: {len(f_today)}")
    print(f"Admissions on May 4: {len(a_today)}")
    
    if len(l_today) > 0:
        print("Sample Leads on May 4:")
        print(l_today[['Student Name', 'Lead Date', 'Form Date', 'Admission Date']].head(5).to_string())

audit_dates("1QQ_Z50FDAhuBbVX5ioCjfgyFjfhr3y0gMGbQqteQ1f8", "REGULAR")
