import requests
TOKEN = ""

# 1. Check direct accounts
print("--- Direct Ad Accounts ---")
resp = requests.get(f"https://graph.facebook.com/v19.0/me/adaccounts?fields=name,account_id&limit=100&access_token={TOKEN}").json()
for acc in resp.get('data', []):
    print(f"Name: {acc['name']}, ID: {acc['account_id']}")

# 2. Check accounts through reachable businesses
print("\n--- Business Ad Accounts ---")
biz_resp = requests.get(f"https://graph.facebook.com/v19.0/me/businesses?access_token={TOKEN}").json()
if 'data' in biz_resp:
    for biz in biz_resp['data']:
        accs = requests.get(f"https://graph.facebook.com/v19.0/{biz['id']}/adaccounts?fields=name,account_id&access_token={TOKEN}").json()
        for acc in accs.get('data', []):
            print(f"Biz: {biz['name']}, Name: {acc['name']}, ID: {acc['account_id']}")
else:
    print("No business access found or permission missing.")
