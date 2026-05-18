import requests
TOKEN = ""
resp = requests.get(f"https://graph.facebook.com/v19.0/me/adaccounts?fields=name,account_id&limit=100&access_token={TOKEN}").json()
for acc in resp.get('data', []):
    if "univ" in acc['name'].lower() or "admit" in acc['name'].lower():
        print(f"Name: {acc['name']}, ID: {acc['account_id']}")
