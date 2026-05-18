import pandas as pd

# Load the Meta data for May 4
df = pd.read_csv('may4_reflection_final_v2.csv')

# Query results mapped to campaign names
# Online
online_campaign_lms = {
    "IGNOU_Online_Courses_Admission_DFYD": 49,
    "Galgotias_Lead_2026": 28,
    "F_UA1_FEB_MBA_Aryan v1.4": 21,
    "F_UA01_{UG All Colleges V03.1}": 17,
    "UG_Online_Admission_2026+_SF": 3,
    "LPU_Online_Alpha": 3,
    "Panjab_Admissions": 1
}
unknown_online = 34 + 21 # Empty utm_campaign + google_form leads

# Regular
regular_campaign_lms = {
    "CU_Mohali_Int": 7,
    "CU_Lucknow_Int": 6,
    "CU_Lucknow_Remarketing": 4,
    "CU_Mohali_Rem": 1
}

# 1. First, assign known campaign leads
df['LMS Leads'] = 0.0

# Apply known campaign leads
for camp, count in online_campaign_lms.items():
    mask = df['Campaign'].str.contains(camp.replace('{','').replace('}',''), case=False, na=False)
    if mask.any():
        total_panel = df.loc[mask, 'Panel Leads'].sum()
        if total_panel > 0:
            df.loc[mask, 'LMS Leads'] += (df.loc[mask, 'Panel Leads'] / total_panel) * count

for camp, count in regular_campaign_lms.items():
    mask = df['Campaign'].str.contains(camp, case=False, na=False)
    if mask.any():
        total_panel = df.loc[mask, 'Panel Leads'].sum()
        if total_panel > 0:
            df.loc[mask, 'LMS Leads'] += (df.loc[mask, 'Panel Leads'] / total_panel) * count

# 2. Distribute "Unknown" Online leads across all Online ads proportionally
online_mask = df['Platform Type'] == 'Online'
total_online_panel = df.loc[online_mask, 'Panel Leads'].sum()
if total_online_panel > 0:
    df.loc[online_mask, 'LMS Leads'] += (df.loc[online_mask, 'Panel Leads'] / total_online_panel) * unknown_online

# Round and convert to int
df['LMS Leads'] = df['LMS Leads'].round().astype(int)

# Check totals
print(f"Online LMS Leads: {df[df['Platform Type'] == 'Online']['LMS Leads'].sum()}")
print(f"Regular LMS Leads: {df[df['Platform Type'] == 'Regular']['LMS Leads'].sum()}")

df.to_csv('may4_reflection_final_distributed_v2.csv', index=False)
