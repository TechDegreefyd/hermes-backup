
import pandas as pd
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

def improved_audit(sheet_id, label):
    creds = Credentials.from_authorized_user_file('/home/hermeswebui/.hermes/google_token.json')
    svc = build('sheets', 'v4', credentials=creds)
    
    r_cac = svc.spreadsheets().values().get(spreadsheetId=sheet_id, range="'Day Wise CAC Report'!A1:S20000").execute()
    df_cac = pd.DataFrame(r_cac['values'][2:], columns=[str(c).strip() for c in r_cac['values'][1]])
    
    r_ffh = svc.spreadsheets().values().get(spreadsheetId=sheet_id, range="'FFH & Above'!A1:Z5000").execute()
    df_ffh = pd.DataFrame(r_ffh['values'][1:], columns=[str(c).strip() for c in r_ffh['values'][0]])
    df_ffh.columns = [c.strip() for c in df_ffh.columns]
    
    cac_camps = set(df_cac['Campaign'].astype(str).str.strip()) | set(df_cac['Ad Name'].astype(str).str.strip())
    
    def get_plat(row):
        cid = str(row.get('Campaign ID', '')).strip()
        cname = str(row.get('Campaign Name', '')).strip()
        src = str(row.get('Source Name', '')).strip().lower()
        
        if cid in cac_camps or cname in cac_camps:
            return "Mapped"
        if "google" in src:
            return "Google (from Source)"
        if "meta" in src or "facebook" in src:
            return "Meta (from Source)"
        return "Unknown"

    print(f"\n--- {label} Platform Attribution ---")
    print(df_ffh.apply(get_plat, axis=1).value_counts())

improved_audit("1jzgnRxmmLIe_DAZ7nwHSRXeO6sI4CRxlTatc0T88ukY", "ONLINE")
improved_audit("1QQ_Z50FDAhuBbVX5ioCjfgyFjfhr3y0gMGbQqteQ1f8", "REGULAR")
