import pandas as pd
import json

# My fetched data
meta_df = pd.read_csv('meta_may4_final.csv')

# User-provided data (from the message)
user_data = [
    {"Account": "FaceBook_University_Admit", "Ad Name": "F_UA01_{UG All Colleges 3.1} {INT 01} {C1.3}", "Spends": 1121.76, "Panel": 20, "LMS": 17},
    {"Account": "FaceBook_University_Admit", "Ad Name": "F_UA1_FEB_MBA_Aryan (INT 01)_ 1.1", "Spends": 2326.33, "Panel": 26, "LMS": 21},
    {"Account": "FaceBook_University_Admit", "Ad Name": "UA_MBA_Website_Leads V1 (INT 01) C01", "Spends": 1372.93, "Panel": 9, "LMS": 17},
    {"Account": "FaceBook_University_Admit", "Ad Name": "UA_MBA_Website_Leads V1(INT 01 ) C03", "Spends": 0.75, "Panel": 0, "LMS": 0},
    {"Account": "FaceBook_University_Admit", "Ad Name": "UA_MBA_Website_Leads V2 (INT 01) C01", "Spends": 680.07, "Panel": 2, "LMS": 1},
    {"Account": "FaceBook_University_Admit", "Ad Name": "UA_MBA_Website_Leads V3 (INT 01) C01", "Spends": 11.31, "Panel": 0, "LMS": 0},
    {"Account": "FaceBook_University_Admit", "Ad Name": "UA_MBA_Website_Leads V3 (INT 01) C02", "Spends": 82.59, "Panel": 0, "LMS": 0},
    {"Account": "FaceBook_University_Admit", "Ad Name": "UA_MBA_Website_Leads V3 (INT 02) C02", "Spends": 926.82, "Panel": 11, "LMS": 10},
    {"Account": "FaceBook_University_Admit", "Ad Name": "UA_MBA_Website_Leads V3 (INT 03) C01", "Spends": 212.87, "Panel": 2, "LMS": 2},
    {"Account": "FaceBook_University_Admit", "Ad Name": "UA_MBA_Website_Leads V3 (INT 03) C03", "Spends": 45.13, "Panel": 0, "LMS": 0},
    {"Account": "FaceBook_Degreefyd_B", "Ad Name": "Galgotias_Leads_2026_P_Ad_01", "Spends": 1809.95, "Panel": 32, "LMS": 28},
    {"Account": "FaceBook_Degreefyd_B", "Ad Name": "IGNOU_Online_Courses_Admission_DFYD_Delhi_NCR_Ad01", "Spends": 958.34, "Panel": 29, "LMS": 26},
    {"Account": "FaceBook_Degreefyd_B", "Ad Name": "IGNOU_Online_Courses_Admission_DFYD_Rest_Ad01", "Spends": 541.42, "Panel": 24, "LMS": 23},
    {"Account": "FaceBook_Degreefyd_B", "Ad Name": "IGNOU_ONLINE_Degree_CR1", "Spends": 382.13, "Panel": 7, "LMS": 4},
    {"Account": "FaceBook_Degreefyd_B", "Ad Name": "Online_MBA_SF_G1_CR2", "Spends": 177.91, "Panel": 3, "LMS": 0},
    {"Account": "FaceBook_Degreefyd_B", "Ad Name": "UG_Online_Admission_SF_Ad_Set01_Ad02", "Spends": 398.7, "Panel": 3, "LMS": 3},
    {"Account": "FaceBook_Degreefyd_B", "Ad Name": "Ignou_Online_MBA_SF_Ad1", "Spends": 300.78, "Panel": 2, "LMS": 0},
    {"Account": "FaceBook_Degreefyd_B", "Ad Name": "Online_MBA_SF_G1_CR1", "Spends": 36.05, "Panel": 1, "LMS": 0},
    {"Account": "FaceBook_Degreefyd_B", "Ad Name": "UG_Online_Admission_SF_Ad_Set01_Ad01", "Spends": 71.38, "Panel": 0, "LMS": 3},
    {"Account": "FaceBook_Degreefyd_B", "Ad Name": "Online_UG&PG_SF_CR1", "Spends": 65.06, "Panel": 0, "LMS": 0},
    {"Account": "FaceBook_Degreefyd_B", "Ad Name": "Online_BBA_SF_ASH_CR1", "Spends": 137.14, "Panel": 0, "LMS": 0},
    {"Account": "FaceBook_Degreefyd_B", "Ad Name": "Online_UG&PG_SF_CR2", "Spends": 141.23, "Panel": 0, "LMS": 0},
    {"Account": "FaceBook_Degreefyd_B", "Ad Name": "Online_UG_Video_SF_VD1", "Spends": 51.61, "Panel": 0, "LMS": 0},
    {"Account": "FaceBook_Degreefyd_B", "Ad Name": "Online_UG_Video_SF_VD2", "Spends": 79.9, "Panel": 0, "LMS": 0},
    {"Account": "FaceBook_Degreefyd_B", "Ad Name": "CU_Mohali_Int_ADG1_Ad01", "Spends": 390.23, "Panel": 7, "LMS": 7},
    {"Account": "FaceBook_Degreefyd_B", "Ad Name": "CU_Lucknow_Int_ADG1_Ad01", "Spends": 589.75, "Panel": 6, "LMS": 6},
    {"Account": "FaceBook_Degreefyd_B", "Ad Name": "CU_Lucknow_Rem_Ad01", "Spends": 662.33, "Panel": 4, "LMS": 3},
    {"Account": "FaceBook_Degreefyd_B", "Ad Name": "CU_Lucknow_Rem_Ad02", "Spends": 10.45, "Panel": 1, "LMS": 1},
    {"Account": "FaceBook_Degreefyd_B", "Ad Name": "CU_Mohali_Rem_ADG1_Ad01", "Spends": 260.96, "Panel": 1, "LMS": 1},
    {"Account": "FaceBook_Degreefyd_B", "Ad Name": "CGC_Landran_UG&PG_CR1", "Spends": 28.36, "Panel": 0, "LMS": 0},
    {"Account": "FaceBook_Degreefyd_B", "Ad Name": "CGC_BTECH_REGU_SF_CR2", "Spends": 256.51, "Panel": 0, "LMS": 3},
    {"Account": "FaceBook_Degreefyd_B", "Ad Name": "CGC_BTECH_REGU_Rem_SF_AD_01", "Spends": 188.86, "Panel": 0, "LMS": 1},
    {"Account": "FaceBook_Degreefyd_B", "Ad Name": "CGC_Landran_UG&PG_SF_CR2", "Spends": 304.03, "Panel": 0, "LMS": 0},
    {"Account": "FaceBook_Degreefyd_B", "Ad Name": "CU_Mohali_Int_ADG1_Ad02", "Spends": 38.04, "Panel": 0, "LMS": 0},
    {"Account": "FaceBook_Degreefyd_B", "Ad Name": "CU_Mohali_Rem_ADG1_Ad02", "Spends": 4.56, "Panel": 0, "LMS": 0}
]
user_df = pd.DataFrame(user_data)

# Mapping account names
account_map = {
    "University_Admit_01": "FaceBook_University_Admit",
    "Degreefyd_B": "FaceBook_Degreefyd_B",
    "DegreeFYD": "FaceBook_DegreeFYD"
}
meta_df['SheetAccount'] = meta_df['Account'].map(account_map)

# Merge to compare
comparison = pd.merge(
    user_df, 
    meta_df, 
    left_on=['Account', 'Ad Name'], 
    right_on=['SheetAccount', 'Ad Name'], 
    how='outer', 
    suffixes=('_Sheet', '_API')
)

discrepancies = comparison[
    (abs(comparison['Spends_Sheet'] - comparison['Spends_API']) > 0.05) | 
    (comparison['Panel'] != comparison['Pannel_Lead'])
]

print("--- Discrepancy Report ---")
for _, row in discrepancies.iterrows():
    print(f"Ad: {row['Ad Name']}")
    print(f"  Spend: Sheet={row['Spends_Sheet']} vs API={row['Spends_API']}")
    print(f"  Panel Leads: Sheet={row['Panel']} vs API={row['Pannel_Lead']}")
    print("---")
