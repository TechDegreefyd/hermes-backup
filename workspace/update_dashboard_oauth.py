import os
import json
import pandas as pd
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Credentials
TOKEN_FILE = '/home/hermeswebui/.hermes/google_token.json'

with open(TOKEN_FILE, 'r') as f:
    creds_info = json.load(f)

# The token file structure might vary, but usually has 'token', 'refresh_token', 'client_id', 'client_secret'
creds = Credentials(
    token=creds_info.get('token'),
    refresh_token=creds_info.get('refresh_token'),
    token_uri=creds_info.get('token_uri', 'https://oauth2.googleapis.com/token'),
    client_id=creds_info.get('client_id'),
    client_secret=creds_info.get('client_secret'),
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)

service = build('sheets', 'v4', credentials=creds)

SPREADSHEET_ID = '1HcqI8yYnM_ANdWMgD21fYRMNNfUAgM4kpaygm_8Ha0U'
df = pd.read_csv('may4_reflection_final.csv')

# Convert DataFrame to list of lists
values = [df.columns.tolist()] + df.values.tolist()
body = {'values': values}

sheet_name = 'May 4 Corrected Reflection'

# Clear and update (using sheet name range)
try:
    service.spreadsheets().values().clear(spreadsheetId=SPREADSHEET_ID, range=f"'{sheet_name}'!A1:Z100").execute()
except Exception:
    # If sheet doesn't exist, create it
    spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    add_sheet_body = {
        'requests': [{
            'addSheet': {
                'properties': {
                    'title': sheet_name
                }
            }
        }]
    }
    service.spreadsheets().batchUpdate(spreadsheetId=SPREADSHEET_ID, body=add_sheet_body).execute()

result = service.spreadsheets().values().update(
    spreadsheetId=SPREADSHEET_ID, range=f"'{sheet_name}'!A1",
    valueInputOption='USER_ENTERED', body=body).execute()

print(f"Updated {result.get('updatedCells')} cells in sheet '{sheet_name}'.")
