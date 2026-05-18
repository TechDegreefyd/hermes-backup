
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import pandas as pd
svc = build('sheets', 'v4', credentials=Credentials.from_authorized_user_file('/home/hermeswebui/.hermes/google_token.json'))
r = svc.spreadsheets().values().get(spreadsheetId='1QQ_Z50FDAhuBbVX5ioCjfgyFjfhr3y0gMGbQqteQ1f8', range="'FFH & Above'!A1:Z2000").execute()
df = pd.DataFrame(r['values'][1:], columns=r['values'][0])
may_forms = df[df['Form Month'].str.contains('May', na=False)]
print(f'May Forms count: {len(may_forms)}')
print(may_forms[['Student Name', 'Form Date', 'Admission Date', 'Form Month']].tail(20).to_string())
