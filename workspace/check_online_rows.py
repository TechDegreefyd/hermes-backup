import subprocess, json, sys

GAPI_SCRIPT = '/home/mohit/.hermes/skills/productivity/google-workspace/scripts/google_api.py'

# Check the Online sheet to see if row 1 has duplicate Campaign and no Ad Name
SHEET_ID = '1jzgnRxmmLIe_DAZ7nwHSRXeO6sI4CRxlTatc0T88ukY'
rng = "'Day Wise CAC Report'!A1:S5"
cmd = [sys.executable, GAPI_SCRIPT, 'sheets', 'get', SHEET_ID, rng]
r = subprocess.run(cmd, capture_output=True, text=True)
cac = json.loads(r.stdout)
print(f"Total rows returned: {len(cac)}")
for i in range(min(5, len(cac))):
    print(f"\nRow {i}:")
    for j, val in enumerate(cac[i]):
        if val:
            print(f"  [{j}] = '{val}'")
