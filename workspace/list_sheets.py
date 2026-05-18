import json
import os
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

TOKEN_PATH = os.path.expanduser('~/.hermes/google_token.json')
with open(TOKEN_PATH, 'r') as f:
    creds_data = json.load(f)
    creds = Credentials.from_authorized_user_info(creds_data)

service = build('sheets', 'v4', credentials=creds)

for sid in ['1jzgnRxmmLIe_DAZ7nwHSRXeO6sI4CRxlTatc0T88ukY', '1QQ_Z50FDAhuBbVX5ioCjfgyFjfhr3y0gMGbQqteQ1f8']:
    spreadsheet = service.spreadsheets().get(spreadsheetId=sid).execute()
    sheets = spreadsheet.get('sheets', [])
    print(f"ID: {sid}")
    for sheet in sheets:
        print(f"  - {sheet.get('properties', {}).get('title')}")
