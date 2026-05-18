import requests
import json

TOKEN = ""
ACCOUNT_ID = "1798418091554447"
DATE = "2026-05-04"

# Variant 1: time_range as dict
print("--- Variant 1 ---")
r1 = requests.get(f"https://graph.facebook.com/v19.0/act_{ACCOUNT_ID}/insights", params={
    'access_token': TOKEN,
    'time_range': json.dumps({'since': DATE, 'until': DATE}),
    'level': 'account',
    'fields': 'spend'
}).json()
print(r1)

# Variant 2: time_range as params
print("--- Variant 2 ---")
r2 = requests.get(f"https://graph.facebook.com/v19.0/act_{ACCOUNT_ID}/insights", params={
    'access_token': TOKEN,
    'time_range': '{"since":"2026-05-04","until":"2026-05-04"}',
    'level': 'account',
    'fields': 'spend'
}).json()
print(r2)

# Variant 3: Wider range to see if it catches anything
print("--- Variant 3 (May 1-6) ---")
r3 = requests.get(f"https://graph.facebook.com/v19.0/act_{ACCOUNT_ID}/insights", params={
    'access_token': TOKEN,
    'time_range': '{"since":"2026-05-01","until":"2026-05-06"}',
    'level': 'account',
    'fields': 'spend,date_start'
}).json()
print(r3)
