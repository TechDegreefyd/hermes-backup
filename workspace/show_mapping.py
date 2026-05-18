import pandas as pd

lms_df = pd.read_csv('/home/mohit/workspace/lms_detailed_05_07.csv')
meta_df = pd.read_csv('/home/mohit/workspace/final_meta_data_05_07.csv')

# This is just a conceptual mapping summary for the user
print("Mapping Summary (How Meta campaigns match to LMS utm_campaigns):")
print("1. Strict Matching:")
print("- F_UA01_{UG All Colleges V03.1} -> matched with LMS 'F_UA01_{UG All Colleges 3.1} {INT 01} {C1.3}'")
print("- F_UA1_FEB_MBA_Aryan v1.4 -> matched with LMS 'F_UA1_FEB_MBA_Aryan (INT 01)_ 1.1'")
print("- UA_MBA_Website_Leads V1 -> matched with LMS 'UA_MBA_Website_Leads V1 (INT 01) C01'")
print("- IGNOU_Online_Courses_Admission_DFYD -> matched with LMS 'IGNOU_Online_Courses_Admission_DFYD_Delhi_NCR_Ad01' and 'IGNOU_Online_Courses_Admission_DFYD_Rest_Ad01'")
print("- Galgotias_Lead_2026 -> matched with LMS 'Galgotias_Leads_2026_P_Ad_01'")

print("\n2. Residual Meta Leads Distribution:")
print("- Leads in LMS tagged simply as 'M_P', 'M_F', or with 'utm_source=facebook/instagram' but lacking a specific campaign name.")
print("- These are pooled together and distributed proportionally across all active Meta ads based on their Panel Lead volume to ensure exact tracking correlation.")

print("\n3. Gap Enforcement:")
print("- After all direct and residual matches, the total LMS leads are scaled to exactly 88% of the Meta Panel Leads, maintaining a consistent ~12% gap as requested.")
