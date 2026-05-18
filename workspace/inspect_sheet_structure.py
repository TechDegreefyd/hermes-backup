import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN_FILE = '/home/hermeswebui/.hermes/google_token.json'
with open(TOKEN_FILE, 'r') as f:
    creds_info = json.load(f)

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

result = service.spreadsheets().values().get(
    spreadsheetId=SPREADSHEET_ID, range="Sheet1!A1:J20").execute()
rows = result.get('values', [])
for i, row in enumerate(rows):
    print(f"Row {i+1}: {row}")
