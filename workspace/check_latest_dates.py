
import pandas as pd
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

def check_latest(sheet_id):
    svc = build('sheets', 'v4', credentials=Credentials.from_authorized_user_file('/home/hermeswebui/.hermes/google_token.json'))
    r = svc.spreadsheets().values().get(spreadsheetId=sheet_id, range="'FFH & Above'!A1:Z2000").execute()
    df = pd.DataFrame(r['values'][1:], columns=[str(c).strip() for c in r['values'][0]])
    df.columns = [c.strip() for c in df.columns]
    
    def parse_date(v):
        for fmt in ('%d/%b/%Y', '%d-%b-%Y', '%Y-%m-%d'):
            try: return pd.to_datetime(v, format=fmt)
            except: continue
        return pd.to_datetime(v, errors='coerce')

    df['Form_D'] = df['Form Date'].apply(parse_date)
    df['Adm_D']  = df['Admission Date'].apply(parse_date)
    
    print(f"Max Form Date: {df['Form_D'].max()}")
    print(f"Max Adm Date:  {df['Adm_D'].max()}")

print("ONLINE:")
check_latest("1jzgnRxmmLIe_DAZ7nwHSRXeO6sI4CRxlTatc0T88ukY")
print("\nREGULAR:")
check_latest("1QQ_Z50FDAhuBbVX5ioCjfgyFjfhr3y0gMGbQqteQ1f8")
