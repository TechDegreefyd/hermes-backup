import requests
import json

TOKEN = ""
ACCOUNT_ID = "1798418091554447"

url = f"https://graph.facebook.com/v19.0/act_{ACCOUNT_ID}/insights"
params = {
    'access_token': TOKEN,
    'date_preset': 'last_30d',
    'time_increment': 1,
    'level': 'account',
    'fields': 'spend,date_start'
}
resp = requests.get(url, params=params).json()
for day in resp.get('data', []):
    print(f"Date: {day['date_start']}, Spend: {day['spend']}")
