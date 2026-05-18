import subprocess
import json
import os

GAPI_PATH = "/home/hermeswebui/.hermes/skills/productivity/google-workspace/scripts/google_api.py"

def run_gapi(args):
    cmd = ["python3", GAPI_PATH] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"GAPI Error: {result.stderr}")
        return None
    try:
        return json.loads(result.stdout)
    except:
        return result.stdout

with open('patched_data.json', 'r') as f:
    data = json.load(f)

# Patch Online Sheet
print("Patching Online Sheet (Day Wise CAC Report)...")
# Using the correct sheet title found from metadata
run_gapi(["sheets", "append", "1jzgnRxmmLIe_DAZ7nwHSRXeO6sI4CRxlTatc0T88ukY", "Day Wise CAC Report!A:I", "--values", json.dumps(data['online'])])

# Patch Regular Sheet
print("Patching Regular Sheet (Day Wise CAC Report)...")
run_gapi(["sheets", "append", "1QQ_Z50FDAhuBbVX5ioCjfgyFjfhr3y0gMGbQqteQ1f8", "Day Wise CAC Report!A:I", "--values", json.dumps(data['regular'])])

print("Done.")
