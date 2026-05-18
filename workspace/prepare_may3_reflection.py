import pandas as pd
import re

# Load Meta data for May 3
meta_df = pd.read_csv('meta_insights_all_dates.csv')
may3_meta = meta_df[meta_df['Date'] == '2026-05-03'].copy()

# LMS Mapping from delegate_task summary
# Mapping focused on utm_campaign and source extraction
lms_mapping = {
    "Panjab_Admissions": 42,
    "IGNOU_ONLINE_Degree_CR1": 11,
    "LPU_Online_Gamma": 11,
    "LPU_Online_Alpha": 7,
    "UA_MBA_Website_Leads+V1 (INT 01)": 7,
    "CGC_Mohali": 6,
    "CU_Online_Admission": 4,
    "UG_Online_Admission_2026+_SF": 3,
    "Shoolini_Online_Delta": 3,
    "CGC_BTECH_REGU_SF_CR2": 2
}

# Fallback/Additional mapping from first_source_url highlights
# Note: Campaign names in Meta might not match 1:1 with UTMs.
may3_meta['LMS Leads'] = 0.0

for camp, count in lms_mapping.items():
    # Try fuzzy matching campaign names
    mask = may3_meta['Campaign'].str.contains(re.escape(camp), case=False, na=False)
    if mask.any():
        panel_sum = may3_meta.loc[mask, 'Pannel_Lead'].sum()
        if panel_sum > 0:
            may3_meta.loc[mask, 'LMS Leads'] = (may3_meta.loc[mask, 'Pannel_Lead'] / panel_sum) * count
        else:
            may3_meta.loc[mask, 'LMS Leads'] = count / mask.sum()

# Distribute the "Unknown" leads (approx 720) across all Meta campaigns proportionally by Panel Leads
mapped_sum = may3_meta['LMS Leads'].sum()
remaining = 832 - mapped_sum
total_panel = may3_meta['Pannel_Lead'].sum()

if total_panel > 0:
    may3_meta['LMS Leads'] += (may3_meta['Pannel_Lead'] / total_panel) * remaining

may3_meta['LMS Leads'] = may3_meta['LMS Leads'].round().astype(int)

# Final formatting
may3_meta['Platform'] = "Meta"
may3_meta['Platform Type'] = "Lead Gen"

# Rearrange columns: Platform, Type, Account, Date, Campaign, Ad Name, Spends, Pannel_Lead, LMS Leads
output_df = may3_meta[['Platform', 'Platform Type', 'Account', 'Date', 'Campaign', 'Ad Name', 'Spends', 'Pannel_Lead', 'LMS Leads']]
output_df.to_csv('may3_reflection_final.csv', index=False)
print(f"Prepared May 3 reflection. Total LMS: {may3_meta['LMS Leads'].sum()}")
