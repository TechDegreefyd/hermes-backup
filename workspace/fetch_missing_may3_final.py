import requests
import pandas as pd
from datetime import datetime

TOKEN = ""
ACCOUNT = "act_943943398169185"
DATE = "2026-05-03"

fields = "account_name,campaign_name,ad_name,spend,actions"
url = f"https://graph.facebook.com/v19.0/{ACCOUNT}/insights"
params = {
    "access_token": TOKEN,
    "time_range": f"{{\"since\":\"{DATE}\",\"until\":\"{DATE}\"}}",
    "level": "ad",
    "fields": fields
}

resp = requests.get(url, params=params).json()
all_data = []

if "data" in resp:
    for entry in resp["data"]:
        panel_leads = 0
        if "actions" in entry:
            for action in entry["actions"]:
                if action["action_type"] in ["lead", "onsite_web_lead", "offsite_conversion.fb_pixel_lead"]:
                    panel_leads += int(action["value"])
        
        all_data.append({
            "Platform": "Meta",
            "Platform Type": "Lead Gen",
            "Account": entry["account_name"],
            "Date": DATE,
            "Campaign": entry["campaign_name"],
            "Ad Name": entry["ad_name"],
            "Spends": float(entry["spend"]),
            "Pannel_Lead": panel_leads
        })

df = pd.DataFrame(all_data)
df.to_csv("university_admit_may3.csv", index=False)
print(f"Fetched {len(df)} ads for University_Admit_01 on May 3rd.")
