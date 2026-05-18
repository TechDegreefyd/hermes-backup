import subprocess, json, sys

GAPI_SCRIPT = '/home/mohit/.hermes/skills/productivity/google-workspace/scripts/google_api.py'

amp = chr(38)

# Regular CAC
SHEET_ID = '1QQ_Z50FDAhuBbVX5ioCjfgyFjfhr3y0gMGbQqteQ1f8'
rng = "'Day Wise CAC Report'!A1:S3"
cmd = [sys.executable, GAPI_SCRIPT, 'sheets', 'get', SHEET_ID, rng]
r = subprocess.run(cmd, capture_output=True, text=True)
cac = json.loads(r.stdout)
print('=== REGULAR CAC headers (row 1):')
for i, h in enumerate(cac[1] if len(cac)>1 else []):
    print(f'  [{i}] "{h}"')

# Regular FFH
tab = f"'FFH {amp} Above'!A1:Z2"
cmd2 = [sys.executable, GAPI_SCRIPT, 'sheets', 'get', SHEET_ID, tab]
r2 = subprocess.run(cmd2, capture_output=True, text=True)
crm = json.loads(r2.stdout)
print('=== REGULAR FFH headers (row 0):')
for i, h in enumerate(crm[0] if crm else []):
    print(f'  [{i}] "{h}"')
