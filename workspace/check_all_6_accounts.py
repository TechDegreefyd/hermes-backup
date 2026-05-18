import requests
import json

TOKEN = ""

# Fetch all account IDs again
resp = requests.get(f"https://graph.facebook.com/v19.0/me/adaccounts?fields=name,account_id&access_token={TOKEN}").json()
accounts = resp.get('data', [])

print(f"{'Account Name':<25} | {'Account ID':<20} | {'Spend (May 4)':<10}")
print("-" * 60)

for acc in accounts:
    acc_id = acc['account_id']
    url = f"https://graph.facebook.com/v19.0/act_{acc_id}/insights"
    params = {
        'access_token': TOKEN,
        'time_range': json.dumps({'since': '2026-05-04', 'until': '2026-05-04'}),
        'level': 'account',
        'fields': 'spend'
    }
    r = requests.get(url, params=params).json()
    spend = r['data'][0]['spend'] if r.get('data') else "0.00"
    print(f"{acc['name']:<25} | {acc_id:<20} | {spend:<10}")
