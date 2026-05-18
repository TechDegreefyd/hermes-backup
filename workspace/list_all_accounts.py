import requests
TOKEN = ""
resp = requests.get(f"https://graph.facebook.com/v19.0/me/adaccounts?fields=name,account_id&access_token={TOKEN}").json()
for acc in resp.get('data', []):
    print(f"Name: {acc['name']}, ID: {acc['account_id']}")
