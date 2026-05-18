
import pandas as pd
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

svc = build('sheets', 'v4', credentials=Credentials.from_authorized_user_file('/home/hermeswebui/.hermes/google_token.json'))
r = svc.spreadsheets().values().get(spreadsheetId='1QQ_Z50FDAhuBbVX5ioCjfgyFjfhr3y0gMGbQqteQ1f8', range="'FFH & Above'!A1:Z5000").execute()
df = pd.DataFrame(r['values'][1:], columns=[str(c).strip() for c in r['values'][0]])
df.columns = [c.strip() for c in df.columns]

print("Check Counted or Not distribution (Regular):")
print(df['Check Counted or Not'].value_counts())
