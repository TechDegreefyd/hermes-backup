
import pandas as pd
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

def check_raw_dates(sheet_id, label):
    svc = build('sheets', 'v4', credentials=Credentials.from_authorized_user_file('/home/hermeswebui/.hermes/google_token.json'))
    r = svc.spreadsheets().values().get(spreadsheetId=sheet_id, range="'FFH & Above'!A1:Z5000").execute()
    rows = r['values']
    df = pd.DataFrame(rows[1:], columns=[str(c).strip() for c in rows[0]])
    
    print(f"\n--- {label} RAW DATES ---")
    print("Unique Form Dates (last 20):")
    print(df['Form Date'].tail(20).tolist())
    
    # Check for "04/May/2026"
    matches = df[df['Form Date'].astype(str).str.contains('04/May', na=False)]
    print(f"Rows matching '04/May': {len(matches)}")
    if len(matches) > 0:
        print(matches[['Student Name', 'Form Date']].to_string())

print("ONLINE:")
check_raw_dates("1jzgnRxmmLIe_DAZ7nwHSRXeO6sI4CRxlTatc0T88ukY", "ONLINE")
print("\nREGULAR:")
check_raw_dates("1QQ_Z50FDAhuBbVX5ioCjfgyFjfhr3y0gMGbQqteQ1f8", "REGULAR")
