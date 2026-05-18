
import pandas as pd
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

SHEET_ID_REGULAR = '1QQ_Z50FDAhuBbVX5ioCjfgyFjfhr3y0gMGbQqteQ1f8'
creds = Credentials.from_authorized_user_file('/home/hermeswebui/.hermes/google_token.json')
svc = build('sheets', 'v4', credentials=creds)

# CAC
r = svc.spreadsheets().values().get(spreadsheetId=SHEET_ID_REGULAR, range="'Day Wise CAC Report'!A1:S20000").execute()
cac_raw = r.get('values',[])
headers = [str(c).strip() for c in cac_raw[1]]
df = pd.DataFrame(cac_raw[2:], columns=headers[:len(cac_raw[2])])

print("CAC Columns:", list(df.columns))

# FFH
r2 = svc.spreadsheets().values().get(spreadsheetId=SHEET_ID_REGULAR, range="'FFH & Above'!A1:Z5000").execute()
ffh_raw = r2.get('values',[])
headers_ffh = [str(c).strip() for c in ffh_raw[0]]
df_ffh = pd.DataFrame(ffh_raw[1:], columns=headers_ffh[:len(ffh_raw[1])])

print("FFH Columns:", list(df_ffh.columns))

# Check Campaign mapping
print("\nSample FFH Campaign fields:")
print(df_ffh[['Campaign Name', 'Campaign ID']].head(5).to_string())

print("\nSample CAC Campaign fields:")
print(df[['Campaign', 'Ad Name']].head(5).to_string())
