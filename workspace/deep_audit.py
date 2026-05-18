
import pandas as pd
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

def audit(sheet_id, label):
    creds = Credentials.from_authorized_user_file('/home/hermeswebui/.hermes/google_token.json')
    svc = build('sheets', 'v4', credentials=creds)
    r = svc.spreadsheets().values().get(spreadsheetId=sheet_id, range="'FFH & Above'!A1:Z5000").execute()
    rows = r.get('values', [])
    df = pd.DataFrame(rows[1:], columns=[str(c).strip() for c in rows[0]])
    
    # Try multiple date formats
    def parse_date(v):
        for fmt in ('%d/%b/%Y', '%d-%b-%Y', '%Y-%m-%d'):
            try: return pd.to_datetime(v, format=fmt)
            except: continue
        return pd.to_datetime(v, errors='coerce')

    df['Form_D'] = df['Form Date'].apply(parse_date)
    df['Adm_D']  = df['Admission Date'].apply(parse_date)
    
    target = pd.to_datetime('2026-05-04')
    
    print(f"\n--- {label} ---")
    f_today = df[df['Form_D'] == target]
    a_today = df[df['Adm_D'] == target]
    
    print(f"Total Rows: {len(df)}")
    print(f"Forms on May 4: {len(f_today)}")
    print(f"Admissions on May 4: {len(a_today)}")
    
    if len(f_today) > 0:
        print("Sample Forms on May 4:")
        print(f_today[['Student Name', 'Form Date', 'Admission Date', 'Invoicing Variable']].head(5).to_string())
    
    if len(a_today) > 0:
        print("Sample Admissions on May 4:")
        print(a_today[['Student Name', 'Form Date', 'Admission Date', 'Invoicing Variable']].head(5).to_string())

audit("1jzgnRxmmLIe_DAZ7nwHSRXeO6sI4CRxlTatc0T88ukY", "ONLINE")
audit("1QQ_Z50FDAhuBbVX5ioCjfgyFjfhr3y0gMGbQqteQ1f8", "REGULAR")
