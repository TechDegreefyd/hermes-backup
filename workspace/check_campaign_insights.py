import requests
TOKEN = ""
ACCOUNT_ID = "1798418091554447"
DATE = "2026-05-04"

# Get active campaigns
url_campaigns = f"https://graph.facebook.com/v19.0/act_{ACCOUNT_ID}/campaigns"
params = {'access_token': TOKEN, 'fields': 'id,name', 'effective_status': '["ACTIVE"]'}
campaigns = requests.get(url_campaigns, params=params).json().get('data', [])

for c in campaigns:
    url_insights = f"https://graph.facebook.com/v19.0/{c['id']}/insights"
    params_ins = {
        'access_token': TOKEN,
        'time_range': f'{{"since":"{DATE}","until":"{DATE}"}}',
        'fields': 'spend,account_name,campaign_name'
    }
    resp = requests.get(url_insights, params_ins).json()
    print(f"Campaign: {c['name']}, Insights: {resp}")
