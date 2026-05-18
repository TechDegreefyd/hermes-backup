
import pandas as pd
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

SHEET_ID_REGULAR = '1QQ_Z50FDAhuBbVX5ioCjfgyFjfhr3y0gMGbQqteQ1f8'
creds = Credentials.from_authorized_user_file('/home/hermeswebui/.hermes/google_token.json')
svc = build('sheets', 'v4', credentials=creds)

r_cac = svc.spreadsheets().values().get(spreadsheetId=SHEET_ID_REGULAR, range="'Day Wise CAC Report'!A1:S20000").execute()
df_cac = pd.DataFrame(r_cac['values'][2:], columns=[str(c).strip() for c in r_cac['values'][1]])

r_ffh = svc.spreadsheets().values().get(spreadsheetId=SHEET_ID_REGULAR, range="'FFH & Above'!A1:Z5000").execute()
df_ffh = pd.DataFrame(r_ffh['values'][1:], columns=[str(c).strip() for c in r_ffh['values'][0]])

# Get unique campaign identifiers from CAC
cac_camps = set(df_cac['Campaign'].astype(str).str.strip()) | set(df_cac['Ad Name'].astype(str).str.strip())

# Check mapping from FFH
df_ffh['C_ID'] = df_ffh['Campaign ID'].astype(str).str.strip()
df_ffh['C_Name'] = df_ffh['Campaign Name'].astype(str).str.strip()

mapped = df_ffh[df_ffh['C_ID'].isin(cac_camps) | df_ffh['C_Name'].isin(cac_camps)]
unmapped = df_ffh[~(df_ffh['C_ID'].isin(cac_camps) | df_ffh['C_Name'].isin(cac_camps))]

print(f"Total FFH Rows: {len(df_ffh)}")
print(f"Mapped: {len(mapped)}")
print(f"Unmapped: {len(unmapped)}")

if len(unmapped) > 0:
    print("\nSample Unmapped Rows:")
    print(unmapped[['Campaign Name', 'Campaign ID']].head(20).to_string())
    
print("\nUnique Campaign/Ad Names in CAC (first 20):")
print(list(cac_camps)[:20])
