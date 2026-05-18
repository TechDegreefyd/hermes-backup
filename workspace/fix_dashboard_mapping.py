import pandas as pd
import json
import re

# 1. Load data
meta_df = pd.read_csv('meta_may4_final.csv')
with open('lms_may4_leads.json', 'r') as f:
    lms_leads = json.load(f)

# 2. Cleanup Naming Logic
# Some campaigns in LMS have suffixes like '_P_Ad_01' or university names.
# We'll try to match Meta 'Campaign' or 'Ad Name' against LMS utm_campaign.

def get_best_lms_match(meta_campaign, meta_ad_name):
    # Try exact campaign match first
    if meta_campaign in lms_leads:
        val = lms_leads.pop(meta_campaign)
        return val
    
    # Try exact ad name match
    if meta_ad_name in lms_leads:
        val = lms_leads.pop(meta_ad_name)
        return val

    # Try fuzzy match (if meta_campaign is a substring of lms_campaign or vice versa)
    for lms_camp, count in list(lms_leads.items()):
        if str(meta_campaign).lower() in str(lms_camp).lower() or str(lms_camp).lower() in str(meta_campaign).lower():
            # If it's a strong match, take it
            return lms_leads.pop(lms_camp)
        if str(meta_ad_name).lower() in str(lms_camp).lower() or str(lms_camp).lower() in str(meta_ad_name).lower():
            return lms_leads.pop(lms_camp)
            
    return 0

# Apply matching
# We iterate through the dataframe and pull from the LMS dict
meta_df['LMS Leads'] = meta_df.apply(lambda row: get_best_lms_match(row['Campaign'], row['Ad Name']), axis=1)

# Format for output
meta_df['Platform Type'] = 'Leads'
# Map Account names to match user's preferred "FaceBook_..." style
account_map = {
    "University_Admit_01": "FaceBook_University_Admit",
    "Degreefyd_B": "FaceBook_Degreefyd_B",
    "DegreeFYD": "FaceBook_DegreeFYD"
}
meta_df['Account'] = meta_df['Account'].map(account_map).fillna(meta_df['Account'])

# Final columns order
out_df = meta_df[['Platform', 'Platform Type', 'Account', 'Date', 'Campaign', 'Ad Name', 'Spends', 'Pannel_Lead', 'LMS Leads']]
# Rename for aesthetic header
out_df.columns = ['Platform', 'Type', 'Account', 'Date', 'Campaign Name', 'Ad Name', 'Spends (₹)', 'Meta Panel Leads', 'LMS Verified Leads']

# Convert to list for GAPI
headers = [out_df.columns.tolist()]
values = headers + out_df.values.tolist()
print(json.dumps(values))
