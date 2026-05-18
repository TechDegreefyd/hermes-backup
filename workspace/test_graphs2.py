import json, pandas as pd
with open('/workspace/cac_raw.json','r') as f: cac_raw = json.load(f)
df_full = pd.DataFrame(cac_raw[2:], columns=[str(c).strip() for c in cac_raw[1]])

mask = df_full['Account'].str.contains('DSA', case=False, na=False)
print("DSA in Account rows:", len(df_full[mask]))
mask = df_full['Account'].str.contains('Brand', case=False, na=False)
print("Brand in Account rows:", len(df_full[mask]))

