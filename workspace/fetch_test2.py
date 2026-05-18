import json
import pandas as pd
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN_PATH = "/home/hermeswebui/.hermes/google_token.json"
creds = Credentials.from_authorized_user_file(TOKEN_PATH)
service = build("sheets", "v4", credentials=creds)
spreadsheet_id = "1jzgnRxmmLIe_DAZ7nwHSRXeO6sI4CRxlTatc0T88ukY"

res = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range="DSA_graph1!A1:F5").execute()
print(res.get('values', []))
