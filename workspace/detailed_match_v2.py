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
    df['Spends'] = df['Spends'].astype(str).str.replace('₹','').str.replace(',','').str.replace('-','0')
    df['Spends'] = pd.to_numeric(df['Spends'], errors='coerce').fillna(0)
    df['Pannel_Lead'] = pd.to_numeric(df['Pannel_Lead'], errors='coerce').fillna(0)
    df['LMS_Leads'] = pd.to_numeric(df['LMS Leads'], errors='coerce').fillna(0)
    return df

online_sheet = clean_sheet(online_sheet)
regular_sheet = clean_sheet(regular_sheet)

# Filter for May 4
target_date = pd.to_datetime('2026-05-04').date()
m4 = meta[meta['Date'] == target_date].copy()
o4 = online_sheet[online_sheet['Date'] == target_date].copy()
r4 = regular_sheet[regular_sheet['Date'] == target_date].copy()
l4 = lms[pd.to_datetime(lms['created_date']).dt.date == target_date].copy()

# Consolidate sheets for matching
s4 = pd.concat([o4, r4])

# Helper to find LMS leads by Campaign
def get_lms_count(campaign_name):
    # Match campaign name exactly or partially
    match = l4[l4['utm_campaign'].str.contains(campaign_name, case=False, na=False)]
    return match['lead_count'].sum() if not match.empty else 0

results = []

for _, row in m4.iterrows():
    ad_name = row['Ad Name']
    campaign = row['Campaign Name']
    meta_spend = row['Spends']
    meta_leads = row['Pannel_Lead']
    lms_leads = get_lms_count(campaign)
    
    # Match in sheet
    sheet_row = s4[s4['Ad Name'] == ad_name]
    
    if not sheet_row.empty:
        sheet_spend = sheet_row['Spends'].sum()
        sheet_leads = sheet_row['Pannel_Lead'].sum()
        status = "MATCH" if (abs(meta_spend - sheet_spend) < 1 and meta_leads == sheet_leads) else "DISCREPANCY"
    else:
        sheet_spend = 0
        sheet_leads = 0
        status = "MISSING IN SHEET"
    
    results.append({
        "Account": row['Account Name'],
        "Campaign": campaign,
        "Ad Name": ad_name,
        "Meta Spend": meta_spend,
        "Sheet Spend": sheet_spend,
        "Meta Panel": meta_leads,
        "Sheet Panel": sheet_leads,
        "LMS Leads": lms_leads,
        "Status": status
    })

res_df = pd.DataFrame(results)
print(res_df.to_string(index=False))

# Calculate summary
print("\n--- Summary ---")
print(f"Total Meta Records: {len(m4)}")
print(f"Missing in Sheet: {len(res_df[res_df['Status'] == 'MISSING IN SHEET'])}")
print(f"Discrepancies: {len(res_df[res_df['Status'] == 'DISCREPANCY'])}")
