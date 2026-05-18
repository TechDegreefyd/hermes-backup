import json
import pandas as pd
from datetime import datetime

with open('/workspace/cac_raw.json','r') as f: cac_raw = json.load(f)
df_cac = pd.DataFrame(cac_raw[2:], columns=[str(c).strip() for c in cac_raw[1]])
df_cac['Date_Parsed'] = pd.to_datetime(df_cac['Date'], errors='coerce')
df_cac['Adm'] = pd.to_numeric(df_cac['Adm'].replace(['', '-', 'N/A'], '0'), errors='coerce').fillna(0)
df_cac['Invoicing_Var'] = pd.to_numeric(df_cac['Invoicing_Var'].replace(['', '-', 'N/A'], '0'), errors='coerce').fillna(0)

with open('/workspace/ffh_raw.json','r') as f: ffh_raw = json.load(f)
df_ffh = pd.DataFrame(ffh_raw[1:], columns=[str(c).strip() for c in ffh_raw[0]])

# Let's find rows in cac where Adm > 0
cac_adms = df_cac[df_cac['Adm'] > 0]
print("Total Adm in CAC sheet:", cac_adms['Adm'].sum())

# Let's print one cac row with adm > 0
if not cac_adms.empty:
    sample = cac_adms.iloc[0]
    print(f"Sample CAC Adm: Date={sample['Date_Parsed']}, Campaign={sample['Campaign']}, Adm={sample['Adm']}")
    
    # Let's find this campaign in FFH
    ffh_match = df_ffh[df_ffh['Campaign Name'] == sample['Campaign']]
    print(f"Matches in FFH for {sample['Campaign']}:")
    for _, row in ffh_match.iterrows():
        print(f"  Lead Date: {row['Lead Date']}, Form Date: {row['Form Date']}, Adm Date: {row['Admission Date']}")

print("Campaigns in FFH:", df_ffh['Campaign Name'].unique())

