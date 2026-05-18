import requests
import json
import csv

ACCESS_TOKEN = ""
ACCOUNTS = ["2276414612586714", "771369141855853", "1798418091554447"]
START_DATE = "2026-04-28"
END_DATE = "2026-05-06"

def get_insights(account_id):
    url = f"https://graph.facebook.com/v19.0/act_{account_id}/insights"
    params = {
        'level': 'ad',
        'fields': 'account_name,campaign_name,ad_name,spend,actions,date_start',
        'time_range': json.dumps({'since': START_DATE, 'until': END_DATE}),
        'access_token': ACCESS_TOKEN,
        'limit': 1000
    }
    all_data = []
    while url:
        resp = requests.get(url, params=params)
        response = resp.json()
        if 'error' in response:
            break
        
        data = response.get('data', [])
        for entry in data:
            actions = entry.get('actions', [])
            leads = sum(int(a['value']) for a in actions if a['action_type'] in ['lead', 'onsite_web_lead', 'offsite_conversion.fb_pixel_lead'])
            
            all_data.append({
                'Platform': 'Meta',
                'Account': entry.get('account_name'),
                'Date': entry.get('date_start'),
                'Campaign': entry.get('campaign_name'),
                'Ad Name': entry.get('ad_name'),
                'Spends': float(entry.get('spend', 0)),
                'Pannel_Lead': leads
            })
            
        url = response.get('paging', {}).get('next')
        params = {}
        
    return all_data

full_results = []
for acc in ACCOUNTS:
    full_results.extend(get_insights(acc))

if full_results:
    keys = full_results[0].keys()
    with open('meta_insights_raw_v2.csv', 'w', newline='') as f:
        dict_writer = csv.DictWriter(f, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(full_results)
    print(f"Saved {len(full_results)} records.")
