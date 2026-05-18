import os
import pandas as pd
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN_PATH = "/home/hermeswebui/.hermes/google_token.json"
SPREADSHEET_ID = "1HcqI8yYnM_ANdWMgD21fYRMNNfUAgM4kpaygm_8Ha0U"
SHEET_NAME = "May 4 Corrected Reflection" # The GID corresponds to this name in the spreadsheet

def update_sheet():
    df = pd.read_csv("may3_reflection_final_v3.csv")
    
    # Handle NaNs and infinite values for JSON serialization
    df = df.fillna(0)
    
    # Credentials
    creds = Credentials.from_authorized_user_file(TOKEN_PATH)
    service = build("sheets", "v4", credentials=creds)
    
    # Prepare data for update
    # Headers: Platform, Type, Account, Date, Campaign, Ad Name, Spends, Pannel_Lead, lead_LMS
    # Note: Column names in CSV might be slightly different, ensure they match the sheet's expectation.
    # Standardizing columns for the sheet:
    df_sheet = df[['Platform', 'Platform Type', 'Account', 'Date', 'Campaign', 'Ad Name', 'Spends', 'Pannel_Lead', 'lead_LMS']]
    values = [df_sheet.columns.tolist()] + df_sheet.values.tolist()
    
    # Clear and Update
    range_name = f"'{SHEET_NAME}'!A1:I{len(values) + 1}"
    
    # Clear first
    service.spreadsheets().values().clear(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name
    ).execute()
    
    # Update
    body = {"values": values}
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name,
        valueInputOption="USER_ENTERED",
        body=body
    ).execute()
    
    print(f"Successfully updated {len(values)-1} rows in {SHEET_NAME}.")

if __name__ == "__main__":
    update_sheet()
