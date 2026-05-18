import pandas as pd

df = pd.read_csv('may4_reflection_final_v2.csv')

# Known campaign-to-leads mapping from LMS
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

# Distribute leads proportionally within identified campaigns
df['LMS Leads'] = 0.0

for camp, total_leads in lms_mapping.items():
    mask = df['Campaign'] == camp
    if mask.any():
        panel_leads = df.loc[mask, 'Panel Leads']
        total_panel = panel_leads.sum()
        if total_panel > 0:
            df.loc[mask, 'LMS Leads'] = (panel_leads / total_panel) * total_leads
        else:
            # If no panel leads, distribute equally among ads
            df.loc[mask, 'LMS Leads'] = total_leads / mask.sum()

# Distribute remaining 55 Online leads (34 empty + 21 google_form) across all Online ads proportionally
online_mask = df['Platform Type'] == 'Online'
remaining_online_leads = 55
total_online_panel = df.loc[online_mask, 'Panel Leads'].sum()

if total_online_panel > 0:
    df.loc[online_mask, 'LMS Leads'] += (df.loc[online_mask, 'Panel Leads'] / total_online_panel) * remaining_online_leads

# Final formatting
df['LMS Leads'] = df['LMS Leads'].round().astype(int)

print(f"Online LMS Total: {df[df['Platform Type'] == 'Online']['LMS Leads'].sum()}")
print(f"Regular LMS Total: {df[df['Platform Type'] == 'Regular']['LMS Leads'].sum()}")
print(f"Total LMS: {df['LMS Leads'].sum()}")

df.to_csv('may4_reflection_final_distributed_v3.csv', index=False)
