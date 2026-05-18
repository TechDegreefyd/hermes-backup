import pandas as pd
import io

raw_text = """Meta Ads	FaceBook_Degreefyd_B	2026-05-03	CU_Lucknow_Remarketing	CU_Lucknow_Rem_Ad01	480.43	7	6
Meta Ads	FaceBook_Degreefyd_B	2026-05-03	CU_Lucknow_Int	CU_Lucknow_Int_ADG1_Ad01	431.68	4	4
Meta Ads	FaceBook_Degreefyd_B	2026-05-03	CU_Mohali_Int	CU_Mohali_Int_ADG1_Ad01	272.6	4	3
Meta Ads	FaceBook_Degreefyd_B	2026-05-03	CU_Mohali_Rem	CU_Mohali_Rem_ADG1_Ad01	222.35	3	3
Meta Ads	FaceBook_Degreefyd_B	2026-05-03	CU_Lucknow_Int	CU_Lucknow_Int_ADG1_Ad02	11.4	1	1
Meta Ads	FaceBook_Degreefyd_B	2026-05-03	CGC_BTECH_REGU_SF	CGC_BTECH_REGU_SF_CR2	369.02	1	2
Meta Ads	FaceBook_Degreefyd_B	2026-05-03	CGC_BTECH_REGU_Rem_SF	CGC_BTECH_REGU_Rem_SF_AD_01	419.23	1	1
Meta Ads	FaceBook_Degreefyd_B	2026-05-03	CGC_Landran_UG&PG_SF	CGC_Landran_UG&PG_SF_CR2	524.49	1	0
Meta Ads	FaceBook_Degreefyd_B	2026-05-03	CGC_Landran_UG&PG_SF	CGC_Landran_UG&PG_CR1	39.28	0	0
Meta Ads	FaceBook_Degreefyd_B	2026-05-03	CU_Mohali_Int	CU_Mohali_Int_ADG1_Ad02	34.48	0	0
Meta Ads	FaceBook_Degreefyd_B	2026-05-03	CU_Mohali_Rem	CU_Mohali_Rem_ADG1_Ad02	5.14	0	0
Meta Ads	FaceBook_Degreefyd_B	2026-05-04	CU_Mohali_Int	CU_Mohali_Int_ADG1_Ad01	390.23	7	7
Meta Ads	FaceBook_Degreefyd_B	2026-05-04	CU_Lucknow_Int	CU_Lucknow_Int_ADG1_Ad01	589.75	6	6
Meta Ads	FaceBook_Degreefyd_B	2026-05-04	CU_Lucknow_Remarketing	CU_Lucknow_Rem_Ad01	662.33	4	3
Meta Ads	FaceBook_Degreefyd_B	2026-05-04	CU_Lucknow_Remarketing	CU_Lucknow_Rem_Ad02	10.45	1	1
Meta Ads	FaceBook_Degreefyd_B	2026-05-04	CU_Mohali_Rem	CU_Mohali_Rem_ADG1_Ad01	260.96	1	1
Meta Ads	FaceBook_Degreefyd_B	2026-05-04	CGC_Landran_UG&PG_SF	CGC_Landran_UG&PG_CR1	28.36	0	0
Meta Ads	FaceBook_Degreefyd_B	2026-05-04	CGC_BTECH_REGU_SF	CGC_BTECH_REGU_SF_CR2	256.51	0	3
Meta Ads	FaceBook_Degreefyd_B	2026-05-04	CGC_BTECH_REGU_Rem_SF	CGC_BTECH_REGU_Rem_SF_AD_01	188.86	0	1
Meta Ads	FaceBook_Degreefyd_B	2026-05-04	CGC_Landran_UG&PG_SF	CGC_Landran_UG&PG_SF_CR2	304.03	0	0
Meta Ads	FaceBook_Degreefyd_B	2026-05-04	CU_Mohali_Int	CU_Mohali_Int_ADG1_Ad02	38.04	0	0
Meta Ads	FaceBook_Degreefyd_B	2026-05-04	CU_Mohali_Rem	CU_Mohali_Rem_ADG1_Ad02	4.56	0	0


Meta Ads	FaceBook_University_Admit	2026-05-03	F_UA01_{UG All Colleges V03.1}	F_UA01_{UG All Colleges 3.1} {INT 01} {C1.3}	1175.64	13	10
Meta Ads	FaceBook_University_Admit	2026-05-03	F_UA1_FEB_MBA_Aryan v1.4	F_UA1_FEB_MBA_Aryan (INT 01)_ 1.1	2218.66	31	28
Meta Ads	FaceBook_University_Admit	2026-05-03	F_UA1_FEB_MBA_Aryan_April_ V2	F_UA1_FEB_MBA_Aryan_April_ V2 (INT01) C02	0	1	0
Meta Ads	FaceBook_University_Admit	2026-05-03	UA_MBA_Website_Leads V1	UA_MBA_Website_Leads V1 (INT 01) C01	1188.67	5	7
Meta Ads	FaceBook_University_Admit	2026-05-03	UA_MBA_Website_Leads V1	UA_MBA_Website_Leads V1 (INT 01) C02	13.73	0	0
Meta Ads	FaceBook_University_Admit	2026-05-03	UA_MBA_Website_Leads V1	UA_MBA_Website_Leads V1(INT 01 ) C03	0.23	0	0
Meta Ads	FaceBook_University_Admit	2026-05-03	UA_MBA_Website_Leads V2	UA_MBA_Website_Leads V2 (INT 01) C01	436.12	0	2
Meta Ads	FaceBook_University_Admit	2026-05-03	UA_MBA_Website_Leads V3	UA_MBA_Website_Leads V3 (INT 01) C01	71.35	0	0
Meta Ads	FaceBook_University_Admit	2026-05-03	UA_MBA_Website_Leads V3	UA_MBA_Website_Leads V3 (INT 01) C02	138.53	1	1
Meta Ads	FaceBook_University_Admit	2026-05-03	UA_MBA_Website_Leads V3	UA_MBA_Website_Leads V3 (INT 01) C03	10.45	0	0
Meta Ads	FaceBook_University_Admit	2026-05-03	UA_MBA_Website_Leads V3	UA_MBA_Website_Leads V3 (INT 02) C01	66.8	0	0
Meta Ads	FaceBook_University_Admit	2026-05-03	UA_MBA_Website_Leads V3	UA_MBA_Website_Leads V3 (INT 02) C02	291.02	3	2
Meta Ads	FaceBook_University_Admit	2026-05-03	UA_MBA_Website_Leads V3	UA_MBA_Website_Leads V3 (INT 03) C01	475.17	1	1
Meta Ads	FaceBook_University_Admit	2026-05-03	UA_MBA_Website_Leads V3	UA_MBA_Website_Leads V3 (INT 03) C02	38.93	0	0
Meta Ads	FaceBook_University_Admit	2026-05-03	UA_MBA_Website_Leads V3	UA_MBA_Website_Leads V3 (INT 03) C03	39.05	0	0
Meta Ads	FaceBook_Degreefyd_B	2026-05-03	Galgotias_Lead_2026	Galgotias_Leads_2026_P_Ad_01	1332.35	27	23
Meta Ads	FaceBook_Degreefyd_B	2026-05-03	IGNOU_Online_Courses_Admission_DFYD	IGNOU_Online_Courses_Admission_DFYD_Rest_Ad01	366.42	22	21
Meta Ads	FaceBook_Degreefyd_B	2026-05-03	IGNOU_Online_Courses_Admission_DFYD	IGNOU_Online_Courses_Admission_DFYD_Delhi_NCR_Ad01	671.18	16	15
Meta Ads	FaceBook_Degreefyd_B	2026-05-03	IGNOU_ONLINE_DEGREE	IGNOU_ONLINE_Degree_CR1	641.68	9	11
Meta Ads	FaceBook_Degreefyd_B	2026-05-03	Ignou_Online_MBA	Ignou_Online_MBA_SF_Ad1	406.32	4	0
Meta Ads	FaceBook_Degreefyd_B	2026-05-03	Online_MBA_SF_G1	Online_MBA_SF_G1_CR1	67.85	1	0
Meta Ads	FaceBook_Degreefyd_B	2026-05-03	UG_Online_Admission_2026 _SF	UG_Online_Admission_SF_Ad_Set01_Ad02	357.66	1	3
Meta Ads	FaceBook_Degreefyd_B	2026-05-03	Online_MBA_SF_G1	Online_MBA_SF_G1_CR2	210.33	0	0
Meta Ads	FaceBook_Degreefyd_B	2026-05-03	UG_Online_Admission_2026 _SF	UG_Online_Admission_SF_Ad_Set01_Ad01	42.95	0	3"""

# Clean the raw text (handle multiple tabs and empty lines)
lines = [l.strip() for l in raw_text.split("\n") if l.strip()]
data = []
for l in lines:
    parts = l.split("\t")
    # Expected: Platform, Account, Date, Campaign, Ad Name, Spends, Panel, LMS
    # Fix Account names
    acc = parts[1].replace("FaceBook_", "").replace("FaceBook ", "")
    if acc == "University_Admit": acc = "University_Admit_01"
    
    # Pad if missing columns
    while len(parts) < 8:
        parts.append("0")
    
    # Handle empty numeric strings
    spends = parts[5] if parts[5] else "0"
    panel = parts[6] if parts[6] else "0"
    lms = parts[7] if parts[7] else "0"
    
    data.append({
        "Platform": "Meta",
        "Platform Type": "Lead Gen",
        "Account": acc,
        "Date": parts[2],
        "Campaign": parts[3],
        "Ad Name": parts[4],
        "Spends": float(spends),
        "Pannel_Lead": int(panel) if panel.isdigit() else 0,
        "lead_LMS": int(lms) if lms.isdigit() else 0
    })

df = pd.DataFrame(data)
df.to_csv("may3_marketing_raw_parsed.csv", index=False)
print(f"Parsed {len(df)} rows from marketing data.")
