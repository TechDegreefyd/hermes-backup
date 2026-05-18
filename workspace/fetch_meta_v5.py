import requests
import json
import csv
import sys
import argparse
import re
from datetime import datetime, timedelta

def get_token_from_script():
    try:
        with open('fetch_meta_v3.py', 'r') as f:
            content = f.read()
            # The token in the file was truncated in the read_file output but I can extract it properly if I read carefully.
            # Actually, I'll just use the full string if I can get it.
            match = re.search(r'ACCESS_TOKEN\s*=\s*"(.*?)"', content)
            if match:
                return match.group(1)
    except:
        pass
    return None

def fetch_data(start_date, end_date, output_file):
    token = get_token_from_script()
    if not token:
        print("Could not retrieve token from fetch_meta_v3.py")
        return

    accounts = ["2276414612586714", "771369141855853", "1798418091554447"]
    
    def get_insights_for_date(account_id, date_str):
        url = f"https://graph.facebook.com/v19.0/act_{account_id}/insights"
        params = {
            'level': 'ad',
            'fields': 'account_name,campaign_name,ad_name,spend,actions,date_start',
            'time_range': json.dumps({'since': date_str, 'until': date_str}),
            'access_token': token,
            'limit': 1000
        }
        all_data = []
        resp = requests.get(url, params=params)
        response = resp.json()
        if 'error' in response:
            print(f"Error for {account_id} on {date_str}: {response['error'].get('message')}")
            return []
        
        data = response.get('data', [])
        for entry in data:
            actions = entry.get('actions', [])
            # Sum leads, onsite_web_lead, and pixel leads as per previous instructions
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
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    current = start
    while current <= end:
        d_str = current.strftime('%Y-%m-%d')
        for acc in accounts:
            print(f"Fetching {acc} for {d_str}...")
            full_results.extend(get_insights_for_date(acc, d_str))
        current += timedelta(days=1)

    if full_results:
        keys = full_results[0].keys()
        with open(output_file, 'w', newline='') as f:
            dict_writer = csv.DictWriter(f, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(full_results)
        print(f"Saved {len(full_results)} records to {output_file}.")
    else:
        print("No records found.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--start', required=True)
    parser.add_argument('--end', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    fetch_data(args.start, args.end, args.output)
