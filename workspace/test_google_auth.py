import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

try:
    TOKEN_PATH = "/home/hermeswebui/.hermes/google_token.json"
    creds = Credentials.from_authorized_user_file(TOKEN_PATH)
    service = build("sheets", "v4", credentials=creds)
    spreadsheet_id = "1jzgnRxmmLIe_DAZ7nwHSRXeO6sI4CRxlTatc0T88ukY"
    # let's just get the sheet metadata to see if it works
    sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheets = sheet_metadata.get('sheets', '')
    print("Success! Available sheets:")
    for s in sheets:
        print(s.get("properties", {}).get("title", ""))
except Exception as e:
    print("Error:", str(e))
