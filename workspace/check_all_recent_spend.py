import requests
TOKEN = ""
ACCOUNTS = ["2276414612586714", "771369141855853", "1798418091554447"]

for acc_id in ACCOUNTS:
    url = f"https://graph.facebook.com/v19.0/act_{acc_id}/insights"
    params = {
        'access_token': TOKEN,
        'date_preset': 'last_30d',
        'level': 'account',
        'fields': 'spend,account_name'
    }
    resp = requests.get(url, params=params).json()
    print(f"Account {acc_id}: {resp}")
