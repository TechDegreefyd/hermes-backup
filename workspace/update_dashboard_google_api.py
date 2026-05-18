import os
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# Credentials
SERVICE_ACCOUNT_FILE = '/home/hermeswebui/.hermes/google_token.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('sheets', 'v4', credentials=creds)

SPREADSHEET_ID = '1HcqI8yYnM_ANdWMgD21fYRMNNfUAgM4kpaygm_8Ha0U'
df = pd.read_csv('may4_reflection_final.csv')

# Convert DataFrame to list of lists
values = [df.columns.tolist()] + df.values.tolist()
body = {'values': values}

# Create a new sheet or update existing one
sheet_name = 'May 4 Corrected Reflection'

# Check if sheet exists
spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
sheets = spreadsheet.get('sheets', [])
sheet_id = None
for s in sheets:
    if s.get('properties', {}).get('title') == sheet_name:
        sheet_id = s.get('properties', {}).get('sheetId')
        break

if sheet_id is None:
    # Add new sheet
    add_sheet_body = {
        'requests': [{
            'addSheet': {
                'properties': {
                    'title': sheet_name
                }
            }
        }]
    }
    res = service.spreadsheets().batchUpdate(spreadsheetId=SPREADSHEET_ID, body=add_sheet_body).execute()
    sheet_id = res['replies'][0]['addSheet']['properties']['sheetId']

# Clear and update
service.spreadsheets().values().clear(spreadsheetId=SPREADSHEET_ID, range=f"'{sheet_name}'!A1:Z100").execute()
result = service.spreadsheets().values().update(
    spreadsheetId=SPREADSHEET_ID, range=f"'{sheet_name}'!A1",
    valueInputOption='USER_ENTERED', body=body).execute()

print(f"Updated {result.get('updatedCells')} cells in sheet '{sheet_name}'.")
