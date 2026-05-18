import requests

TOKEN = ""

# 1. Fetch all accounts
resp = requests.get(f"https://graph.facebook.com/v19.0/me/adaccounts?fields=name,account_id&access_token={TOKEN}").json()
accounts = resp.get('data', [])

target_substr = "UA"

for acc in accounts:
    acc_id = acc['account_id']
    url = f"https://graph.facebook.com/v19.0/act_{acc_id}/campaigns"
    params = {'access_token': TOKEN, 'fields': 'name,id', 'limit': 500}
    c_resp = requests.get(url, params=params).json()
    found = False
    for c in c_resp.get('data', []):
        if target_substr in c['name']:
            print(f"MATCH: Account '{acc['name']}' ({acc_id}) has campaign '{c['name']}' (ID: {c['id']})")
            found = True
    if not found:
        # Also check ad sets just in case
        url_as = f"https://graph.facebook.com/v19.0/act_{acc_id}/adsets"
        as_resp = requests.get(url_as, params={'access_token': TOKEN, 'fields': 'name', 'limit': 500}).json()
        for aset in as_resp.get('data', []):
            if target_substr in aset['name']:
                print(f"ADSET MATCH: Account '{acc['name']}' ({acc_id}) has adset '{aset['name']}'")
