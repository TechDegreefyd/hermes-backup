import pandas as pd
df_meta = pd.read_csv("meta_insights_all_dates.csv")
# Create mapping
mapping = df_meta[['Campaign ID', 'Campaign']].drop_duplicates()
print("Campaign ID to Name mapping:")
print(mapping)
