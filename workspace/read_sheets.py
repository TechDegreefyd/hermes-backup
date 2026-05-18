from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import json
import csv

ONLINE_SHEET_ID = "1jzgnRxmmLIe_DAZ7nwHSRXeO6sI4CRxlTatc0T88ukY"
REGULAR_SHEET_ID = "1QQ_Z50FDAhuBbVX5ioCjfgyFjfhr3y0gMGbQqteQ1f8"
TOKEN_PATH = '/home/hermeswebui/.hermes/google_token.json'

def get_sheet_data(sheet_id, sheet_name):
    try:
        creds = Credentials.from_authorized_user_file(TOKEN_PATH)
        service = build('sheets', 'v4', credentials=creds)
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id, range=f"'{sheet_name}'!A1:Z5000"
        ).execute()
        return result.get('values', [])
    except Exception as e:
        print(f"Error reading {sheet_id} ({sheet_name}): {e}")
        return []

# Fetch key sheets
online_cac = get_sheet_data(ONLINE_SHEET_ID, "Day Wise CAC Report")
regular_cac = get_sheet_data(REGULAR_SHEET_ID, "Day Wise CAC Report")

def save_to_csv(data, filename):
    if not data: return
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(data)

save_to_csv(online_cac, 'online_cac_sheet.csv')
save_to_csv(regular_cac, 'regular_cac_sheet.csv')
print(f"Saved {len(online_cac)} rows from Online and {len(regular_cac)} rows from Regular.")
