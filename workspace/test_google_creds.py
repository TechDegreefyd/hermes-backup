import sys
sys.path.append('/home/hermeswebui/.hermes/skills/productivity/google-workspace/scripts')
from google_api import build_service

service = build_service('sheets', 'v4')
sheet_metadata = service.spreadsheets().get(spreadsheetId="1jzgnRxmmLIe_DAZ7nwHSRXeO6sI4CRxlTatc0T88ukY").execute()

for sheet in sheet_metadata.get('sheets', ''):
    print(f"Title: {sheet['properties']['title']}, SheetId: {sheet['properties']['sheetId']}")
