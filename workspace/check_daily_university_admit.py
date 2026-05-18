import requests
TOKEN = ""
ACCOUNT_ID = "1798418091554447"

dates = ["2026-05-02", "2026-05-03", "2026-05-04", "2026-05-05", "2026-05-06"]

for d in dates:
    url = f"https://graph.facebook.com/v19.0/act_{ACCOUNT_ID}/insights"
    params = {
        'access_token': TOKEN,
        'time_range': f'{{"since":"{d}","until":"{d}"}}',
        'level': 'account',
        'fields': 'spend'
    }
    resp = requests.get(url, params=params).json()
    print(f"Date: {d}, Response: {resp}")
