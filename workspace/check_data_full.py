import os
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

headers = [c.strip() for c in rows[1]]
df = pd.DataFrame(rows[2:], columns=headers)

print(f"Total Rows: {len(df)}")
print("\nUnique Platforms:", df['Platform'].unique())
print("\nUnique Types:", df['Type'].unique())

# Check where DSA and Brand are mentioned
dsa_rows = df[df['Campaign'].str.contains('DSA', case=False, na=False)]
brand_rows = df[df['Campaign'].str.contains('Brand', case=False, na=False)]

print(f"\nRows with 'DSA' in Campaign: {len(dsa_rows)}")
print(f"Rows with 'Brand' in Campaign: {len(brand_rows)}")

print("\nSample DSA rows:")
print(dsa_rows[['Platform', 'Type', 'Account', 'Campaign']].head(5))

print("\nSample Brand rows:")
print(brand_rows[['Platform', 'Type', 'Account', 'Campaign']].head(5))
