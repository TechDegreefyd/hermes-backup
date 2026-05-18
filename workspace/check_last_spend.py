import requests
TOKEN = ""
ACCOUNT_ID = "1798418091554447"

url = f"https://graph.facebook.com/v19.0/act_{ACCOUNT_ID}/insights"
params = {
    'access_token': TOKEN,
    'date_preset': 'maximum',
    'level': 'account',
    'fields': 'date_start,date_stop,spend',
    'limit': 1
}
resp = requests.get(url, params=params).json()
print("Max Insights:", resp)
