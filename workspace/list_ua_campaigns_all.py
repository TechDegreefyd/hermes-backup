import requests
TOKEN = ""
ACCOUNT_ID = "1798418091554447"
url = f"https://graph.facebook.com/v19.0/act_{ACCOUNT_ID}/campaigns"
params = {'access_token': TOKEN, 'fields': 'name', 'limit': 200}
resp = requests.get(url, params=params).json()
for c in resp.get('data', []):
    print(c['name'])
