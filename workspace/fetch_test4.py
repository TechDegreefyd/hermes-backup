import json
import pandas as pd
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN_PATH = "/home/hermeswebui/.hermes/google_token.json"
creds = Credentials.from_authorized_user_file(TOKEN_PATH)
service = build("sheets", "v4", credentials=creds)
spreadsheet_id = "1jzgnRxmmLIe_DAZ7nwHSRXeO6sI4CRxlTatc0T88ukY"

res = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range="'Day Wise CAC Report'!A1:S5000").execute()
rows = res.get('values', [])
headers = [str(h).strip() for h in rows[1]]
df = pd.DataFrame(rows[2:], columns=headers)
print("Unique Types:", df['Type'].unique())
print("Unique Accounts:", df['Account'].unique())
