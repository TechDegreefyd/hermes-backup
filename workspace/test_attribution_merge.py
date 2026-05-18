import json, pandas as pd, numpy as np
cac_raw = json.load(open('/workspace/cac_raw.json'))
df_cac = pd.DataFrame(cac_raw[2:], columns=[str(c).strip() for c in cac_raw[1]])
for c in ['Spends', 'Pannel_Lead', 'Lead_LMS', 'FFH', 'Adm', 'Invoicing_Var']:
    df_cac[c] = pd.to_numeric(df_cac[c].replace(['', '-', 'N/A'], '0'), errors='coerce').fillna(0)
df_cac['Date_Parsed'] = pd.to_datetime(df_cac['Date'], errors='coerce')
df_cac = df_cac.dropna(subset=['Date_Parsed'])

ffh_raw = json.load(open('/workspace/ffh_full.json'))
df_ffh = pd.DataFrame(ffh_raw[1:], columns=[str(c).strip() for c in ffh_raw[0]])

df_ffh['Form Date P'] = pd.to_datetime(df_ffh['Form Date'], format='%d/%b/%Y', errors='coerce')
df_ffh['Adm Date P'] = pd.to_datetime(df_ffh['Admission Date'], format='%d/%b/%Y', errors='coerce')

df_cac['FFH'] = 0.0
df_cac['Adm'] = 0.0
df_cac['Invoicing_Var'] = 0.0
df_ffh['Inv_Value'] = pd.to_numeric(df_ffh['Invoicing Variable'].replace(['', '-', 'N/A', ' '], '0'), errors='coerce').fillna(0)

ffh_forms = df_ffh.dropna(subset=['Form Date P']).groupby(['Form Date P', 'Campaign Name']).agg(FFH_Count=('Form Date', 'count')).reset_index()
ffh_adms = df_ffh.dropna(subset=['Adm Date P']).groupby(['Adm Date P', 'Campaign Name']).agg(Adm_Count=('Admission Date', 'count'), Inv_Value=('Inv_Value', 'sum')).reset_index()

campaign_map = {}
for _, r in df_cac.iterrows():
    ad = str(r.get('Ad Name', '')).strip()
    cmp = str(r.get('Campaign', '')).strip()
    if ad: campaign_map[ad] = {'Platform': r.get('Platform', 'Unknown'), 'Account': r.get('Account', 'Unknown'), 'Campaign': cmp, 'Ad Name': ad}
    if cmp: campaign_map[cmp] = {'Platform': r.get('Platform', 'Unknown'), 'Account': r.get('Account', 'Unknown'), 'Campaign': cmp, 'Ad Name': ''}

new_rows = []
for _, r in ffh_forms.iterrows():
    date = r['Form Date P']
    camp_name = str(r['Campaign Name']).strip()
    mask1 = df_cac['Date_Parsed'] == date
    mask2 = (df_cac['Ad Name'] == camp_name) | (df_cac['Campaign'] == camp_name)
    intersect = mask1[mask1].index.intersection(mask2[mask2].index)
    matches = df_cac.loc[intersect]
    if len(matches) > 0: df_cac.at[matches.index[0], 'FFH'] += r['FFH_Count']
    else:
        cmap = campaign_map.get(camp_name, {'Platform': 'Unknown', 'Account': 'Unknown', 'Campaign': camp_name, 'Ad Name': camp_name})
        new_rows.append({'Platform': cmap['Platform'], 'Account': cmap['Account'], 'Campaign': cmap['Campaign'], 'Ad Name': cmap.get('Ad Name', camp_name), 'Date': date.strftime('%Y-%m-%d'), 'Date_Parsed': date, 'Spends': 0.0, 'Pannel_Lead': 0.0, 'Lead_LMS': 0.0, 'FFH': float(r['FFH_Count']), 'Adm': 0.0, 'Invoicing_Var': 0.0})

if new_rows: df_cac = pd.concat([df_cac, pd.DataFrame(new_rows)], ignore_index=True)
new_rows = []

for _, r in ffh_adms.iterrows():
    date = r['Adm Date P']
    camp_name = str(r['Campaign Name']).strip()
    mask1 = df_cac['Date_Parsed'] == date
    mask2 = (df_cac['Ad Name'] == camp_name) | (df_cac['Campaign'] == camp_name)
    intersect = mask1[mask1].index.intersection(mask2[mask2].index)
    matches = df_cac.loc[intersect]
    if len(matches) > 0:
        df_cac.at[matches.index[0], 'Adm'] += r['Adm_Count']
        df_cac.at[matches.index[0], 'Invoicing_Var'] += r['Inv_Value']
    else:
        cmap = campaign_map.get(camp_name, {'Platform': 'Unknown', 'Account': 'Unknown', 'Campaign': camp_name, 'Ad Name': camp_name})
        new_rows.append({'Platform': cmap['Platform'], 'Account': cmap['Account'], 'Campaign': cmap['Campaign'], 'Ad Name': cmap.get('Ad Name', camp_name), 'Date': date.strftime('%Y-%m-%d'), 'Date_Parsed': date, 'Spends': 0.0, 'Pannel_Lead': 0.0, 'Lead_LMS': 0.0, 'FFH': 0.0, 'Adm': float(r['Adm_Count']), 'Invoicing_Var': float(r['Inv_Value'])})

if new_rows: df_cac = pd.concat([df_cac, pd.DataFrame(new_rows)], ignore_index=True)

may1 = df_cac[df_cac['Date_Parsed'].dt.month == 5]
today = pd.to_datetime('2026-05-04')
may = may1[may1['Date_Parsed'] <= today]
print("May Adm MTD:", may['Adm'].sum())
print("May Inv MTD:", may['Invoicing_Var'].sum())
