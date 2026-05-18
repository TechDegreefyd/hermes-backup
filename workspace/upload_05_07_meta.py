import os
import csv
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN_PATH = '/home/mohit/.hermes/google_token.json'
creds = Credentials.from_authorized_user_file(TOKEN_PATH)
service = build('sheets', 'v4', credentials=creds)

SPREADSHEET_ID = '1HcqI8yYnM_ANdWMgD21fYRMNNfUAgM4kpaygm_8Ha0U'
NEW_SHEET_NAME = "Meta Data 5-7 May"

# First, create the sheet
try:
    batch_update_spreadsheet_request_body = {
        'requests': [
            {
                'addSheet': {
                    'properties': {
                        'title': NEW_SHEET_NAME
                    }
                }
            }
        ]
    }
    service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body=batch_update_spreadsheet_request_body
    ).execute()
    print(f"Created sheet: {NEW_SHEET_NAME}")
except Exception as e:
    print(f"Sheet might already exist or error: {e}")

# Read the data using csv module
rows = []
csv_path = '/home/mohit/workspace/meta_data_05_07.csv'
with open(csv_path, 'r', newline='') as f:
    reader = csv.reader(f)
    for row in reader:
        # Convert numeric strings to floats/ints for better sheet formatting
        processed_row = []
        for cell in row:
            try:
                if '.' in cell:
                    processed_row.append(float(cell))
                else:
                    processed_row.append(int(cell))
            except ValueError:
                processed_row.append(cell)
        rows.append(processed_row)

if rows:
    body = {'values': rows}
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID, 
        range=f"'{NEW_SHEET_NAME}'!A1", 
        valueInputOption='USER_ENTERED', 
        body=body
    ).execute()
    print(f"Populated {len(rows)-1} rows to {NEW_SHEET_NAME}")
else:
    print("No data found to upload.")
