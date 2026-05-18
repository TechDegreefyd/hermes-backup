import pandas as pd
import numpy as np

# Load data
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
df_lms = pd.read_csv("lms_leads_activity_may3.csv")

def map_activity_leads(df_meta, df_lms):
    df_meta['lead_LMS'] = 0.0
    df_lms['mapped'] = False
    
    # 1. Direct Mapping
    for idx, row in df_meta.iterrows():
        campaign = str(row['Campaign']).strip()
        ad_name = str(row['Ad Name']).strip()
        mask = (df_lms['utm_campaign'].astype(str).str.strip() == campaign) | (df_lms['utm_campaign'].astype(str).str.strip() == ad_name)
        if mask.any():
            df_meta.at[idx, 'lead_LMS'] += df_lms.loc[mask, 'lead_count'].sum()
            df_lms.loc[mask, 'mapped'] = True

    # 2. Residual Attribution for Meta-related sources
    unmapped = df_lms[~df_lms['mapped']]
    
    def is_meta_source(utm):
        utm = str(utm)
        if utm.isdigit() and len(utm) > 5: return True # Likely Campaign ID
        if any(k in utm for k in ['FaceBook', 'Meta', 'UA', 'F_UA', 'S_P', 'S_F']): return True
        return False

    meta_leads_df = unmapped[unmapped['utm_campaign'].apply(is_meta_source)]
    
    # Separate UA from Others
    ua_leads = meta_leads_df[meta_leads_df['utm_campaign'].str.contains('UA|F_UA', case=False, na=False)]['lead_count'].sum()
    others_leads = meta_leads_df[~meta_leads_df['utm_campaign'].str.contains('UA|F_UA', case=False, na=False)]['lead_count'].sum()
    
    # Distribute
    def distribute(mask, amount):
        if amount > 0 and mask.any():
            panel = df_meta.loc[mask, 'Pannel_Lead'].sum()
            if panel > 0:
                df_meta.loc[mask, 'lead_LMS'] += (df_meta.loc[mask, 'Pannel_Lead'] / panel) * amount
            else:
                df_meta.loc[mask, 'lead_LMS'] += amount / mask.sum()

    distribute(df_meta['Account'] == 'University_Admit_01', ua_leads)
    distribute(df_meta['Account'].isin(['Degreefyd_B', 'DegreeFYD']), others_leads)

    return df_meta

df_final = map_activity_leads(df_meta, df_lms)
df_final['lead_LMS'] = df_final['lead_LMS'].round().astype(int)
df_final = df_final[['Platform', 'Platform Type', 'Account', 'Date', 'Campaign', 'Ad Name', 'Spends', 'Pannel_Lead', 'lead_LMS']]
df_final.to_csv("may3_reflection_activity_final_v2.csv", index=False)
print(f"Total LMS leads distributed (Activity-based): {df_final['lead_LMS'].sum()}")
