import requests
TOKEN = ""

# Check businesses
biz_resp = requests.get(f"https://graph.facebook.com/v19.0/me/businesses?access_token={TOKEN}").json()
print("Businesses:", biz_resp)

for biz in biz_resp.get('data', []):
    biz_id = biz['id']
    accs = requests.get(f"https://graph.facebook.com/v19.0/{biz_id}/adaccounts?fields=name,account_id&access_token={TOKEN}").json()
    print(f"Accounts for Biz {biz['name']}:", accs)
