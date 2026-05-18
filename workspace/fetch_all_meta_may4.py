import requests
import json
import csv

TOKEN = ""
ACCOUNTS = ["2276414612586714", "771369141855853", "943943398169185"]
DATE = "2026-05-04"

def get_insights(acc_id):
    url = f"https://graph.facebook.com/v19.0/act_{acc_id}/insights"
    params = {
        'access_token': TOKEN,
        'time_range': json.dumps({'since': DATE, 'until': DATE}),
        'level': 'ad',
        'fields': 'account_name,campaign_name,ad_name,spend,actions',
        'limit': 1000
    }
    resp = requests.get(url, params=params).json()
    if 'error' in resp:
        print(f"Error for {acc_id}: {resp['error'].get('message')}")
        return []
    
    results = []
    for entry in resp.get('data', []):
        actions = entry.get('actions', [])
        # Sum panel leads, website leads, and pixel leads
        leads = sum(int(a['value']) for a in actions if a['action_type'] in ['lead', 'onsite_web_lead', 'offsite_conversion.fb_pixel_lead'])
        results.append({
            'Platform': 'Meta',
            'Account': entry.get('account_name'),
            'Date': DATE,
            'Campaign': entry.get('campaign_name'),
            'Ad Name': entry.get('ad_name'),
            'Spends': float(entry.get('spend', 0)),
            'Pannel_Lead': leads
        })
    return results

all_data = []
for acc in ACCOUNTS:
    all_data.extend(get_insights(acc))

with open('meta_may4_full_corrected.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['Platform', 'Account', 'Date', 'Campaign', 'Ad Name', 'Spends', 'Pannel_Lead'])
    writer.writeheader()
    writer.writerows(all_data)

print(f"Saved {len(all_data)} records to meta_may4_full_corrected.csv")
