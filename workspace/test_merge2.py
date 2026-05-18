import json
import pandas as pd

with open('/workspace/cac_raw.json','r') as f: cac_raw = json.load(f)
df_cac = pd.DataFrame(cac_raw[2:], columns=[str(c).strip() for c in cac_raw[1]])
df_cac['Date_Parsed'] = pd.to_datetime(df_cac['Date'], errors='coerce')
df_cac['Adm'] = pd.to_numeric(df_cac['Adm'].replace(['', '-', 'N/A'], '0'), errors='coerce').fillna(0)

with open('/workspace/ffh_full.json','r') as f: ffh_raw = json.load(f)
df_ffh = pd.DataFrame(ffh_raw[1:], columns=[str(c).strip() for c in ffh_raw[0]])

# Sample from CAC
sample = df_cac[df_cac['Adm'] > 0].iloc[0]
print(f"Sample CAC Adm: Date={sample['Date_Parsed']}, Campaign={sample['Campaign']}, Adm={sample['Adm']}")

ffh_match = df_ffh[df_ffh['Campaign Name'] == sample['Campaign']]
print(f"Matches in FFH for {sample['Campaign']}:")
for _, row in ffh_match.head(5).iterrows():
    print(f"  Lead Date: {row['Lead Date']}, Form Date: {row['Form Date']}, Adm Date: {row['Admission Date']}")

