import pandas as pd
import json

# 1. Load Meta Data
meta_df = pd.read_csv('meta_insights_raw.csv')
meta_df['Date'] = pd.to_datetime(meta_df['Date']).dt.date

# 2. Load Google Sheets Data
online_df = pd.read_csv('online_cac_sheet.csv', header=1)
online_df.columns = [c.strip() for c in online_df.columns]
online_df['Date'] = pd.to_datetime(online_df['Date'], errors='coerce').dt.date

regular_df = pd.read_csv('regular_cac_sheet.csv', header=1)
regular_df.columns = [c.strip() for c in regular_df.columns]
regular_df['Date'] = pd.to_datetime(regular_df['Date'], errors='coerce').dt.date

target_dates = [pd.to_datetime(d).date() for d in ['2026-05-01', '2026-05-02', '2026-05-03', '2026-05-04']]
meta_sub = meta_df[meta_df['Date'].isin(target_dates)].copy()

def diagnose(meta_sub, sheet_df, label):
    print(f"\n--- DIAGNOSIS: {label} ---")
    sheet_sub = sheet_df[sheet_df['Date'].isin(target_dates)].copy()
    
    meta_sub['AdClean'] = meta_sub['Ad Name'].str.strip().str.lower()
    sheet_sub['AdClean'] = sheet_sub['Ad Name'].astype(str).str.strip().str.lower()
    
    merged = pd.merge(meta_sub, sheet_sub, on=['Date', 'AdClean'], how='left', suffixes=('_Meta', '_Sheet'))
    
    missing_in_sheet = merged[merged['Ad Name_Sheet'].isna()]
    print(f"Total Meta Records: {len(meta_sub)}")
    print(f"Records missing in {label} sheet: {len(missing_in_sheet)}")
    
    if not missing_in_sheet.empty:
        print("\nTop Missing Ads in Sheet:")
        print(missing_in_sheet[['Date', 'Account_Meta', 'Ad Name_Meta']].head(10).to_string())

diagnose(meta_sub, online_df, "ONLINE")
diagnose(meta_sub, regular_df, "REGULAR")
