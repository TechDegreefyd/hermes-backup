import os
import pandas as pd
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN_PATH = '/home/hermeswebui/.hermes/google_token.json'
creds = Credentials.from_authorized_user_file(TOKEN_PATH)
service = build('sheets', 'v4', credentials=creds)

SPREADSHEET_ID = '1HcqI8yYnM_ANdWMgD21fYRMNNfUAgM4kpaygm_8Ha0U'
GID = '1234636367'

# 1. Identify sheet name from GID
sheet_metadata = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
sheet_name = None
for sheet in sheet_metadata['sheets']:
    if str(sheet['properties']['sheetId']) == GID:
        sheet_name = sheet['properties']['title']
        break

if not sheet_name:
    print(f"GID {GID} not found.")
    exit(1)

# 2. Clear existing sheet content
service.spreadsheets().values().clear(spreadsheetId=SPREADSHEET_ID, range=f"'{sheet_name}'!A:Z").execute()

# 3. Populate new data
df = pd.read_csv('may3_reflection_final.csv')
rows = [df.columns.tolist()] + df.values.tolist()

body = {'values': rows}
service.spreadsheets().values().update(
    spreadsheetId=SPREADSHEET_ID, 
    range=f"'{sheet_name}'!A1", 
    valueInputOption='USER_ENTERED', 
    body=body
).execute()
print(f"Updated '{sheet_name}' (GID {GID}) with {len(rows)-1} rows for May 3.")
