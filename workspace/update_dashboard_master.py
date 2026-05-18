import json
import pandas as pd
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Credentials
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

# 1. Read existing Master sheet to find column indices and row positions
# Assuming gid=0 is the first sheet or named 'Master' or similar. 
# I'll fetch the first sheet's data.
spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
sheet_name = spreadsheet['sheets'][0]['properties']['title']
print(f"Targeting sheet: {sheet_name}")

result = service.spreadsheets().values().get(
    spreadsheetId=SPREADSHEET_ID, range=f"'{sheet_name}'!A1:Z5000").execute()
rows = result.get('values', [])

if not rows:
    print("No data found in Master sheet.")
    exit(1)

# Find header row (usually row 2 based on history, or row 1)
header_row_idx = 1 # Defaulting to 0-indexed 1 (Row 2) as per previous context
header = rows[header_row_idx]
print(f"Header found: {header}")

# Map columns
col_map = {col: i for i, col in enumerate(header)}
req_cols = ['Date', 'Account', 'Campaign', 'Ad Name', 'Panel Leads', 'LMS Leads', 'Spends (₹)']
for c in req_cols:
    if c not in col_map:
        # Try to find partial matches if exact fails
        for actual_col in header:
            if c.lower() in actual_col.lower():
                col_map[c] = header.index(actual_col)
                break

print(f"Column mapping: {col_map}")

# 2. Load corrected data
df_corrected = pd.read_csv('may4_reflection_final.csv')
df_corrected['Date'] = pd.to_datetime(df_corrected['Date']).dt.strftime('%Y-%m-%d')

# 3. Prepare updates
updates = []
for _, c_row in df_corrected.iterrows():
    found = False
    # Search for matching row in the sheet
    for i, s_row in enumerate(rows[header_row_idx + 1:], start=header_row_idx + 2):
        # Match on Date, Account, Campaign, Ad Name
        try:
            s_date = pd.to_datetime(s_row[col_map['Date']]).strftime('%Y-%m-%d')
            s_acc = s_row[col_map['Account']]
            s_camp = s_row[col_map['Campaign']]
            s_ad = s_row[col_map['Ad Name']]
            
            if (s_date == c_row['Date'] and 
                s_acc == c_row['Account'] and 
                s_camp == c_row['Campaign'] and 
                s_ad == c_row['Ad Name']):
                
                # Update Panel Leads, LMS Leads, Spends
                updates.append({
                    'range': f"'{sheet_name}'!{chr(65 + col_map['Panel Leads'])}{i}",
                    'values': [[int(c_row['Pannel_Lead'])]]
                })
                updates.append({
                    'range': f"'{sheet_name}'!{chr(65 + col_map['LMS Leads'])}{i}",
                    'values': [[int(c_row['LMS Leads'])]]
                })
                updates.append({
                    'range': f"'{sheet_name}'!{chr(65 + col_map['Spends (₹)'])}{i}",
                    'values': [[float(c_row['Spends'])]]
                })
                found = True
                break
        except (IndexError, ValueError, KeyError):
            continue
            
    if not found:
        # If not found, we might need to append. 
        # But for "patching", we focus on existing rows first.
        print(f"Row not found for: {c_row['Campaign']} | {c_row['Ad Name']}")

# 4. Batch update
if updates:
    body = {
        'valueInputOption': 'USER_ENTERED',
        'data': updates
    }
    service.spreadsheets().values().batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()
    print(f"Applied {len(updates)//3} row updates to Master sheet.")
else:
    print("No matching rows found to update.")

