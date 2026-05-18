
import pandas as pd
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import json

SHEET_ID_REGULAR = '1QQ_Z50FDAhuBbVX5ioCjfgyFjfhr3y0gMGbQqteQ1f8'
creds = Credentials.from_authorized_user_file('/home/hermeswebui/.hermes/google_token.json')
svc = build('sheets', 'v4', credentials=creds)

meta = svc.spreadsheets().get(spreadsheetId=SHEET_ID_REGULAR).execute()
sheet_names = [s['properties']['title'] for s in meta['sheets']]
print("Sheet Names in Regular Data Source:")
for s in sheet_names:
    print(f" - {s}")

if 'Day Wise CAC Report' in sheet_names:
    r_cac = svc.spreadsheets().values().get(spreadsheetId=SHEET_ID_REGULAR, range="'Day Wise CAC Report'!A1:S5").execute()
    print("\nHeaders in 'Day Wise CAC Report':")
    for row in r_cac.get('values', []):
        print(row)

if 'FFH & Above' in sheet_names:
    r_ffh = svc.spreadsheets().values().get(spreadsheetId=SHEET_ID_REGULAR, range="'FFH & Above'!A1:Z5").execute()
    print("\nHeaders in 'FFH & Above':")
    for row in r_ffh.get('values', []):
        print(row)
