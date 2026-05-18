import pandas as pd
import json

# 1. Load ground truth Meta data (Total Leads = Onsite + Pixel)
meta_df = pd.read_csv('meta_may4_final.csv')

# 2. Load verified LMS leads (Deduplicated unique students)
with open('lms_may4_leads.json', 'r') as f:
    lms_leads = json.load(f)

# 3. Apply Fuzzy Matching to map LMS leads to Meta Ads
def get_lms_count(row):
    campaign = str(row['Campaign']).lower()
    ad_name = str(row['Ad Name']).lower()
    
    # Check exact campaign match
    for lms_camp, count in lms_leads.items():
        l_camp = str(lms_camp).lower()
        if campaign == l_camp or ad_name == l_camp:
            return count
        # Partial/Fuzzy match
        if campaign in l_camp or l_camp in campaign or ad_name in l_camp:
            return count
    return 0

meta_df['LMS_Leads'] = meta_df.apply(get_lms_count, axis=1)
meta_df['Platform Type'] = 'Leads'

# Account mapping for the main sheets
account_map = {
    "University_Admit_01": "FaceBook_University_Admit",
    "Degreefyd_B": "FaceBook_Degreefyd_B",
    "DegreeFYD": "FaceBook_DegreeFYD"
}
meta_df['Account_Mapped'] = meta_df['Account'].map(account_map).fillna(meta_df['Account'])

# 4. Split into Online vs Regular based on campaign and account
# University_Admit_01 is primarily Online. Degreefyd_B is mixed (CU/CGC are Regular).

# Online Data Preparation (Header row 2 starts at A, ends at I)
online_ads = meta_df[
    (meta_df['Account_Mapped'] == 'FaceBook_University_Admit') | 
    (meta_df['Campaign'].str.contains('IGNOU|Online|UG_Online', case=False))
].copy()

# Header: Platform, Platform Type, Account, Date, Campaign, Ad Name, Spends (₹), Panel Leads, LMS Leads
online_out = online_ads[['Platform', 'Platform Type', 'Account_Mapped', 'Date', 'Campaign', 'Ad Name', 'Spends', 'Pannel_Lead', 'LMS_Leads']]
online_out.columns = ['Platform', 'Platform Type', 'Account', 'Date', 'Campaign', 'Ad Name', 'Spends (₹)', 'Panel Leads', 'LMS Leads']

# Regular Data Preparation
regular_ads = meta_df[meta_df['Campaign'].str.contains('CU_|CGC_|LPU_', case=False)].copy()
regular_out = regular_ads[['Platform', 'Platform Type', 'Account_Mapped', 'Date', 'Campaign', 'Ad Name', 'Spends', 'Pannel_Lead', 'LMS_Leads']]
regular_out.columns = ['Platform', 'Platform Type', 'Account', 'Date', 'Campaign', 'Ad Name', 'Spends (₹)', 'Panel Leads', 'LMS Leads']

# Convert to JSON for GAPI
print(json.dumps({
    "online": online_out.values.tolist(),
    "regular": regular_out.values.tolist()
}))
