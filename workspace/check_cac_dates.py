
import pandas as pd
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import json

SHEET_ID_REGULAR = '1QQ_Z50FDAhuBbVX5ioCjfgyFjfhr3y0gMGbQqteQ1f8'
creds = Credentials.from_authorized_user_file('/home/hermeswebui/.hermes/google_token.json')
svc = build('sheets', 'v4', credentials=creds)

r = svc.spreadsheets().values().get(spreadsheetId=SHEET_ID_REGULAR, range="'Day Wise CAC Report'!A1:S20000").execute()
rows = r.get('values', [])
df = pd.DataFrame(rows[2:], columns=[str(c).strip() for c in rows[1]])
df['Date_Parsed'] = pd.to_datetime(df['Date'], errors='coerce')
df = df.dropna(subset=['Date_Parsed'])
print(f"Max Date in Regular CAC: {df['Date_Parsed'].max()}")

# List last 10 dates
print("\nLast 10 dates in CAC:")
print(df['Date_Parsed'].sort_values().tail(10).unique())
