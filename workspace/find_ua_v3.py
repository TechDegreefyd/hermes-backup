import requests
import json

TOKEN = ""

# 1. Fetch all accounts this token can see
url = "https://graph.facebook.com/v19.0/me/adaccounts"
params = {
    'fields': 'name,account_id,id,account_status',
    'access_token': TOKEN,
    'limit': 200
}

resp = requests.get(url, params=params).json()
accounts = resp.get('data', [])

print(f"Total accounts found: {len(accounts)}")
for acc in accounts:
    if "univ" in acc['name'].lower() or "admit" in acc['name'].lower():
        print(f"MATCH: Name: {acc['name']}, ID: {acc['account_id']}, Status: {acc['account_status']}")

# 2. Try fetching insights for the suspected account ID specifically for May 4th
# but let's try WITHOUT level='ad' first to see if level='account' returns anything.
target_id = "1798418091554447"
print(f"\nChecking insights for {target_id} on 2026-05-04...")
ins_url = f"https://graph.facebook.com/v19.0/act_{target_id}/insights"
ins_params = {
    'access_token': TOKEN,
    'time_range': json.dumps({'since': '2026-05-04', 'until': '2026-05-04'}),
    'level': 'account',
    'fields': 'spend,account_name'
}
ins_resp = requests.get(ins_url, params=ins_params).json()
print("Account Level Insights:", ins_resp)

# 3. Check if there are any 'Business' objects the user is part of and list those accounts
biz_url = "https://graph.facebook.com/v19.0/me/businesses"
biz_resp = requests.get(biz_url, params={'access_token': TOKEN}).json()
print("\nBusiness Access:", biz_resp)
