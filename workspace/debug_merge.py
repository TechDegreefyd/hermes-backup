import json, pandas as pd

cac_raw = json.load(open('/workspace/cac_raw.json'))
df_full = pd.DataFrame(cac_raw[2:], columns=[str(c).strip() for c in cac_raw[1]])
df_full['Date_Parsed'] = pd.to_datetime(df_full['Date'], errors='coerce')
df_full = df_full.dropna(subset=['Date_Parsed'])
today = df_full['Date_Parsed'].max()
print('Today:', today)

ffh_raw = json.load(open('/workspace/ffh_raw.json'))
df_ffh = pd.DataFrame(ffh_raw[1:], columns=[str(c).strip() for c in ffh_raw[0]])
df_full['FFH'] = 0.0
df_full['Adm'] = 0.0
df_full['Invoicing_Var'] = 0.0

df_ffh['Form Date Parsed'] = pd.to_datetime(df_ffh['Form Date'], format='%d/%b/%Y', errors='coerce')
df_ffh['Admission Date Parsed'] = pd.to_datetime(df_ffh['Admission Date'], format='%d/%b/%Y', errors='coerce')
df_ffh['Inv_Value'] = pd.to_numeric(df_ffh['Invoicing Variable'].replace(['', '-', 'N/A', ' '], '0'), errors='coerce').fillna(0)

# Group FFH by Form Date
ffh_counts = df_ffh.dropna(subset=['Form Date Parsed']).groupby(['Form Date Parsed', 'Campaign Name']).size().reset_index(name='FFH_Count')

# Group Adm and Inv by Admission Date
adm_counts = df_ffh.dropna(subset=['Admission Date Parsed']).groupby(['Admission Date Parsed', 'Campaign Name']).agg(
    Adm_Count=('Admission Date Parsed', 'count'),
    Inv_Value=('Inv_Value', 'sum')
).reset_index()

metrics_map = {}

for _, r in ffh_counts.iterrows():
    k = (r['Form Date Parsed'], str(r['Campaign Name']).strip())
    if k not in metrics_map: metrics_map[k] = {'FFH': 0.0, 'Adm': 0.0, 'Inv': 0.0}
    metrics_map[k]['FFH'] += float(r['FFH_Count'])

for _, r in adm_counts.iterrows():
    k = (r['Admission Date Parsed'], str(r['Campaign Name']).strip())
    if k not in metrics_map: metrics_map[k] = {'FFH': 0.0, 'Adm': 0.0, 'Inv': 0.0}
    metrics_map[k]['Adm'] += float(r['Adm_Count'])
    metrics_map[k]['Inv'] += float(r['Inv_Value'])

campaign_map = {}
for _, r in df_full.iterrows():
    ad = str(r.get('Ad Name', '')).strip()
    cmp = str(r.get('Campaign', '')).strip()
    if ad: campaign_map[ad] = {'Platform': r.get('Platform', 'Unknown'), 'Account': r.get('Account', 'Unknown'), 'Campaign': cmp, 'Ad Name': ad}
    if cmp: campaign_map[cmp] = {'Platform': r.get('Platform', 'Unknown'), 'Account': r.get('Account', 'Unknown'), 'Campaign': cmp, 'Ad Name': ''}

new_rows = []
for k, v in metrics_map.items():
    date = k[0]
    camp_name = k[1]
    
    mask1 = df_full['Date_Parsed'] == date
    mask2 = (df_full.get('Ad Name', '') == camp_name) | (df_full.get('Campaign', '') == camp_name)
    intersect = mask1[mask1].index.intersection(mask2[mask2].index)
    matches = df_full.loc[intersect]
    
    if len(matches) > 0:
        idx = matches.index[0]
        df_full.at[idx, 'FFH'] += v['FFH']
        df_full.at[idx, 'Adm'] += v['Adm']
        df_full.at[idx, 'Invoicing_Var'] += v['Inv']
    else:
        if camp_name in campaign_map:
            cmap = campaign_map[camp_name]
            new_rows.append({
                'Platform': cmap['Platform'], 'Account': cmap['Account'], 'Campaign': cmap['Campaign'], 'Ad Name': camp_name,
                'Date': date.strftime('%Y-%m-%d'), 'Date_Parsed': date, 'Spends': 0.0, 'Pannel_Lead': 0.0, 'Lead_LMS': 0.0,
                'FFH': float(v['FFH']), 'Adm': float(v['Adm']), 'Invoicing_Var': float(v['Inv'])
            })
        else:
            new_rows.append({
                'Platform': 'Unknown', 'Account': 'Unknown', 'Campaign': camp_name, 'Ad Name': camp_name,
                'Date': date.strftime('%Y-%m-%d'), 'Date_Parsed': date, 'Spends': 0.0, 'Pannel_Lead': 0.0, 'Lead_LMS': 0.0,
                'FFH': float(v['FFH']), 'Adm': float(v['Adm']), 'Invoicing_Var': float(v['Inv'])
            })

if new_rows:
    df_full = pd.concat([df_full, pd.DataFrame(new_rows)], ignore_index=True)

df_full = df_full[df_full['Date_Parsed'] <= today]

may4_df = df_full[df_full['Date_Parsed'] == today]
print("\n--- MAY 4 TOTALS AFTER MERGE ---")
print("Adm:", may4_df['Adm'].sum())
print("Inv:", may4_df['Invoicing_Var'].sum())
print("FFH:", may4_df['FFH'].sum())

print("\nMay 4th rows with Adm > 0:")
print(may4_df[may4_df['Adm'] > 0][['Campaign', 'Ad Name', 'Adm', 'Invoicing_Var']])

