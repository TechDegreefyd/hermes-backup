import json
import pandas as pd

with open('/workspace/cac_raw.json','r') as f: cac_raw = json.load(f)
df_cac = pd.DataFrame(cac_raw[2:], columns=[str(c).strip() for c in cac_raw[1]])
df_cac['Adm'] = pd.to_numeric(df_cac['Adm'].replace(['', '-', 'N/A'], '0'), errors='coerce').fillna(0)
cac_camps = set(df_cac[df_cac['Adm']>0]['Campaign'].unique())

with open('/workspace/ffh_full.json','r') as f: ffh_raw = json.load(f)
df_ffh = pd.DataFrame(ffh_raw[1:], columns=[str(c).strip() for c in ffh_raw[0]])
ffh_camps = set(df_ffh['Campaign Name'].unique())

print("Top 5 campaigns in CAC with Adm > 0:")
print(df_cac[df_cac['Adm']>0].groupby('Campaign')['Adm'].sum().sort_values(ascending=False).head(5))

print("\nTop 5 campaigns in FFH by count:")
print(df_ffh['Campaign Name'].value_counts().head(5))

