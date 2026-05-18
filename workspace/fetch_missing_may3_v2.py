import requests
import pandas as pd

TOKEN = ""
ACCOUNT = "act_943943398169185" # University_Admit_01
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
print(resp)
