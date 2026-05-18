import requests
import csv
import sys

TOKEN = ""
ACCOUNT_ID = "1798418091554447"

def get_insights(date):
    url = f"https://graph.facebook.com/v19.0/act_{ACCOUNT_ID}/insights"
    params = {
        'access_token': TOKEN,
        'time_range': f'{{"since":"{date}","until":"{date}"}}',
        'level': 'ad',
        'fields': 'account_name,campaign_name,ad_name,spend,actions',
        'limit': 500
    }
    resp = requests.get(url, params=params).json()
    if 'error' in resp:
        print(f"Error: {resp['error']['message']}", file=sys.stderr)
        return []
    
    results = []
    for entry in resp.get('data', []):
        spend = float(entry.get('spend', 0))
        actions = entry.get('actions', [])
        leads = sum(int(a['value']) for a in actions if a['action_type'] in ['lead', 'onsite_web_lead', 'offsite_conversion.fb_pixel_lead'])
        results.append({
            'Account': entry['account_name'],
            'Date': date,
            'Campaign': entry['campaign_name'],
            'Ad Name': entry['ad_name'],
            'Spends': spend,
            'Pannel_Lead': leads
        })
    return results

data = get_insights("2026-05-04")
with open('university_admit_may4.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['Account', 'Date', 'Campaign', 'Ad Name', 'Spends', 'Pannel_Lead'])
    writer.writeheader()
    writer.writerows(data)

print(f"Fetched {len(data)} records for University Admit on May 4th.")
