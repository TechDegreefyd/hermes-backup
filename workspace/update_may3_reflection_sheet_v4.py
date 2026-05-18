import os
import pandas as pd
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN_PATH = "/home/hermeswebui/.hermes/google_token.json"
SPREADSHEET_ID = "1HcqI8yYnM_ANdWMgD21fYRMNNfUAgM4kpaygm_8Ha0U"
SHEET_NAME = "May 4 Corrected Reflection" 

def update_sheet():
    df = pd.read_csv("may3_reflection_final_distributed_v4.csv")
    df = df.fillna(0)
    
    creds = Credentials.from_authorized_user_file(TOKEN_PATH)
    service = build("sheets", "v4", credentials=creds)
    
    # Platform, Platform Type, Account, Date, Campaign, Ad Name, Spends, Pannel_Lead, lead_LMS
    values = [df.columns.tolist()] + df.values.tolist()
    
    # The sheet likely has existing data (like headers), so we target the range
    range_name = f"'{SHEET_NAME}'!A1:I{len(values) + 1}"
    
    # Clear and Update
    service.spreadsheets().values().clear(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name
    ).execute()
    
    body = {"values": values}
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name,
        valueInputOption="USER_ENTERED",
        body=body
    ).execute()
    
    print(f"Successfully updated {len(values)-1} rows for May 3rd with 514 LMS leads.")

if __name__ == "__main__":
    update_sheet()
