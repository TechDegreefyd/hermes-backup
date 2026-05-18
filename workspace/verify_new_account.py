import requests
import json

TOKEN = ""
ACCOUNT_ID = "943943398169185"

url = f"https://graph.facebook.com/v19.0/act_{ACCOUNT_ID}/insights"
params = {
    'access_token': TOKEN,
    'time_range': json.dumps({'since': '2026-05-04', 'until': '2026-05-04'}),
    'level': 'ad',
    'fields': 'account_name,campaign_name,ad_name,spend,actions',
    'limit': 1000
}

resp = requests.get(url, params=params).json()
if 'error' in resp:
    print(f"ERROR: {resp['error'].get('message')}")
else:
    print(f"SUCCESS: Found {len(resp.get('data', []))} ad records for University_Admit_01.")
    # Show first few to verify
    for entry in resp.get('data', [])[:3]:
        print(f"- {entry['campaign_name']} | {entry['ad_name']} | Spend: {entry['spend']}")
