import pandas as pd
import numpy as np

# Meta Data
meta_df = pd.read_csv('meta_insights_raw.csv')
meta_df['Date'] = pd.to_datetime(meta_df['Date']).dt.date

# Online Sheet: Header is at row 1
online_df = pd.read_csv('online_cac_sheet.csv', header=1)
online_df.columns = [c.strip() for c in online_df.columns]
online_df['Date'] = pd.to_datetime(online_df['Date'], errors='coerce').dt.date

# Regular Sheet: Header is at row 1
regular_df = pd.read_csv('regular_cac_sheet.csv', header=1)
regular_df.columns = [c.strip() for c in regular_df.columns]
regular_df['Date'] = pd.to_datetime(regular_df['Date'], errors='coerce').dt.date

def match_data(meta_df, sheet_df, label):
    print(f"\n--- MATCHING META TO {label} SHEET ---")
    sheet_df = sheet_df[sheet_df['Date'].notnull()].copy()
    
    # Clean sheet numeric columns
    for col in ['Spends', 'Pannel_Lead']:
        if col in sheet_df.columns:
            sheet_df[col] = sheet_df[col].astype(str).str.replace('₹','').str.replace(',','').replace('nan', '0').replace('-', '0')
            sheet_df[col] = pd.to_numeric(sheet_df[col], errors='coerce').fillna(0)

    # Perform Merge on Date and Ad Name
    # Stripping whitespace from Ad Name to improve matching
    meta_df['Ad Name Clean'] = meta_df['Ad Name'].astype(str).str.strip().str.lower()
    sheet_df['Ad Name Clean'] = sheet_df['Ad Name'].astype(str).str.strip().str.lower()
    
    merged = pd.merge(
        meta_df, 
        sheet_df, 
        left_on=['Date', 'Ad Name Clean'],
        right_on=['Date', 'Ad Name Clean'],
        how='inner', 
        suffixes=('_Meta', '_Sheet')
    )
    
    if not merged.empty:
        cols = ['Date', 'Ad Name_Meta', 'Spends_Meta', 'Spends_Sheet', 'Pannel_Lead_Meta', 'Pannel_Lead_Sheet']
        print(merged[cols].head(15).to_string())
        print(f"Total Matches: {len(merged)}")
    else:
        print("No exact Ad Name + Date matches found.")
        print("Sample Sheet Ad Names:", sheet_df['Ad Name'].unique()[:5])
        print("Sample Meta Ad Names:", meta_df['Ad Name'].unique()[:5])

match_data(meta_df, online_df, "ONLINE")
match_data(meta_df, regular_df, "REGULAR")
