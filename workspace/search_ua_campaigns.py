import requests

TOKEN = ""
TARGET_CAMPAIGNS = ["F_UA01_{UG All Colleges V03.1}", "F_UA1_FEB_MBA_Aryan v1.4", "UA_MBA_Website_Leads V1"]

# Get all accounts
resp = requests.get(f"https://graph.facebook.com/v19.0/me/adaccounts?fields=name,account_id&access_token={TOKEN}").json()
accounts = resp.get('data', [])

for acc in accounts:
    acc_id = acc['account_id']
    print(f"Checking account: {acc['name']} ({acc_id})")
    url = f"https://graph.facebook.com/v19.0/act_{acc_id}/campaigns"
    params = {'access_token': TOKEN, 'fields': 'name', 'limit': 100}
    c_resp = requests.get(url, params=params).json()
    for c in c_resp.get('data', []):
        if any(target in c['name'] for target in TARGET_CAMPAIGNS):
            print(f"  FOUND {c['name']} in {acc['name']}")
