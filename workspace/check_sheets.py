
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import json

SHEET_ID = "1jzgnRxmmLIe_DAZ7nwHSRXeO6sI4CRxlTatc0T88ukY"

creds = Credentials.from_authorized_user_file('/home/hermeswebui/.hermes/google_token.json')
service = build('sheets', 'v4', credentials=creds)

# Get FFH & Above headers + first 5 rows
r1 = service.spreadsheets().values().get(
    spreadsheetId=SHEET_ID,
    range='FFH & Above!A1:Z6'
).execute()
print("=== FFH & Above sheet (first 6 rows) ===")
for row in r1.get('values', []):
    print(row)

# Total rows
r2 = service.spreadsheets().values().get(
    spreadsheetId=SHEET_ID,
    range='FFH & Above!A:A'
).execute()
print(f"\nTotal rows in FFH & Above: {len(r2.get('values', []))}")

r3 = service.spreadsheets().values().get(
    spreadsheetId=SHEET_ID,
    range='Day Wise CAC Report!A:A'
).execute()
print(f"Total rows in Day Wise CAC Report: {len(r3.get('values', []))}")

# Get latest dates in Day Wise CAC Report
r4 = service.spreadsheets().values().get(
    spreadsheetId=SHEET_ID,
    range='Day Wise CAC Report!A1:S20'
).execute()
print("\n=== Day Wise CAC Report latest rows (checking date col) ===")
rows = r4.get('values', [])
# Show last few rows for dates
r5 = service.spreadsheets().values().get(
    spreadsheetId=SHEET_ID,
    range='Day Wise CAC Report!A1:S5000'
).execute()
all_rows = r5.get('values', [])
print(f"Total data rows: {len(all_rows)}")
# Show last 5
print("Last 5 rows:")
for row in all_rows[-5:]:
    print(row)
