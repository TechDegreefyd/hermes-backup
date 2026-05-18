import os
import json
import pandas as pd
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN_PATH = "/home/hermeswebui/.hermes/google_token.json"
creds = Credentials.from_authorized_user_file(TOKEN_PATH)
service = build("sheets", "v4", credentials=creds)
spreadsheet_id = "1jzgnRxmmLIe_DAZ7nwHSRXeO6sI4CRxlTatc0T88ukY"

res = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range="'Day Wise CAC Report'!A1:S1000").execute()
rows = res.get('values', [])

def pnum(val):
    try:
        s = str(val).replace(',', '').strip().replace('%', '').replace('₹', '')
        if s == '-' or s == '': return 0.0
        return float(s)
    except: return 0.0

headers = [c.strip() for c in rows[1]]
df = pd.DataFrame(rows[2:], columns=headers)
for col in ['Spends', 'Pannel_Lead', 'Lead_LMS', 'FFH', 'Adm']:
    df[col] = df[col].apply(pnum)

print(f"Total Rows: {len(df)}")
print("\nUnique Platforms:", df['Platform'].unique())
print("\nUnique Types:", df['Type'].unique())

# Check for empty accounts/campaigns
empty_accts = df[df['Account'].isna() | (df['Account'].str.strip() == '')]
print(f"\nRows with empty Account: {len(empty_accts)}")

# Check totals per Platform
print("\nTotals by Platform (Raw):")
print(df.groupby('Platform')[['Spends', 'Lead_LMS']].sum())

# Sample of data to see formatting
print("\nSample Rows:")
print(df[['Platform', 'Account', 'Campaign', 'Spends']].head(10))
