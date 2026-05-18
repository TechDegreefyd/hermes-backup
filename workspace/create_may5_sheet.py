import os
import pandas as pd
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN_PATH = '/home/hermeswebui/.hermes/google_token.json'
creds = Credentials.from_authorized_user_file(TOKEN_PATH)
service = build('sheets', 'v4', credentials=creds)

SPREADSHEET_ID = '1HcqI8yYnM_ANdWMgD21fYRMNNfUAgM4kpaygm_8Ha0U'
NEW_SHEET_NAME = "May 5 Reflection"

# 1. Create the sheet if it doesn't exist
sheet_metadata = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
sheet_id = None
for sheet in sheet_metadata['sheets']:
    if sheet['properties']['title'] == NEW_SHEET_NAME:
        sheet_id = sheet['properties']['sheetId']
        break

if not sheet_id:
    batch_update_request = {
        'requests': [{'addSheet': {'properties': {'title': NEW_SHEET_NAME}}}]
    }
    response = service.spreadsheets().batchUpdate(spreadsheetId=SPREADSHEET_ID, body=batch_update_request).execute()
    sheet_id = response['replies'][0]['addSheet']['properties']['sheetId']
    print(f"Created new sheet: {NEW_SHEET_NAME}")
else:
    print(f"Sheet {NEW_SHEET_NAME} already exists.")

# 2. Populate data
df = pd.read_csv('may5_reflection_final.csv')
# Formatting for sheet
# Columns in CSV: Platform, Account, Date, Campaign, Ad Name, Spends, Pannel_Lead, LMS Leads
# Rearrange to match May 4 structure: Platform, Platform Type, Account, Date, Campaign, Ad Name, Spends, Pannel_Lead, LMS Leads
rows = [["Platform", "Platform Type", "Account", "Date", "Campaign", "Ad Name", "Spends", "Pannel_Lead", "LMS Leads"]]
for _, r in df.iterrows():
    rows.append([
        "Meta",
        "Lead Gen",
        r['Account'],
        r['Date'],
        r['Campaign'],
        r['Ad Name'],
        float(r['Spends (₹)']),
        int(r['Pannel_Lead']),
        int(r['LMS Leads'])
    ])

body = {'values': rows}
service.spreadsheets().values().update(
    spreadsheetId=SPREADSHEET_ID, 
    range=f"'{NEW_SHEET_NAME}'!A1", 
    valueInputOption='USER_ENTERED', 
    body=body
).execute()
print(f"Populated {len(rows)-1} rows to {NEW_SHEET_NAME}")
