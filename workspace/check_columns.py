import subprocess, json, sys

GAPI_SCRIPT = '/home/mohit/.hermes/skills/productivity/google-workspace/scripts/google_api.py'

amp = chr(38)  # &

# Online CAC
SHEET_ID = '1jzgnRxmmLIe_DAZ7nwHSRXeO6sI4CRxlTatc0T88ukY'
rng = "'Day Wise CAC Report'!A1:S3"
cmd = [sys.executable, GAPI_SCRIPT, 'sheets', 'get', SHEET_ID, rng]
r = subprocess.run(cmd, capture_output=True, text=True)
cac = json.loads(r.stdout)
print('=== ONLINE CAC headers (row 1):')
for i, h in enumerate(cac[1] if len(cac)>1 else []):
    print(f'  [{i}] "{h}"')
print('=== ONLINE CAC row 2:')
for i, h in enumerate(cac[2] if len(cac)>2 else []):
    print(f'  [{i}] "{h}"')

# Online FFH
tab = f"'FFH {amp} Above'!A1:Z2"
cmd2 = [sys.executable, GAPI_SCRIPT, 'sheets', 'get', SHEET_ID, tab]
r2 = subprocess.run(cmd2, capture_output=True, text=True)
crm = json.loads(r2.stdout)
print('=== ONLINE FFH headers (row 0):')
for i, h in enumerate(crm[0] if crm else []):
    print(f'  [{i}] "{h}"')
