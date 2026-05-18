import os
import requests
import json
import csv

ACCESS_TOKEN = os.getenv("GOOGLE_ACCESS_TOKEN")
SPREADSHEET_ID = "1HcqI8yYnM_ANdWMgD21fYRMNNfUAgM4kpaygm_8Ha0U"
SHEET_NAME = "Meta Data 5-7 May"

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

# 1. Clear existing data in the tab (or just overwrite)
# Re-reading CSV
rows = []
csv_path = '/home/mohit/workspace/meta_data_05_07_final.csv'
with open(csv_path, 'r', newline='') as f:
    reader = csv.reader(f)
    for row in reader:
        processed_row = []
        for cell in row:
            try:
                if '.' in cell:
                    processed_row.append(float(cell))
                else:
                    processed_row.append(int(cell))
            except ValueError:
                processed_row.append(cell)
        rows.append(processed_row)

# 2. Update values (this will overwrite)
update_url = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/'{SHEET_NAME}'!A1?valueInputOption=USER_ENTERED"
update_body = {
    "values": rows
}
resp = requests.put(update_url, headers=headers, json=update_body)
print(f"Update values response: {resp.status_code}")
if resp.status_code != 200:
    print(resp.text)
else:
    print(f"Successfully uploaded {len(rows)} rows with LMS Leads to tab '{SHEET_NAME}'.")
