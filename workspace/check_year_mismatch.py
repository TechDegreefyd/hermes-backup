import requests
TOKEN = ""
ACCOUNT_ID = "1798418091554447"

url = f"https://graph.facebook.com/v19.0/act_{ACCOUNT_ID}/insights"
params = {
    'access_token': TOKEN,
    'time_range': '{"since":"2025-05-04","until":"2025-05-04"}',
    'level': 'account',
    'fields': 'spend'
}
resp = requests.get(url, params=params).json()
print("2025 Spend:", resp)
