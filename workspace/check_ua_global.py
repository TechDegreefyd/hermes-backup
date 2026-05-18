import requests
TOKEN = ""
ACCOUNT_ID = "1798418091554447"

# Check if there's any spend at all in the last week
url = f"https://graph.facebook.com/v19.0/act_{ACCOUNT_ID}/insights"
params = {
    'access_token': TOKEN,
    'date_preset': 'last_week_mon_sun',
    'level': 'account',
    'fields': 'spend,date_start,date_stop'
}
resp = requests.get(url, params=params).json()
print("Last Week (Mon-Sun) Insights:", resp)

# Try 'yesterday' specifically relative to current session date (May 6)
url_yest = f"https://graph.facebook.com/v19.0/act_{ACCOUNT_ID}/insights"
params_yest = {
    'access_token': TOKEN,
    'date_preset': 'yesterday',
    'level': 'account',
    'fields': 'spend,date_start'
}
resp_yest = requests.get(url_yest, params_yest).json()
print("Yesterday Insights:", resp_yest)
