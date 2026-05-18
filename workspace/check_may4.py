
"""
Pull raw FFH & Above rows for May 4 and show exact Invoicing Variable values.
Cross-check what the user sees in the sheet.
"""
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import pandas as pd

SHEET_ID = "1jzgnRxmmLIe_DAZ7nwHSRXeO6sI4CRxlTatc0T88ukY"
creds = Credentials.from_authorized_user_file('/home/hermeswebui/.hermes/google_token.json')
service = build('sheets', 'v4', credentials=creds)

r = service.spreadsheets().values().get(
    spreadsheetId=SHEET_ID,
    range='FFH & Above!A1:Z2000'
).execute()
rows = r.get('values', [])
headers = rows[0]
df = pd.DataFrame(rows[1:], columns=headers)

# Show all column names first
print("Columns:", list(df.columns))
print(f"Total rows: {len(df)}")

# Parse dates
df['Adm_Date_Parsed'] = pd.to_datetime(df['Admission Date'], format='%d/%b/%Y', errors='coerce')
df['Form_Date_Parsed'] = pd.to_datetime(df['Form Date'], format='%d/%b/%Y', errors='coerce')

# All rows with Adm Date = May 4
may4_adm = df[df['Adm_Date_Parsed'].dt.strftime('%Y-%m-%d') == '2026-05-04']
# All rows with Form Date = May 4
may4_form = df[df['Form_Date_Parsed'].dt.strftime('%Y-%m-%d') == '2026-05-04']

print(f"\n=== Rows with Admission Date = 04/May/2026 ({len(may4_adm)} rows) ===")
print(f"{'#':<3} {'Student Name':<30} {'Admission Date':<18} {'Invoicing Variable':<20} {'Total Variable':<15} {'Fee Submitted':<15} {'Campaign Name'}")
print("-"*130)
for i, (_, row) in enumerate(may4_adm.iterrows(), 1):
    print(f"{i:<3} {str(row.get('Student Name','')):<30} {str(row.get('Admission Date','')):<18} {str(row.get('Invoicing Variable','')):<20} {str(row.get('Total Variable','')):<15} {str(row.get('Fee Submitted','')):<15} {row.get('Campaign Name','')}")

# Raw Invoicing Variable values
inv_raw = may4_adm['Invoicing Variable'].tolist()
print(f"\nRaw Invoicing Variable values: {inv_raw}")

# Try to sum them
def parse_inv(v):
    try:
        return float(str(v).replace(',','').strip())
    except:
        return 0.0

inv_vals = [parse_inv(v) for v in inv_raw]
print(f"Parsed values: {inv_vals}")
print(f"Sum: ₹{sum(inv_vals):,.2f}")

print(f"\n=== Rows with Form Date = 04/May/2026 ({len(may4_form)} rows) ===")
print(f"{'#':<3} {'Student Name':<30} {'Form Date':<15} {'Campaign Name'}")
print("-"*80)
for i, (_, row) in enumerate(may4_form.iterrows(), 1):
    print(f"{i:<3} {str(row.get('Student Name','')):<30} {str(row.get('Form Date','')):<15} {row.get('Campaign Name','')}")
