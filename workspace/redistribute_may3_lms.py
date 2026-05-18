import pandas as pd

# Load the May 3rd Meta data
df_meta = pd.read_csv("may3_reflection_final_v3.csv")

# Load the May 3rd LMS leads
df_lms = pd.read_csv("lms_leads_may3_detailed.csv")

# Define the sources we consider as "Meta"
# Based on the data: 'FaceBook', 'Facebook', 'FaceBook_University_Admit', 'Meta_M'
meta_sources = ['FaceBook', 'Facebook', 'FaceBook_University_Admit', 'Meta_M']
df_meta_lms = df_lms[df_lms['utm_campaign'].isin(meta_sources)]
total_meta_lms = df_meta_lms['lead_count'].sum()

print(f"Total Meta-related LMS leads for May 3rd: {total_meta_lms}")

# Map accounts to specific UTMs for better precision
ua_lms = df_lms[df_lms['utm_campaign'] == 'FaceBook_University_Admit']['lead_count'].sum()
other_lms = df_lms[df_lms['utm_campaign'].isin(['FaceBook', 'Facebook', 'Meta_M'])]['lead_count'].sum()

print(f"UA LMS leads: {ua_lms}")
print(f"DegreeFYD/B LMS leads (incl. Meta_M): {other_lms}")

# Redistribute
df_meta['lead_LMS'] = 0.0

# 1. University_Admit_01
mask_ua = df_meta['Account'] == 'University_Admit_01'
if mask_ua.any():
    panel_ua = df_meta.loc[mask_ua, 'Pannel_Lead'].sum()
    if panel_ua > 0:
        df_meta.loc[mask_ua, 'lead_LMS'] = (df_meta.loc[mask_ua, 'Pannel_Lead'] / panel_ua) * ua_lms
    else:
        df_meta.loc[mask_ua, 'lead_LMS'] = ua_lms / mask_ua.sum()

# 2. DegreeFYD and Degreefyd_B
mask_others = df_meta['Account'].isin(['DegreeFYD', 'Degreefyd_B'])
if mask_others.any():
    panel_others = df_meta.loc[mask_others, 'Pannel_Lead'].sum()
    if panel_others > 0:
        df_meta.loc[mask_others, 'lead_LMS'] = (df_meta.loc[mask_others, 'Pannel_Lead'] / panel_others) * other_lms
    else:
        df_meta.loc[mask_others, 'lead_LMS'] = other_lms / mask_others.sum()

# Round and finalize
df_meta['lead_LMS'] = df_meta['lead_LMS'].round().astype(int)
print(f"Final distributed LMS total: {df_meta['lead_LMS'].sum()}")

# Save to final CSV
df_meta.to_csv("may3_reflection_final_distributed_v4.csv", index=False)
