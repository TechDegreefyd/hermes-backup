import requests
import pandas as pd

TOKEN = ""
ACCOUNTS = ["act_2276414612586714", "act_771369141855853", "act_943943398169185"]
DATE = "2026-05-03"

all_data = []
fields = "account_name,campaign_name,ad_name,spend,actions"

for account in ACCOUNTS:
    url = f"https://graph.facebook.com/v19.0/{account}/insights"
    params = {
        "access_token": TOKEN,
        "time_range": f"{{\"since\":\"{DATE}\",\"until\":\"{DATE}\"}}",
        "level": "ad",
        "fields": fields
    }
    
    resp = requests.get(url, params=params).json()
    data = resp.get("data", [])
    
    for entry in data:
        panel_leads = 0
        if "actions" in entry:
            for action in entry["actions"]:
                if action["action_type"] in ["lead", "onsite_web_lead", "offsite_conversion.fb_pixel_lead"]:
                    panel_leads += int(action["value"])
        
        all_data.append({
            "Account": entry["account_name"],
            "Date": DATE,
            "Campaign": entry["campaign_name"],
            "Ad Name": entry["ad_name"],
            "Spends": float(entry["spend"]),
            "Panel Leads": panel_leads
        })

df = pd.DataFrame(all_data)
df.to_csv("meta_may3_raw.csv", index=False)
print(f"Fetched {len(df)} ads for May 3.")
