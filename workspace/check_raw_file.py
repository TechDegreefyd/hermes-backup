import json

with open('/workspace/ffh_raw.json') as f:
    ffh_raw = json.load(f)

print(len(ffh_raw), "rows in ffh_raw.json")

with open('/workspace/ffh_full.json') as f:
    ffh_full = json.load(f)

print(len(ffh_full), "rows in ffh_full.json")
