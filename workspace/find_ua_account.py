import requests
TOKEN = ""
resp = requests.get(f"https://graph.facebook.com/v19.0/me/adaccounts?fields=name,account_id&limit=100&access_token={TOKEN}").json()
for acc in resp.get('data', []):
    if "University" in acc['name']:
        print(f"Found: {acc['name']} ({acc['account_id']})")
