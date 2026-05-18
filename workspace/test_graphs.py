import json, pandas as pd
with open('/workspace/cac_raw.json','r') as f: cac_raw = json.load(f)
df_full = pd.DataFrame(cac_raw[2:], columns=[str(c).strip() for c in cac_raw[1]])

print("Platform values:", df_full['Platform'].unique())
mask = df_full['Platform'].str.contains('DSA', case=False, na=False)
print("DSA rows:", len(df_full[mask]))

mask2 = df_full['Platform'].str.contains('Brand', case=False, na=False)
print("Brand rows:", len(df_full[mask2]))

mask3 = df_full['Platform'].str.contains('Meta', case=False, na=False)
print("Meta rows:", len(df_full[mask3]))

