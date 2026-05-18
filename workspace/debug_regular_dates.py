
import pandas as pd
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

svc = build('sheets', 'v4', credentials=Credentials.from_authorized_user_file('/home/hermeswebui/.hermes/google_token.json'))
r = svc.spreadsheets().values().get(spreadsheetId='1QQ_Z50FDAhuBbVX5ioCjfgyFjfhr3y0gMGbQqteQ1f8', range="'FFH & Above'!A1:Z5000").execute()
df = pd.DataFrame(r['values'][1:], columns=[str(c).strip() for c in r['values'][0]])
df.columns = [c.strip() for c in df.columns]

df['F_D'] = pd.to_datetime(df['Form Date'], format='%d/%b/%Y', errors='coerce')
target = pd.to_datetime('2026-05-04')

matches = df[df['F_D'] == target]
print(f"Regular Forms on May 4: {len(matches)}")
if len(matches) > 0:
    print(matches[['Student Name', 'Form Date']].to_string())
else:
    print("No matches found for 2026-05-04 using %d/%b/%Y")
    # Check if there are other formats
    print("Unique raw values in Form Date (last 50):")
    print(df['Form Date'].tail(50).unique())
