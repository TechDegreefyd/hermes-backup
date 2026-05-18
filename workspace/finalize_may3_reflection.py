import pandas as pd
import numpy as np

df_ua = pd.read_csv("university_admit_may3.csv")
try:
    df_all = pd.read_csv("meta_insights_all_dates.csv")
    df_other = df_all[(df_all['Date'] == '2026-05-03') & (df_all['Account'].isin(['Degreefyd_B', 'DegreeFYD']))]
    df_other = df_other.rename(columns={'Account': 'Account', 'Campaign': 'Campaign', 'Ad Name': 'Ad Name', 'Spends (₹)': 'Spends', 'Panel Leads': 'Pannel_Lead'})
    df_other['Platform'] = 'Meta'
    df_other['Platform Type'] = 'Lead Gen'
    df_other = df_other[['Platform', 'Platform Type', 'Account', 'Date', 'Campaign', 'Ad Name', 'Spends', 'Pannel_Lead']]
except Exception as e:
    print(f"Error loading meta_insights_all_dates.csv: {e}")
    df_other = pd.read_csv("may3_reflection_final.csv")
    df_other = df_other[df_other['Account'].isin(['Degreefyd_B', 'DegreeFYD'])]

df_meta = pd.concat([df_other, df_ua], ignore_index=True)
df_lms = pd.read_csv("lms_leads_may3_detailed.csv")

# Account mapping to utm_campaign strings
account_map = {
    'University_Admit_01': 'FaceBook_University_Admit',
    'DegreeFYD': 'FaceBook',
    'Degreefyd_B': 'FaceBook'
}

def distribute_lms(df_meta, df_lms):
    df_meta['lead_LMS'] = 0.0
    
    # Process accounts
    for account, utm in account_map.items():
        # Get total LMS leads for this account-source
        lms_total = df_lms[df_lms['utm_campaign'].str.contains(utm, case=False, na=False)]['lead_count'].sum()
        
        # Get ads for this account
        mask = df_meta['Account'] == account
        if mask.any() and lms_total > 0:
            # Distribute based on Panel Leads ratio
            panel_total = df_meta.loc[mask, 'Pannel_Lead'].sum()
            if panel_total > 0:
                df_meta.loc[mask, 'lead_LMS'] = (df_meta.loc[mask, 'Pannel_Lead'] / panel_total) * lms_total
            else:
                # Distribute equally if no panel leads
                count = mask.sum()
                df_meta.loc[mask, 'lead_LMS'] = lms_total / count
    
    return df_meta

df_final = distribute_lms(df_meta, df_lms)
df_final['lead_LMS'] = df_final['lead_LMS'].round().astype(int)

df_final = df_final[['Platform', 'Platform Type', 'Account', 'Date', 'Campaign', 'Ad Name', 'Spends', 'Pannel_Lead', 'lead_LMS']]
df_final.to_csv("may3_reflection_final_v3.csv", index=False)
print(f"Total LMS leads distributed: {df_final['lead_LMS'].sum()}")
print(df_final.head())
