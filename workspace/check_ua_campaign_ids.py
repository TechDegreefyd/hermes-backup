import requests
TOKEN = ""
# Campaign IDs from previous output
IDS = ["120241654500420437", "120241590978930437", "120241509605400437", "120241508843940437", "120241447331950437", "120241445405940437", "120241426255500437"]

for cid in IDS:
    url = f"https://graph.facebook.com/v19.0/{cid}/insights"
    params = {
        'access_token': TOKEN,
        'time_range': '{"since":"2026-05-04","until":"2026-05-04"}',
        'fields': 'spend,campaign_name'
    }
    resp = requests.get(url, params=params).json()
    print(f"ID {cid}: {resp}")
