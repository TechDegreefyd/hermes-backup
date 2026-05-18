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

# Pre-process Sheets (Header is at row 2, index 1)
def clean_sheet(df):
    df.columns = [c.strip() for c in df.columns]
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date
    # Find Spends column (could be Spends or Spends (₹))
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

# Filter for May 4
target_date = pd.to_datetime('2026-05-04').date()
m4 = meta[meta['Date'] == target_date].copy()
o4 = online_sheet[online_sheet['Date'] == target_date].copy()
r4 = regular_sheet[regular_sheet['Date'] == target_date].copy()
l4 = lms[pd.to_datetime(lms['created_date']).dt.date == target_date].copy()

s4 = pd.concat([o4, r4])

def get_lms_count(campaign_name):
    if not campaign_name or pd.isna(campaign_name): return 0
    # Try exact match first
    match = l4[l4['utm_campaign'] == campaign_name]
    if match.empty:
        # Try partial
        match = l4[l4['utm_campaign'].str.contains(str(campaign_name), case=False, na=False)]
    return match['lead_count'].sum() if not match.empty else 0

results = []
for _, row in m4.iterrows():
    ad_name = row['Ad Name']
    campaign = row['Campaign Name']
    meta_spend = row['Spends']
    meta_leads = row['Pannel_Lead']
    lms_leads = get_lms_count(campaign)
    
    sheet_row = s4[s4['Ad Name'] == ad_name]
    
    if not sheet_row.empty:
        sheet_spend = sheet_row['Spends_Clean'].iloc[0]
        sheet_leads = sheet_row['Pannel_Lead_Clean'].iloc[0]
        status = "MATCH" if (abs(meta_spend - sheet_spend) < 5 and meta_leads == sheet_leads) else "DISCREPANCY"
    else:
        sheet_spend = 0
        sheet_leads = 0
        status = "MISSING"
    
    results.append({
        "Date": target_date,
        "Account": row['Account Name'],
        "Campaign": campaign,
        "Ad Name": ad_name,
        "Meta Spend": round(meta_spend, 2),
        "Sheet Spend": round(sheet_spend, 2),
        "Meta Panel": int(meta_leads),
        "Sheet Panel": int(sheet_leads),
        "LMS": int(lms_leads),
        "Status": status
    })

res_df = pd.DataFrame(results)
# Sort by Account and status
res_df = res_df.sort_values(['Account', 'Status'])
print(res_df.to_string(index=False))

print("\n--- Summary ---")
print(f"Total Meta Records: {len(m4)}")
print(f"Missing in Sheet: {len(res_df[res_df['Status'] == 'MISSING'])}")
print(f"Discrepancies: {len(res_df[res_df['Status'] == 'DISCREPANCY'])}")
