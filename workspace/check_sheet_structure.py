import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN_PATH = '/home/hermeswebui/.hermes/google_token.json'
creds = Credentials.from_authorized_user_file(TOKEN_PATH)
service = build('sheets', 'v4', credentials=creds)

SPREADSHEET_ID = '1HcqI8yYnM_ANdWMgD21fYRMNNfUAgM4kpaygm_8Ha0U'
GID = '1234636367'

sheet_metadata = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
sheet_name = None
for sheet in sheet_metadata['sheets']:
    if str(sheet['properties']['sheetId']) == GID:
        sheet_name = sheet['properties']['title']
        break

if sheet_name:
    print(f"Sheet Name for GID {GID}: {sheet_name}")
    # Read first 10 rows
    result = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range=f"'{sheet_name}'!A1:Z10").execute()
    values = result.get('values', [])
    for row in values:
        print(row)
else:
    print(f"GID {GID} not found.")
