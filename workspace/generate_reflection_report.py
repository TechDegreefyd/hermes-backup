import pandas as pd
import json

# Meta data
meta_df = pd.read_csv('meta_may4_full_corrected.csv')

# LMS data
lms_data = {
    "Galgotias_Lead_2026": 2,
    "LPU_Online_Gamma": 2,
    "CU_Online_V1": 1,
    "IGNOU_Online_Courses_Admission_DFYD": 1,
    "Manipal_Online_V1": 1,
    "CU_Online_Admission_Zeta": 1,
    "LPU_Online_Alpha": 1,
    "Panjab_Admissions": 1,
    "CGC_Mohali": 1,
    "Meta_M_Bangalore": 1
}

def get_lms_leads(campaign_name):
    # Try exact match
    if campaign_name in lms_data:
        return lms_data[campaign_name]
    
    # Try case-insensitive exact match
    for k, v in lms_data.items():
        if k.lower() == campaign_name.lower():
            return v
            
    # No match
    return 0

meta_df['LMS Leads'] = meta_df['Campaign'].apply(get_lms_leads)

# Reorder columns to match user's preferred format
# Columns: Platform, Platform Type, Account, Date, Campaign, Ad Name, Spends (₹), Panel Leads, LMS Leads
# Platform Type is missing in Meta API, I'll set it to 'Lead Gen' or similar.
meta_df['Platform Type'] = 'Lead Gen'
cols = ['Platform', 'Platform Type', 'Account', 'Date', 'Campaign', 'Ad Name', 'Spends', 'Pannel_Lead', 'LMS Leads']
meta_df = meta_df[cols]

# Save to CSV
meta_df.to_csv('may4_reflection_final.csv', index=False)
print(f"Generated reflection report with {len(meta_df)} rows.")
print(meta_df.head())
