import pandas as pd
import numpy as np

# Load data
meta = pd.read_csv('meta_insights_all_dates.csv')
online_sheet = pd.read_csv('online_cac_sheet.csv', header=1)
regular_sheet = pd.read_csv('regular_cac_sheet.csv', header=1)
lms = pd.read_csv('lms_leads_all_dbs.csv')

# Pre-process Meta
meta['Date'] = pd.to_datetime(meta['Date']).dt.date
meta['Spends'] = pd.to_numeric(meta['Spends'], errors='coerce').fillna(0)
meta['Pannel_Lead'] = pd.to_numeric(meta['Pannel_Lead'], errors='coerce').fillna(0)

# Pre-process Sheets
def clean_sheet(df):
    df.columns = [c.strip() for c in df.columns]
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date
    spend_col = [c for c in df.columns if 'Spends' in c][0]
    df['Spends_Clean'] = df[spend_col].astype(str).str.replace('₹','').str.replace(',','').str.replace('-','0')
    df['Spends_Clean'] = pd.to_numeric(df['Spends_Clean'], errors='coerce').fillna(0)
    
    lead_col = 'Pannel_Lead' if 'Pannel_Lead' in df.columns else 'Lead_LMS'
    df['Pannel_Lead_Clean'] = pd.to_numeric(df[lead_col], errors='coerce').fillna(0)
    
    lms_col = 'Lead_LMS' if 'Lead_LMS' in df.columns else 'LMS Leads'
    if lms_col in df.columns:
        df['LMS_Leads_Clean'] = pd.to_numeric(df[lms_col], errors='coerce').fillna(0)
    else:
        df['LMS_Leads_Clean'] = 0
    return df

online_sheet = clean_sheet(online_sheet)
regular_sheet = clean_sheet(regular_sheet)

target_date = pd.to_datetime('2026-05-04').date()
m4 = meta[meta['Date'] == target_date].copy()
o4 = online_sheet[online_sheet['Date'] == target_date].copy()
r4 = regular_sheet[regular_sheet['Date'] == target_date].copy()
l4 = lms[pd.to_datetime(lms['created_date']).dt.date == target_date].copy()

s4 = pd.concat([o4, r4])

def get_lms_count(campaign_name):
    if not campaign_name or pd.isna(campaign_name): return 0
    # Search for campaign name in the LMS 'utm_campaign' column
    match = l4[l4['utm_campaign'].str.contains(str(campaign_name), case=False, na=False)]
    return match['lead_count'].sum() if not match.empty else 0

results = []
for _, row in m4.iterrows():
    ad_name = row['Ad Name']
    campaign = row['Campaign']
    meta_spend = row['Spends']
    meta_leads = row['Pannel_Lead']
    lms_leads = get_lms_count(campaign)
    
    # Matching logic: Date + Ad Name
    sheet_row = s4[s4['Ad Name'] == ad_name]
    
    if not sheet_row.empty:
        # Use first match
        s_row = sheet_row.iloc[0]
        sheet_spend = s_row['Spends_Clean']
        sheet_leads = s_row['Pannel_Lead_Clean']
        sheet_lms = s_row['LMS_Leads_Clean']
        
        # Determine status
        # Meta Spend vs Sheet Spend
        # Meta Panel vs Sheet Panel
        # Calc LMS vs Sheet LMS
        is_spend_match = abs(meta_spend - sheet_spend) < 5
        is_panel_match = meta_leads == sheet_leads
        is_lms_match = lms_leads == sheet_lms
        
        if is_spend_match and is_panel_match and is_lms_match:
            status = "MATCH"
        else:
            status = "DISCREPANCY"
    else:
        sheet_spend = 0
        sheet_leads = 0
        sheet_lms = 0
        status = "MISSING"
    
    results.append({
        "Account": row['Account'],
        "Campaign": campaign,
        "Ad Name": ad_name,
        "Meta Spend": round(meta_spend, 2),
        "Sheet Spend": round(sheet_spend, 2),
        "Meta Panel": int(meta_leads),
        "Sheet Panel": int(sheet_leads),
        "LMS (Actual)": int(lms_leads),
        "Sheet LMS": int(sheet_lms),
        "Status": status
    })

res_df = pd.DataFrame(results)
res_df = res_df.sort_values(['Account', 'Status'])
print(res_df.to_string(index=False))

print("\n--- Discrepancy Analysis ---")
disc = res_df[res_df['Status'] != 'MATCH']
for _, r in disc.iterrows():
    reasons = []
    if r['Status'] == 'MISSING':
        reasons.append("Row missing from sheet")
    else:
        if abs(r['Meta Spend'] - r['Sheet Spend']) >= 5:
            reasons.append(f"Spend mismatch (Meta: {r['Meta Spend']}, Sheet: {r['Sheet Spend']})")
        if r['Meta Panel'] != r['Sheet Panel']:
            reasons.append(f"Panel leads mismatch (Meta: {r['Meta Panel']}, Sheet: {r['Sheet Panel']})")
        if r['LMS (Actual)'] != r['Sheet LMS']:
            reasons.append(f"LMS leads mismatch (Actual: {r['LMS (Actual)']}, Sheet: {r['Sheet LMS']})")
    print(f"- {r['Ad Name']}: {', '.join(reasons)}")
