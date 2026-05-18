import pandas as pd

meta_df = pd.read_csv('meta_insights_all_dates.csv')
may5_meta = meta_df[meta_df['Date'] == '2026-05-05'].copy()

# Ensure LMS Leads is float for distribution
may5_meta['LMS Leads'] = 0.0

lms_mapping = {
    "Meta_M_Mumbai": 109,
    "Meta_M_Lucknow": 95,
    "Meta_M_Jaipur": 90,
    "Meta_M_Gurugram": 83,
    "IGNOU_Online_Courses_Admission_DFYD": 61,
    "Meta_M_Gwalior": 43,
    "Meta_M_Raipur": 34,
    "F_UA1_FEB_MBA_Aryan v1.4": 24,
    "Galgotias_Lead_2026": 25,
    "F_UA01_{UG All Colleges V03.1}": 22
}

for camp, count in lms_mapping.items():
    mask = may5_meta['Campaign'].str.contains(camp, case=False, na=False)
    if mask.any():
        panel_sum = may5_meta.loc[mask, 'Pannel_Lead'].sum()
        if panel_sum > 0:
            may5_meta.loc[mask, 'LMS Leads'] = (may5_meta.loc[mask, 'Pannel_Lead'] / panel_sum) * count
        else:
            may5_meta.loc[mask, 'LMS Leads'] = count / mask.sum()

mapped_sum = may5_meta['LMS Leads'].sum()
remaining = 838 - mapped_sum
total_panel = may5_meta['Pannel_Lead'].sum()

if total_panel > 0:
    may5_meta['LMS Leads'] += (may5_meta['Pannel_Lead'] / total_panel) * remaining

may5_meta['LMS Leads'] = may5_meta['LMS Leads'].round().astype(int)

# Check totals
print(f"Total LMS Leads: {may5_meta['LMS Leads'].sum()}")
may5_meta.to_csv('may5_reflection_final.csv', index=False)
