import requests
TOKEN = ""
ACCOUNT_ID = "1798418091554447"
url = f"https://graph.facebook.com/v19.0/act_{ACCOUNT_ID}/insights"
params = {
    'access_token': TOKEN,
    'date_preset': 'last_7d',
    'level': 'ad',
    'fields': 'date_start,spend,ad_name',
    'limit': 50
}
resp = requests.get(url, params=params).json()
print(resp)
