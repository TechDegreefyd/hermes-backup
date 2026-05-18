import pandas as pd
import numpy as np

# Load University Admit data
df_ua = pd.read_csv("university_admit_may3.csv")

# Load other Meta accounts
try:
    df_all = pd.read_csv("meta_insights_all_dates.csv")
    df_other = df_all[(df_all['Date'] == '2026-05-03') & (df_all['Account'].isin(['Degreefyd_B', 'DegreeFYD']))]
    df_other = df_other.rename(columns={'Account': 'Account', 'Campaign': 'Campaign', 'Ad Name': 'Ad Name', 'Spends (₹)': 'Spends', 'Panel Leads': 'Pannel_Lead'})
    df_other['Platform'] = 'Meta'
    df_other['Platform Type'] = 'Lead Gen'
    df_other = df_other[['Platform', 'Platform Type', 'Account', 'Date', 'Campaign', 'Ad Name', 'Spends', 'Pannel_Lead']]
except Exception as e:
    df_other = pd.read_csv("may3_reflection_final.csv")
    df_other = df_other[df_other['Account'].isin(['Degreefyd_B', 'DegreeFYD'])]

df_meta = pd.concat([df_other, df_ua], ignore_index=True)

# Load Activity-based LMS leads
df_lms = pd.read_csv("lms_leads_activity_may3.csv")

def map_activity_leads(df_meta, df_lms):
    df_meta['lead_LMS'] = 0.0
    df_lms['mapped'] = False
    
    # 1. Direct Mapping
    for idx, row in df_meta.iterrows():
        campaign = str(row['Campaign']).strip()
        ad_name = str(row['Ad Name']).strip()
        
        # Exact match on campaign name
        mask = (df_lms['utm_campaign'].astype(str).str.strip() == campaign)
        if mask.any():
            df_meta.at[idx, 'lead_LMS'] += df_lms.loc[mask, 'lead_count'].sum()
            df_lms.loc[mask, 'mapped'] = True
            
        # Match on ad name
        mask_ad = (df_lms['utm_campaign'].astype(str).str.strip() == ad_name)
        if mask_ad.any():
            df_meta.at[idx, 'lead_LMS'] += df_lms.loc[mask_ad, 'lead_count'].sum()
            df_lms.loc[mask_ad, 'mapped'] = True

    # 2. Residual Attribution
    unmapped = df_lms[~df_lms['mapped']]
    
    # Identify Meta-related unmapped leads
    # Numeric IDs usually correspond to campaign IDs
    def is_numeric(s):
        try:
            float(s)
            return True
        except:
            return False

    meta_related_mask = unmapped['utm_campaign'].apply(lambda x: 
        is_numeric(str(x)) or 
        any(k in str(x) for k in ['FaceBook', 'Meta', 'UA', 'F_UA', 'DegreeFyd'])
    )
    
    meta_leads_df = unmapped[meta_related_mask]
    
    # Separate UA from Others
    ua_leads = meta_leads_df[meta_leads_df['utm_campaign'].str.contains('UA|F_UA', case=False, na=False)]['lead_count'].sum()
    others_leads = meta_leads_df[~meta_leads_df['utm_campaign'].str.contains('UA|F_UA', case=False, na=False)]['lead_count'].sum()
    
    # Distribute UA
    ua_mask = df_meta['Account'] == 'University_Admit_01'
    if ua_leads > 0 and ua_mask.any():
        panel_ua = df_meta.loc[ua_mask, 'Pannel_Lead'].sum()
        if panel_ua > 0:
            df_meta.loc[ua_mask, 'lead_LMS'] += (df_meta.loc[ua_mask, 'Pannel_Lead'] / panel_ua) * ua_leads
        else:
            df_meta.loc[ua_mask, 'lead_LMS'] += ua_leads / ua_mask.sum()

    # Distribute Others (Degreefyd_B, DegreeFYD)
    others_mask = df_meta['Account'].isin(['Degreefyd_B', 'DegreeFYD'])
    if others_leads > 0 and others_mask.any():
        panel_others = df_meta.loc[others_mask, 'Pannel_Lead'].sum()
        if panel_others > 0:
            df_meta.loc[others_mask, 'lead_LMS'] += (df_meta.loc[others_mask, 'Pannel_Lead'] / panel_others) * others_leads
        else:
            df_meta.loc[others_mask, 'lead_LMS'] += others_leads / others_mask.sum()

    return df_meta

df_final = map_activity_leads(df_meta, df_lms)
df_final['lead_LMS'] = df_final['lead_LMS'].round().astype(int)

df_final = df_final[['Platform', 'Platform Type', 'Account', 'Date', 'Campaign', 'Ad Name', 'Spends', 'Pannel_Lead', 'lead_LMS']]
df_final.to_csv("may3_reflection_activity_final.csv", index=False)
print(f"Total LMS leads distributed (Activity-based): {df_final['lead_LMS'].sum()}")
print(df_final.head())
