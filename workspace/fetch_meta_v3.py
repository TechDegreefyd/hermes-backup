import requests
import json
import csv
from datetime import datetime, timedelta

ACCESS_TOKEN = ""
ACCOUNTS = ["2276414612586714", "771369141855853", "1798418091554447"]
DATES = ["2026-04-28", "2026-04-29", "2026-04-30", "2026-05-01", "2026-05-02", "2026-05-03", "2026-05-04", "2026-05-05", "2026-05-06"]

def get_insights_for_date(account_id, date_str):
    url = f"https://graph.facebook.com/v19.0/act_{account_id}/insights"
    params = {
        'level': 'ad',
        'fields': 'account_name,campaign_name,ad_name,spend,actions,date_start',
        'time_range': json.dumps({'since': date_str, 'until': date_str}),
        'access_token': ACCESS_TOKEN,
        'limit': 1000
    }
    all_data = []
    resp = requests.get(url, params=params)
    response = resp.json()
    if 'error' in response:
        return []
    
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
    return all_data

full_results = []
for acc in ACCOUNTS:
    for d in DATES:
        print(f"Fetching {acc} for {d}...")
        full_results.extend(get_insights_for_date(acc, d))

if full_results:
    keys = full_results[0].keys()
    with open('meta_insights_all_dates.csv', 'w', newline='') as f:
        dict_writer = csv.DictWriter(f, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(full_results)
    print(f"Saved {len(full_results)} records.")
