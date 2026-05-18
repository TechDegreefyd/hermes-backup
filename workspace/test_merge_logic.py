import json, pandas as pd, numpy as np

# Load CAC
cac_raw = json.load(open('/workspace/cac_raw.json'))
df_cac = pd.DataFrame(cac_raw[2:], columns=[str(c).strip() for c in cac_raw[1]])

# Ensure numeric types for existing CAC
for c in ['Spends', 'Pannel_Lead', 'Lead_LMS', 'FFH', 'Adm', 'Invoicing_Var']:
    df_cac[c] = pd.to_numeric(df_cac[c].replace(['', '-', 'N/A'], '0'), errors='coerce').fillna(0)

df_cac['Date_Parsed'] = pd.to_datetime(df_cac['Date'], errors='coerce')
df_cac = df_cac.dropna(subset=['Date_Parsed'])

# Load FFH
ffh_raw = json.load(open('/workspace/ffh_full.json'))
df_ffh = pd.DataFrame(ffh_raw[1:], columns=[str(c).strip() for c in ffh_raw[0]])
df_ffh['Lead Date Parsed'] = pd.to_datetime(df_ffh['Lead Date'], format='%d/%b/%Y', errors='coerce')
df_ffh = df_ffh.dropna(subset=['Lead Date Parsed'])

# Zero out old values to replace them entirely!
df_cac['FFH'] = 0.0
df_cac['Adm'] = 0.0
df_cac['Invoicing_Var'] = 0.0

df_ffh['Adm_Count'] = df_ffh['Admission Date'].apply(lambda x: 1 if str(x).strip() != '' else 0)
df_ffh['Inv_Value'] = pd.to_numeric(df_ffh['Invoicing Variable'].replace(['', '-', 'N/A', ' '], '0'), errors='coerce').fillna(0)

ffh_grouped = df_ffh.groupby(['Lead Date Parsed', 'Campaign Name']).agg(
    FFH_Count=('Lead Date', 'count'),
    Adm_Count=('Adm_Count', 'sum'),
    Inv_Value=('Inv_Value', 'sum')
).reset_index()

unmatched = 0
matched = 0
appended = 0

# To inherit Platform and Account for appending
campaign_map = {}
for _, r in df_cac.iterrows():
    ad = str(r['Ad Name']).strip()
    cmp = str(r['Campaign']).strip()
    if ad: campaign_map[ad] = {'Platform': r['Platform'], 'Account': r['Account'], 'Campaign': cmp, 'Ad Name': ad}
    if cmp: campaign_map[cmp] = {'Platform': r['Platform'], 'Account': r['Account'], 'Campaign': cmp, 'Ad Name': ''}

new_rows = []

for _, r in ffh_grouped.iterrows():
    date = r['Lead Date Parsed']
    camp_name = str(r['Campaign Name']).strip()
    
    # Try to find a match in CAC on Date AND (Ad Name OR Campaign)
    mask1 = df_cac['Date_Parsed'] == date
    mask2 = (df_cac['Ad Name'] == camp_name) | (df_cac['Campaign'] == camp_name)
    intersect = mask1[mask1].index.intersection(mask2[mask2].index)
    matches = df_cac.loc[intersect]
    
    if len(matches) > 0:
        # Add to the first match
        idx = matches.index[0]
        df_cac.at[idx, 'FFH'] += r['FFH_Count']
        df_cac.at[idx, 'Adm'] += r['Adm_Count']
        df_cac.at[idx, 'Invoicing_Var'] += r['Inv_Value']
        matched += 1
    else:
        # We must append a new row
        if camp_name in campaign_map:
            cmap = campaign_map[camp_name]
            new_rows.append({
                'Platform': cmap['Platform'],
                'Account': cmap['Account'],
                'Campaign': cmap['Campaign'],
                'Ad Name': camp_name,
                'Date': date.strftime('%Y-%m-%d'),
                'Date_Parsed': date,
                'Spends': 0, 'Pannel_Lead': 0, 'Lead_LMS': 0,
                'FFH': float(r['FFH_Count']),
                'Adm': float(r['Adm_Count']),
                'Invoicing_Var': float(r['Inv_Value'])
            })
            appended += 1
        else:
            # Utterly unmatched, assign to Unknown
            new_rows.append({
                'Platform': 'Unknown',
                'Account': 'Unknown',
                'Campaign': camp_name,
                'Ad Name': camp_name,
                'Date': date.strftime('%Y-%m-%d'),
                'Date_Parsed': date,
                'Spends': 0, 'Pannel_Lead': 0, 'Lead_LMS': 0,
                'FFH': float(r['FFH_Count']),
                'Adm': float(r['Adm_Count']),
                'Invoicing_Var': float(r['Inv_Value'])
            })
            unmatched += 1

if new_rows:
    df_cac = pd.concat([df_cac, pd.DataFrame(new_rows)], ignore_index=True)

print(f"Matched: {matched}, Appended: {appended}, Unmatched/Unknown: {unmatched}")
print("Total FFH in new CAC:", df_cac['FFH'].sum())
print("Total Adm in new CAC:", df_cac['Adm'].sum())
print("Total Inv in new CAC:", df_cac['Invoicing_Var'].sum())

