import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def undo_last_append(spreadsheet_id, sheet_name, num_rows):
    creds_path = "/home/hermeswebui/.hermes/google_token.json"
    with open(creds_path, 'r') as f:
        info = json.load(f)
    creds = Credentials.from_authorized_user_info(info)
    service = build('sheets', 'v4', credentials=creds)
    
    spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheet_id = None
    for sheet in spreadsheet.get('sheets', []):
        if sheet['properties']['title'] == sheet_name:
            sheet_id = sheet['properties']['sheetId']
            break
    
    if sheet_id is None:
        print(f"Sheet {sheet_name} not found in {spreadsheet_id}")
        return

    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, range=f"'{sheet_name}'!A:A").execute()
    values = result.get('values', [])
    last_content_row = len(values)
    
    body = {
        "requests": [
            {
                "deleteDimension": {
                    "range": {
                        "sheetId": sheet_id,
                        "dimension": "ROWS",
                        "startIndex": last_content_row - num_rows,
                        "endIndex": last_content_row
                    }
                }
            }
        ]
    }
    service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
    print(f"Deleted last {num_rows} rows from {sheet_name} in {spreadsheet_id}")

undo_last_append("1jzgnRxmmLIe_DAZ7nwHSRXeO6sI4CRxlTatc0T88ukY", "Day Wise CAC Report", 14)
undo_last_append("1QQ_Z50FDAhuBbVX5ioCjfgyFjfhr3y0gMGbQqteQ1f8", "Day Wise CAC Report", 11)
