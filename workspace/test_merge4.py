import json, pandas as pd

cac_raw = json.load(open('/workspace/cac_raw.json'))
df_cac = pd.DataFrame(cac_raw[2:], columns=[str(c).strip() for c in cac_raw[1]])
ffh_raw = json.load(open('/workspace/ffh_full.json'))
df_ffh = pd.DataFrame(ffh_raw[1:], columns=[str(c).strip() for c in ffh_raw[0]])

sample_ad = "Galgotias_Leads_2026_P_Ad_01"
print(df_cac[df_cac['Ad Name'] == sample_ad][['Date', 'Ad Name', 'Adm']])
print("----")
print(df_ffh[df_ffh['Campaign Name'] == sample_ad][['Lead Date', 'Form Date', 'Admission Date', 'Campaign Name']].head(5))

