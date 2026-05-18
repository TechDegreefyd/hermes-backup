import pandas as pd
import numpy as np

# 1. Load Meta Data (the data I fetched via API earlier)
meta_df = pd.read_csv('meta_insights_all_dates.csv')
meta_df['Date'] = pd.to_datetime(meta_df['Date']).dt.date
meta_may4 = meta_df[meta_df['Date'] == pd.to_datetime('2026-05-04').date()].copy()

# 2. Load the Google Sheet Data (Online)
online_sheet = pd.read_csv('online_cac_sheet.csv', header=1)
online_sheet.columns = [c.strip() for c in online_sheet.columns]
online_sheet['Date'] = pd.to_datetime(online_sheet['Date'], errors='coerce').dt.date
sheet_may4 = online_sheet[online_sheet['Date'] == pd.to_datetime('2026-05-04').date()].copy()

# User's "Truth" table provided in the prompt for May 4
user_data = [
    {"Ad": "CU_Mohali_Int_ADG1_Ad01", "Spend": 390.23, "Panel": 7, "LMS": 7},
    {"Ad": "CU_Lucknow_Int_ADG1_Ad01", "Spend": 589.75, "Panel": 6, "LMS": 6},
    {"Ad": "CU_Lucknow_Rem_Ad01", "Spend": 662.33, "Panel": 4, "LMS": 3},
    {"Ad": "CU_Lucknow_Rem_Ad02", "Spend": 10.45, "Panel": 1, "LMS": 1},
    {"Ad": "CU_Mohali_Rem_ADG1_Ad01", "Spend": 260.96, "Panel": 1, "LMS": 1},
    {"Ad": "F_UA01_{UG All Colleges 3.1} {INT 01} {C1.3}", "Spend": 1121.76, "Panel": 20, "LMS": 17},
    {"Ad": "F_UA1_FEB_MBA_Aryan (INT 01)_ 1.1", "Spend": 2326.33, "Panel": 26, "LMS": 21},
    {"Ad": "UA_MBA_Website_Leads V1 (INT 01) C01", "Spend": 1372.93, "Panel": 9, "LMS": 17},
    {"Ad": "Galgotias_Leads_2026_P_Ad_01", "Spend": 1809.95, "Panel": 32, "LMS": 28},
    {"Ad": "IGNOU_Online_Courses_Admission_DFYD_Delhi_NCR_Ad01", "Spend": 958.34, "Panel": 29, "LMS": 26},
    {"Ad": "IGNOU_Online_Courses_Admission_DFYD_Rest_Ad01", "Spend": 541.42, "Panel": 24, "LMS": 23},
    {"Ad": "IGNOU_ONLINE_Degree_CR1", "Spend": 382.13, "Panel": 7, "LMS": 4}
]

print("--- COMPARISON FOR MAY 4, 2026 ---")
print(f"{'Ad Name':<45} | {'Source':<10} | {'Spend':<8} | {'Leads':<5}")
print("-" * 75)

for item in user_data:
    ad = item['Ad']
    # 1. Show User's provided values
    print(f"{ad[:45]:<45} | {'User Tbl':<10} | {item['Spend']:<8.2f} | {item['Panel']:<5}")
    
    # 2. Show Meta API values
    m_row = meta_may4[meta_may4['Ad Name'].str.contains(ad.split(' {')[0], case=False, na=False)]
    if not m_row.empty:
        print(f"{'':<45} | {'Meta API':<10} | {m_row['Spends'].sum():<8.2f} | {m_row['Pannel_Lead'].sum():<5}")
    else:
        print(f"{'':<45} | {'Meta API':<10} | {'NOT FOUND':<14}")

    # 3. Show Sheet values
    s_row = sheet_may4[sheet_may4['Ad Name'].str.contains(ad.split(' {')[0], case=False, na=False)]
    if not s_row.empty:
        s_spend_raw = str(s_row.iloc[0]['Spends']).replace('₹','').replace(',','').replace('-','0')
        try: s_spend = float(s_spend_raw)
        except: s_spend = 0.0
        print(f"{'':<45} | {'Sheet':<10} | {s_spend:<8.2f} | {s_row.iloc[0]['Pannel_Lead']:<5}")
    else:
        print(f"{'':<45} | {'Sheet':<10} | {'MISSING':<14}")
    print("-" * 75)

