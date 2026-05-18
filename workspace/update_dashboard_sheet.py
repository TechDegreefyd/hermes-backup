import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# Define scope
scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

# Load credentials
creds = Credentials.from_service_account_file('/home/hermeswebui/.hermes/google_token.json', scopes=scope)
client = gspread.authorize(creds)

# Open the spreadsheet
sheet_id = '1HcqI8yYnM_ANdWMgD21fYRMNNfUAgM4kpaygm_8Ha0U'
spreadsheet = client.open_by_key(sheet_id)

# Try to find a sheet for May 4th, or create it
sheet_name = 'May 4 Corrected Reflection'
try:
    worksheet = spreadsheet.worksheet(sheet_name)
    worksheet.clear()
except gspread.exceptions.WorksheetNotFound:
    worksheet = spreadsheet.add_worksheet(title=sheet_name, rows="100", cols="20")

# Load final reflection data
df = pd.read_csv('may4_reflection_final.csv')

# Prepare headers and values
# Note: Google Sheets index starts at 1, but clear() handled it.
# We want headers at row 2 for consistency with other sheets if preferred, 
# but for a clean reflection sheet, row 1 is fine.
headers = df.columns.tolist()
values = [headers] + df.values.tolist()

# Update worksheet
worksheet.update('A1', values)

# Formatting: Bold headers
worksheet.format('A1:I1', {'textFormat': {'bold': True}})

print(f"Successfully updated Dashboard Sheet: {sheet_name}")
