import json, pandas as pd, numpy as np

# Load CAC
cac_raw = json.load(open('/workspace/cac_raw.json'))
df_cac = pd.DataFrame(cac_raw[2:], columns=[str(c).strip() for c in cac_raw[1]])
for c in ['Spends', 'Pannel_Lead', 'Lead_LMS', 'FFH', 'Adm', 'Invoicing_Var']:
    df_cac[c] = pd.to_numeric(df_cac[c].replace(['', '-', 'N/A'], '0'), errors='coerce').fillna(0)
df_cac['Date_Parsed'] = pd.to_datetime(df_cac['Date'], errors='coerce')
df_cac = df_cac.dropna(subset=['Date_Parsed'])

# Zero out old values
df_cac['FFH'] = 0.0
df_cac['Adm'] = 0.0
df_cac['Invoicing_Var'] = 0.0

# Load FFH
ffh_raw = json.load(open('/workspace/ffh_full.json'))
df_ffh = pd.DataFrame(ffh_raw[1:], columns=[str(c).strip() for c in ffh_raw[0]])

# We will create a mapping of Date -> Campaign -> Metrics
# FFH is by Form Date
df_ffh['Form Date Parsed'] = pd.to_datetime(df_ffh['Form Date'], format='%d/%b/%Y', errors='coerce')
# Adm and Inv are by Admission Date
df_ffh['Admission Date Parsed'] = pd.to_datetime(df_ffh['Admission Date'], format='%d/%b/%Y', errors='coerce')

df_ffh['Inv_Value'] = pd.to_numeric(df_ffh['Invoicing Variable'].replace(['', '-', 'N/A', ' '], '0'), errors='coerce').fillna(0)

# Group FFH by Form Date
ffh_counts = df_ffh.dropna(subset=['Form Date Parsed']).groupby(['Form Date Parsed', 'Campaign Name']).size().reset_index(name='FFH_Count')

# Group Adm by Admission Date
adm_counts = df_ffh.dropna(subset=['Admission Date Parsed']).groupby(['Admission Date Parsed', 'Campaign Name']).agg(
    Adm_Count=('Admission Date Parsed', 'count'),
    Inv_Value=('Inv_Value', 'sum')
).reset_index()

# Build a dictionary to combine them: Key: (Date, Campaign Name) -> {'FFH': x, 'Adm': y, 'Inv': z}
metrics_map = {}

for _, r in ffh_counts.iterrows():
    k = (r['Form Date Parsed'], str(r['Campaign Name']).strip())
    if k not in metrics_map: metrics_map[k] = {'FFH': 0.0, 'Adm': 0.0, 'Inv': 0.0}
    metrics_map[k]['FFH'] += r['FFH_Count']

for _, r in adm_counts.iterrows():
    k = (r['Admission Date Parsed'], str(r['Campaign Name']).strip())
    if k not in metrics_map: metrics_map[k] = {'FFH': 0.0, 'Adm': 0.0, 'Inv': 0.0}
    metrics_map[k]['Adm'] += r['Adm_Count']
    metrics_map[k]['Inv'] += r['Inv_Value']

# Map to Platform and Account
campaign_map = {}
for _, r in df_cac.iterrows():
    ad = str(r.get('Ad Name', '')).strip()
    cmp = str(r.get('Campaign', '')).strip()
    if ad: campaign_map[ad] = {'Platform': r.get('Platform', 'Unknown'), 'Account': r.get('Account', 'Unknown'), 'Campaign': cmp, 'Ad Name': ad}
    if cmp: campaign_map[cmp] = {'Platform': r.get('Platform', 'Unknown'), 'Account': r.get('Account', 'Unknown'), 'Campaign': cmp, 'Ad Name': ''}

new_rows = []

for k, v in metrics_map.items():
    date = k[0]
    camp_name = k[1]
    
    mask1 = df_cac['Date_Parsed'] == date
    mask2 = (df_cac.get('Ad Name', '') == camp_name) | (df_cac.get('Campaign', '') == camp_name)
    intersect = mask1[mask1].index.intersection(mask2[mask2].index)
    matches = df_cac.loc[intersect]
    
    if len(matches) > 0:
        idx = matches.index[0]
        df_cac.at[idx, 'FFH'] += v['FFH']
        df_cac.at[idx, 'Adm'] += v['Adm']
        df_cac.at[idx, 'Invoicing_Var'] += v['Inv']
    else:
        if camp_name in campaign_map:
            cmap = campaign_map[camp_name]
            new_rows.append({
                'Platform': cmap['Platform'], 'Account': cmap['Account'], 'Campaign': cmap['Campaign'], 'Ad Name': camp_name,
                'Date': date.strftime('%Y-%m-%d'), 'Date_Parsed': date, 'Spends': 0.0, 'Pannel_Lead': 0.0, 'Lead_LMS': 0.0,
                'FFH': v['FFH'], 'Adm': v['Adm'], 'Invoicing_Var': v['Inv']
            })
        else:
            new_rows.append({
                'Platform': 'Unknown', 'Account': 'Unknown', 'Campaign': camp_name, 'Ad Name': camp_name,
                'Date': date.strftime('%Y-%m-%d'), 'Date_Parsed': date, 'Spends': 0.0, 'Pannel_Lead': 0.0, 'Lead_LMS': 0.0,
                'FFH': v['FFH'], 'Adm': v['Adm'], 'Invoicing_Var': v['Inv']
            })

if new_rows:
    df_cac = pd.concat([df_cac, pd.DataFrame(new_rows)], ignore_index=True)

# Let's check May MTD totals!
may_mask = df_cac['Date_Parsed'] >= pd.to_datetime('2026-05-01')
df_may = df_cac[may_mask]

print("May FFH:", df_may['FFH'].sum())
print("May Adm:", df_may['Adm'].sum())
print("May Invoicing_Var:", df_may['Invoicing_Var'].sum())

# Let's check exactly May 4 totals!
may4_mask = df_cac['Date_Parsed'] == pd.to_datetime('2026-05-04')
df_may4 = df_cac[may4_mask]

print("May 4 FFH:", df_may4['FFH'].sum())
print("May 4 Adm:", df_may4['Adm'].sum())
print("May 4 Invoicing_Var:", df_may4['Invoicing_Var'].sum())

