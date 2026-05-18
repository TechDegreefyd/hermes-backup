import pandas as pd
import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN_PATH = '/home/hermeswebui/.hermes/google_token.json'
creds = Credentials.from_authorized_user_file(TOKEN_PATH)
service = build('sheets', 'v4', credentials=creds)

ONLINE_ID = '1jzgnRxmmLIe_DAZ7nwHSRXeO6sI4CRxlTatc0T88ukY'
REGULAR_ID = '1QQ_Z50FDAhuBbVX5ioCjfgyFjfhr3y0gMGbQqteQ1f8'

df_final = pd.read_csv('may4_reflection_final_distributed_final.csv')

# Online Account Names (normalized for matching)
online_accounts = ['Degreefyd_B', 'DegreeFYD', 'University_Admit_01'] # Wait, Degreefyd_B was Regular in earlier context but Meta ads usually show specific names.
# Actually, let's use the 'Account' column in our CSV to split them.
# Degreefyd_B -> Regular
# DegreeFYD, University_Admit_01 -> Online

online_data = df_final[df_final['Account'].isin(['DegreeFYD', 'University_Admit_01'])]
regular_data = df_final[df_final['Account'] == 'Degreefyd_B']

def prepare_rows(df):
    rows = []
    for _, r in df.iterrows():
        # Columns: Platform, Type, Account, Date, Campaign, Ad Name, Spends, Pannel_Lead, Lead_LMS, FFH, ...
        # Based on index check: 0=Platform, 1=Type, 2=Account, 3=Date, 4=Campaign, 5=Ad Name, 6=Spends, 7=Pannel_Lead, 8=Lead_LMS
        row = ["Meta Ads", "", r['Account'], r['Date'], r['Campaign'], r['Ad Name'], r['Spends (₹)'], r['Panel Leads'], r['LMS Leads'], 0]
        rows.append(row)
    return rows

def update_sheet(spreadsheet_id, data_df):
    # 1. Find and Delete existing May 4 rows
    sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheet_name = sheet_metadata['sheets'][0]['properties']['title']
    
    result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=f"'{sheet_name}'!A:D").execute()
    values = result.get('values', [])
    
    delete_indices = []
    for i, row in enumerate(values):
        if len(row) > 3 and row[3] == '2026-05-04':
            delete_indices.append(i)
            
    if delete_indices:
        print(f"Found {len(delete_indices)} existing May 4 rows in {spreadsheet_id}. Deleting...")
        # Delete in reverse to maintain indices
        for idx in sorted(delete_indices, reverse=True):
            body = {
                "requests": [
                    {
                        "deleteDimension": {
                            "range": {
                                "sheetId": sheet_metadata['sheets'][0]['properties']['sheetId'],
                                "dimension": "ROWS",
                                "startIndex": idx,
                                "endIndex": idx + 1
                            }
                        }
                    }
                ]
            }
            service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()

    # 2. Append new rows
    new_rows = prepare_rows(data_df)
    if new_rows:
        body = {'values': new_rows}
        service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id, 
            range=f"'{sheet_name}'!A1", 
            valueInputOption='USER_ENTERED', 
            body=body
        ).execute()
        print(f"Appended {len(new_rows)} rows to {spreadsheet_id}")

print("Updating Online Sheet...")
update_sheet(ONLINE_ID, online_data)
print("Updating Regular Sheet...")
update_sheet(REGULAR_ID, regular_data)
