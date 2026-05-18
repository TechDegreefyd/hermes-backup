
import pandas as pd
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

svc = build('sheets', 'v4', credentials=Credentials.from_authorized_user_file('/home/hermeswebui/.hermes/google_token.json'))
r = svc.spreadsheets().values().get(spreadsheetId='1QQ_Z50FDAhuBbVX5ioCjfgyFjfhr3y0gMGbQqteQ1f8', range="'FFH & Above'!A1:Z5000").execute()
rows = r['values']
df = pd.DataFrame(rows[1:], columns=[str(c).strip() for c in rows[0]])

# Filter empty
df = df[df['Form Date'].str.strip() != '']
print(f"Total Non-Empty Form Dates: {len(df)}")
print("Last 20 non-empty form dates:")
print(df['Form Date'].tail(20).tolist())
