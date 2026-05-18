
import pandas as pd
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

svc = build('sheets', 'v4', credentials=Credentials.from_authorized_user_file('/home/hermeswebui/.hermes/google_token.json'))
r = svc.spreadsheets().values().get(spreadsheetId='1jzgnRxmmLIe_DAZ7nwHSRXeO6sI4CRxlTatc0T88ukY', range="'FFH & Above'!A1:Z1000").execute()
df = pd.DataFrame(r['values'][1:], columns=[str(c).strip() for c in r['values'][0]])
df.columns = [c.strip() for c in df.columns]

print("Admission Type counts in Online:")
print(df['Admission Type'].value_counts().head(20))
