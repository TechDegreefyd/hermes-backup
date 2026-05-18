import pandas as pd

df = pd.read_csv('may4_reflection_final_v2.csv')

# User reported: Online 155, Regular 22. Total 177.
target_total = 177

# Mapped leads from LMS queries
lms_mapping = {
    "IGNOU_Online_Courses_Admission_DFYD": 49,
    "Galgotias_Lead_2026": 28,
    "F_UA1_FEB_MBA_Aryan v1.4": 21,
    "F_UA01_{UG All Colleges V03.1}": 17,
    "UG_Online_Admission_2026 _SF": 3,
    "CU_Mohali_Int": 7,
    "CU_Lucknow_Int": 6,
    "CU_Lucknow_Remarketing": 4,
    "CU_Mohali_Rem": 1
}

df['LMS Leads'] = 0.0

# 1. Assign known mapping
for camp, count in lms_mapping.items():
    mask = df['Campaign'] == camp
    if mask.any():
        panel_sum = df.loc[mask, 'Panel Leads'].sum()
        if panel_sum > 0:
            df.loc[mask, 'LMS Leads'] = (df.loc[mask, 'Panel Leads'] / panel_sum) * count
        else:
            df.loc[mask, 'LMS Leads'] = count / mask.sum()

mapped_sum = df['LMS Leads'].sum()
remaining = target_total - mapped_sum

# 2. Distribute remaining 41 leads proportionally across all ads with panel leads
total_panel = df['Panel Leads'].sum()
if total_panel > 0:
    df['LMS Leads'] += (df['Panel Leads'] / total_panel) * remaining

df['LMS Leads'] = df['LMS Leads'].round().astype(int)

print(f"Total LMS Leads assigned: {df['LMS Leads'].sum()}")
df.to_csv('may4_reflection_final_distributed_final.csv', index=False)
