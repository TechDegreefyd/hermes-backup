import pandas as pd
import json

# Load raw Meta data
meta_df = pd.read_csv('meta_insights_raw.csv')
# Convert Date to datetime for matching
meta_df['Date'] = pd.to_datetime(meta_df['Date'])

# Load Sheet data (skip header rows if needed, assuming row 1 is header)
online_df = pd.read_csv('online_cac_sheet.csv')
regular_df = pd.read_csv('regular_cac_sheet.csv')

# Clean headers: trip spaces
online_df.columns = [c.strip() for c in online_df.columns]
regular_df.columns = [c.strip() for c in regular_df.columns]

# Summarize Meta data by Account and Date for a high-level match
meta_summary = meta_df.groupby(['Account', 'Date']).agg({
    'Spends': 'sum',
    'Pannel_Lead': 'sum'
}).reset_index()

print("--- META SUMMARY (28 April - 6 May) ---")
print(meta_summary.to_string())

# Note: Matching to sheets requires knowing which columns in the sheets represent Spends and Panel Leads
# For Online Sheet (1jzgnRxmmLIe_DAZ7nwHSRXeO6sI4CRxlTatc0T88ukY)
# For Regular Sheet (1QQ_Z50FDAhuBbVX5ioCjfgyFjfhr3y0gMGbQqteQ1f8)

print("\n--- FIRST 5 ROWS ONLINE SHEET ---")
print(online_df.head(5).to_string())

print("\n--- FIRST 5 ROWS REGULAR SHEET ---")
print(regular_df.head(5).to_string())
