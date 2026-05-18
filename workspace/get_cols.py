
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
svc = build('sheets', 'v4', credentials=Credentials.from_authorized_user_file('/home/hermeswebui/.hermes/google_token.json'))
r = svc.spreadsheets().values().get(spreadsheetId='1QQ_Z50FDAhuBbVX5ioCjfgyFjfhr3y0gMGbQqteQ1f8', range="'FFH & Above'!A1:Z1").execute()
print(r.get('values',[])[0])
