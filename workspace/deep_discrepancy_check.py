import pandas as pd

# Load mappings
df_map = pd.read_csv("campaign_id_mapping.csv")
mapping_dict = dict(zip(df_map['Campaign ID'], df_map['Campaign Name']))

# Load DB activity
df_db = pd.read_csv("lms_leads_activity_may3.csv")

# Translate Numeric IDs in DB to Names
df_db['Translated Name'] = df_db['utm_campaign'].apply(lambda x: mapping_dict.get(str(x), x))

# Load Marketing Raw
df_mkt = pd.read_csv("may3_marketing_raw_parsed.csv")
df_mkt_may3 = df_mkt[df_mkt['Date'] == '2026-05-03']

print("--- Translated DB Activity vs Marketing Raw (May 3rd) ---")

# Compare
results = []
for idx, row in df_mkt_may3.iterrows():
    mkt_camp = row['Campaign']
    mkt_ad = row['Ad Name']
    
    # Sum all leads in DB that match either name or ad name after translation
    db_match = df_db[(df_db['Translated Name'] == mkt_camp) | (df_db['Translated Name'] == mkt_ad)]
    db_leads = db_match['lead_count'].sum()
    
    results.append({
        "Campaign": mkt_camp,
        "Ad Name": mkt_ad,
        "Marketing_LMS": row['lead_LMS'],
        "DB_Activity_LMS": db_leads,
        "Diff": db_leads - row['lead_LMS']
    })

df_final_comp = pd.DataFrame(results)
print(df_final_comp[df_final_comp['Diff'] != 0].sort_values('Diff', key=abs, ascending=False))

# Sum of unaccounted leads
accounted_names = df_mkt_may3['Campaign'].tolist() + df_mkt_may3['Ad Name'].tolist()
unaccounted_db = df_db[~df_db['Translated Name'].isin(accounted_names)]
print(f"\nTotal Leads in DB still unmapped: {unaccounted_db['lead_count'].sum()}")
print("Top Unmapped Translated Campaigns:")
print(unaccounted_db.sort_values('lead_count', ascending=False).head(10))
