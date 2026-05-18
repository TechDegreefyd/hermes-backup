import json, pandas as pd
with open('/workspace/cac_raw.json','r') as f: cac_raw = json.load(f)
df = pd.DataFrame(cac_raw[2:], columns=[str(c).strip() for c in cac_raw[1]])
print(df.columns)
print(df['Platform'].unique())
print(df['Account'].unique())
