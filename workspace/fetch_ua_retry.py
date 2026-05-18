import requests
import json

TOKEN = ""
# Testing bothact_1798418091554447 and maybe finding if there's a sub-account structure.
ACCOUNT_ID = "1798418091554447"
DATE = "2026-05-04"

url = f"https://graph.facebook.com/v19.0/act_{ACCOUNT_ID}/insights"
params = {
    'access_token': TOKEN,
    'time_range': json.dumps({'since': DATE, 'until': DATE}),
    'level': 'ad',
    'fields': 'account_name,campaign_name,ad_name,spend,actions',
    'filtering': '[{"field":"spend","operator":"GREATER_THAN","value":0}]',
    'limit': 1000
}

resp = requests.get(url, params=params).json()
print("Direct Data:", json.dumps(resp, indent=2))

# If empty, check if filtering is the cause
if not resp.get('data'):
    params.pop('filtering')
    resp = requests.get(url, params=params).json()
    print("Without filtering:", json.dumps(resp, indent=2))

