import requests
import pandas as pd

TOKEN = ""
ACCOUNTS = ["act_2276414612586714", "act_771369141855853", "act_943943398169185"]

all_mappings = []

for acc in ACCOUNTS:
    url = f"https://graph.facebook.com/v19.0/{acc}/campaigns"
    params = {"access_token": TOKEN, "fields": "id,name", "limit": 1000}
    try:
        r = requests.get(url, params=params)
        data = r.json().get('data', [])
        for c in data:
            all_mappings.append({"Campaign ID": str(c['id']), "Campaign Name": c['name']})
        
        # Also get Ads for better mapping
        url_ads = f"https://graph.facebook.com/v19.0/{acc}/ads"
        params_ads = {"access_token": TOKEN, "fields": "id,name,campaign{id,name}", "limit": 1000}
        r_ads = requests.get(url_ads, params=params_ads)
        ads_data = r_ads.json().get('data', [])
        for a in ads_data:
            all_mappings.append({"Campaign ID": str(a['id']), "Campaign Name": a['name']}) # Mapping Ad ID to Ad Name
    except Exception as e:
        print(f"Error fetching for {acc}: {e}")

df = pd.DataFrame(all_mappings).drop_duplicates()
df.to_csv("campaign_id_mapping.csv", index=False)
print(f"Saved {len(df)} ID-to-Name mappings.")
