import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def check_last_rows(spreadsheet_id, sheet_name):
    creds_path = "/home/hermeswebui/.hermes/google_token.json"
    with open(creds_path, 'r') as f:
        info = json.load(f)
    creds = Credentials.from_authorized_user_info(info)
    service = build('sheets', 'v4', credentials=creds)
    
    # Get the last 10 rows
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, 
        range=f"'{sheet_name}'!A:I"
    ).execute()
    values = result.get('values', [])
    
    print(f"\n--- Last 5 rows of {spreadsheet_id} ({sheet_name}) ---")
    if not values:
        print("Sheet is empty.")
    else:
        for row in values[-5:]:
            print(row)

check_last_rows("1jzgnRxmmLIe_DAZ7nwHSRXeO6sI4CRxlTatc0T88ukY", "Day Wise CAC Report")
check_last_rows("1QQ_Z50FDAhuBbVX5ioCjfgyFjfhr3y0gMGbQqteQ1f8", "Day Wise CAC Report")
