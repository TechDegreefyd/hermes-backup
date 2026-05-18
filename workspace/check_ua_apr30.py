import requests
TOKEN = ""
ACCOUNT_ID = "1798418091554447"

url = f"https://graph.facebook.com/v19.0/act_{ACCOUNT_ID}/insights"
params = {
    'access_token': TOKEN,
    'time_range': '{"since":"2026-04-20","until":"2026-04-30"}',
    'level': 'account',
    'fields': 'spend,date_start',
    'time_increment': 1
}
resp = requests.get(url, params=params).json()
print(resp)
