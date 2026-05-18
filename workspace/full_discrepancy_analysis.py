import pandas as pd
import numpy as np

# Load all data sources
meta = pd.read_csv('meta_insights_all_dates.csv')
online_sheet = pd.read_csv('online_cac_sheet.csv', header=1)
regular_sheet = pd.read_csv('regular_cac_sheet.csv', header=1)
lms = pd.read_csv('lms_leads_all_dbs.csv')

# --- Pre-processing ---
meta['Date'] = pd.to_datetime(meta['Date']).dt.date
meta['Spends'] = pd.to_numeric(meta['Spends'], errors='coerce').fillna(0)
meta['Pannel_Lead'] = pd.to_numeric(meta['Pannel_Lead'], errors='coerce').fillna(0)

def clean_sheet(df):
    df.columns = [c.strip() for c in df.columns]
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date
    # Find Spends column
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
sheets = pd.concat([online_sheet, regular_sheet])

lms['created_date'] = pd.to_datetime(lms['created_date']).dt.date

# --- Analysis Logic ---
date_range = pd.date_range(start='2026-04-28', end='2026-05-06').date
all_results = []

def get_lms_count(date, campaign_name):
    if not campaign_name or pd.isna(campaign_name): return 0
    day_lms = lms[lms['created_date'] == date]
    match = day_lms[day_lms['utm_campaign'].str.contains(str(campaign_name), case=False, na=False)]
    return match['lead_count'].sum() if not match.empty else 0

for d in date_range:
    m_day = meta[meta['Date'] == d]
    s_day = sheets[sheets['Date'] == d]
    
    for _, row in m_day.iterrows():
        ad_name = row['Ad Name']
        campaign = row['Campaign']
        meta_spend = row['Spends']
        meta_panel = row['Pannel_Lead']
        lms_actual = get_lms_count(d, campaign)
        
        sheet_match = s_day[s_day['Ad Name'] == ad_name]
        
        if not sheet_match.empty:
            s_row = sheet_match.iloc[0]
            sheet_spend = s_row['Spends_Clean']
            sheet_panel = s_row['Pannel_Lead_Clean']
            sheet_lms = s_row['LMS_Leads_Clean']
            status = "MATCH" if (abs(meta_spend - sheet_spend) < 1 and meta_panel == sheet_panel) else "DISCREPANCY"
        else:
            sheet_spend = 0
            sheet_panel = 0
            sheet_lms = 0
            status = "MISSING"
            
        all_results.append({
            "Date": d,
            "Account": row['Account'],
            "Ad Name": ad_name,
            "Meta Spend": meta_spend,
            "Sheet Spend": sheet_spend,
            "Meta Panel": meta_panel,
            "Sheet Panel": sheet_panel,
            "LMS Actual": lms_actual,
            "Sheet LMS": sheet_lms,
            "Status": status
        })

report_df = pd.DataFrame(all_results)
report_df.to_csv('final_discrepancy_report.csv', index=False)

# Summary by Date
summary = report_df.groupby(['Date', 'Status']).size().unstack(fill_value=0)
print("--- SUMMARY BY DATE ---")
print(summary)

# Filter major discrepancies (spend diff > 10 or panel diff > 2)
major = report_df[
    (report_df['Status'] == 'MISSING') | 
    (abs(report_df['Meta Spend'] - report_df['Sheet Spend']) > 10) |
    (abs(report_df['Meta Panel'] - report_df['Sheet Panel']) > 2)
]

print("\n--- MAJOR DISCREPANCIES (TOP 20) ---")
print(major.sort_values('Date', ascending=False).head(20).to_string(index=False))
