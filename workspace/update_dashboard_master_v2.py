import json
import pandas as pd
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

# Load corrected data
df_corrected = pd.read_csv('may4_reflection_final.csv')
df_corrected['Date'] = pd.to_datetime(df_corrected['Date']).dt.strftime('%Y-%m-%d')

sheet_name = 'Sheet1'
result = service.spreadsheets().values().get(
    spreadsheetId=SPREADSHEET_ID, range=f"'{sheet_name}'!A1:I5000").execute()
rows = result.get('values', [])

header = rows[0]
col_map = {col: i for i, col in enumerate(header)}
print(f"Col Map: {col_map}")

updates = []
for _, c_row in df_corrected.iterrows():
    found = False
    c_acc = c_row['Account']
    # Handle the 'FaceBook_' prefix in the sheet
    
    for i, s_row in enumerate(rows[1:], start=2):
        try:
            # Handle variable row lengths
            if len(s_row) < 6: continue
            
            s_date = pd.to_datetime(s_row[col_map['Date']]).strftime('%Y-%m-%d')
            s_acc = s_row[col_map['Account']]
            s_camp = s_row[col_map['Campaign Name']]
            s_ad = s_row[col_map['Ad Name']]
            
            # Match (allowing for 'FaceBook_' prefix)
            if (s_date == c_row['Date'] and 
                (s_acc == c_acc or s_acc == f"FaceBook_{c_acc}") and 
                s_camp == c_row['Campaign'] and 
                s_ad == c_row['Ad Name']):
                
                # Update Panel Leads (Col H / Index 7), LMS Leads (Col I / Index 8)
                # Note: chr(65+7) = 'H', chr(65+8) = 'I'
                panel_col = chr(65 + col_map['Meta Panel Leads'])
                lms_col = chr(65 + col_map['LMS Verified Leads'])
                spend_col = chr(65 + col_map['Spends (₹)'])

                updates.append({'range': f"'{sheet_name}'!{panel_col}{i}", 'values': [[int(c_row['Pannel_Lead'])]]})
                updates.append({'range': f"'{sheet_name}'!{lms_col}{i}", 'values': [[int(c_row['LMS Leads'])]]})
                updates.append({'range': f"'{sheet_name}'!{spend_col}{i}", 'values': [[float(c_row['Spends'])]]})
                found = True
                break
        except Exception as e:
            continue
            
    if not found:
        # If not found, append to the end
        new_row = [
            'Meta', 
            'Leads', 
            f"FaceBook_{c_acc}" if not c_acc.startswith('FaceBook') else c_acc,
            c_row['Date'],
            c_row['Campaign'],
            c_row['Ad Name'],
            float(c_row['Spends']),
            int(c_row['Pannel_Lead']),
            int(c_row['LMS Leads'])
        ]
        updates.append({'range': f"'{sheet_name}'!A{len(rows)+1}", 'values': [new_row]})
        rows.append(new_row) # Update local list to prevent duplicate appends

if updates:
    body = {'valueInputOption': 'USER_ENTERED', 'data': updates}
    service.spreadsheets().values().batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()
    print(f"Applied {len(updates)} updates/appends to Master sheet.")
else:
    print("No updates needed.")
