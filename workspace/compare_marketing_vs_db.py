import pandas as pd

# Load the parsed raw marketing data
df_mkt = pd.read_csv("may3_marketing_raw_parsed.csv")
# Filter for May 3rd only to match my recent DB pull
df_mkt_may3 = df_mkt[df_mkt['Date'] == '2026-05-03']

# Load the activity-based DB query results
df_db = pd.read_csv("lms_leads_activity_may3.csv")

print("--- Comparison for May 3rd ---")
print(f"Marketing Total LMS Leads: {df_mkt_may3['lead_LMS'].sum()}")

# Direct matches on Campaign/Ad Name
matches = []
for idx, row in df_mkt_may3.iterrows():
    camp = str(row['Campaign']).strip()
    ad = str(row['Ad Name']).strip()
    
    db_leads = df_db[df_db['utm_campaign'].isin([camp, ad])]['lead_count'].sum()
    matches.append({
        "Campaign": camp,
        "Ad Name": ad,
        "Marketing_LMS": row['lead_LMS'],
        "DB_Activity_LMS": db_leads,
        "Diff": db_leads - row['lead_LMS']
    })

df_comp = pd.DataFrame(matches)
print("\nTop Discrepancies (DB vs Marketing):")
print(df_comp[df_comp['Diff'] != 0].sort_values('Diff', key=abs, ascending=False).head(10))

# Check for leads in DB that are NOT in marketing list
mkt_camps = df_mkt_may3['Campaign'].unique().tolist() + df_mkt_may3['Ad Name'].unique().tolist()
unaccounted_db = df_db[~df_db['utm_campaign'].isin(mkt_camps)]
print(f"\nLeads in DB NOT matched to any Marketing Ad Name/Campaign: {unaccounted_db['lead_count'].sum()}")
print("Top Unmatched DB Campaigns:")
print(unaccounted_db.sort_values('lead_count', ascending=False).head(10))
