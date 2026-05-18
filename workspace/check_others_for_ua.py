import requests
TOKEN = ""
ACCOUNTS = ["2276414612586714", "771369141855853"]

for acc_id in ACCOUNTS:
    url = f"https://graph.facebook.com/v19.0/act_{acc_id}/insights"
    params = {
        'access_token': TOKEN,
        'time_range': '{"since":"2026-05-04","until":"2026-05-04"}',
        'level': 'ad',
        'fields': 'account_name,campaign_name,ad_name,spend',
        'limit': 1000
    }
    resp = requests.get(url, params=params).json()
    print(f"Account {acc_id} has {len(resp.get('data', []))} records.")
    for entry in resp.get('data', []):
        if "University" in entry['campaign_name'] or "UA" in entry['campaign_name']:
            print(f"  Found UA in {acc_id}: {entry['campaign_name']}")
