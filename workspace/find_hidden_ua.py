import requests
TOKEN = ""
# Fetch all accounts including those that might be deleted or disabled
url = f"https://graph.facebook.com/v19.0/me/adaccounts"
params = {
    'fields': 'name,account_id,id,account_status',
    'access_token': TOKEN,
    'limit': 1000
}
resp = requests.get(url, params=params).json()
for acc in resp.get('data', []):
    print(f"Name: {acc['name']}, ID: {acc['account_id']}, Status: {acc['account_status']}")
