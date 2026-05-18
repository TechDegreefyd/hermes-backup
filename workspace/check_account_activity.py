import requests
TOKEN = ""
ACCOUNT_ID = "1798418091554447"

# Check campaigns to see if any are active
url_campaigns = f"https://graph.facebook.com/v19.0/act_{ACCOUNT_ID}/campaigns"
params = {
    'access_token': TOKEN,
    'fields': 'name,status,effective_status',
    'limit': 50
}
resp = requests.get(url_campaigns, params=params).json()
print("Campaigns:", resp)

# Check insights for a wider range (last 30 days) to see if it's running at all
url_insights = f"https://graph.facebook.com/v19.0/act_{ACCOUNT_ID}/insights"
params_insights = {
    'access_token': TOKEN,
    'date_preset': 'last_30d',
    'level': 'account',
    'fields': 'date_start,date_stop,spend'
}
resp_insights = requests.get(url_insights, params_insights).json()
print("Insights (Last 30d):", resp_insights)
