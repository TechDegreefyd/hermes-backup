import pandas as pd
import io
import re

raw_data = """
-- Online LMS
created_date	utm_campaign	lead_count
04-05-2026		38
04-05-2026	Galgotias_Leads_2026_P_Ad_01	28
04-05-2026	23349276370	28
04-05-2026	IGNOU_Online_Courses_Admission_DFYD_Delhi_NCR_Ad01	26
04-05-2026	IGNOU_Online_Courses_Admission_DFYD_Rest_Ad01	23
04-05-2026	F_UA1_FEB_MBA_Aryan (INT 01)_ 1.1	21
04-05-2026	23228113322	21
04-05-2026	UA_MBA_Website_Leads V1 (INT 01) C01	17
04-05-2026	F_UA01_{UG All Colleges 3.1} {INT 01} {C1.3}	17
04-05-2026	UA_MBA_Website_Leads V3 (INT 02) C02	10
04-05-2026	23463111599	4
04-05-2026	IGNOU_ONLINE_Degree_CR1	4
04-05-2026	LPU_Online_Alpha	3
04-05-2026	UG_Online_Admission_2026 _SF	3
04-05-2026	CU_Online_Admission_Delta	3
04-05-2026	UA_MBA_Website_Leads V3 (INT 03) C01	2
04-05-2026	G_P	2
04-05-2026	UA_MBA_Website_Leads V2 (INT 01) C01	1
04-05-2026	23486436393	1
04-05-2026	Ignou_Online_MBA_Ad1	1
04-05-2026	Panjab_Admissions	1

-- Regular LMS
04-05-2026	23463111599	65 
04-05-2026	Panjab_Admissions	34 
04-05-2026	23292287218	22 
04-05-2026		19 
04-05-2026	23748848361	19 
04-05-2026	LPU_Online_Alpha	19 
04-05-2026	23486436393	14 
04-05-2026	LPU_Online_Gamma	8 
04-05-2026	CU_Mohali_Int_ADG1_Ad01	7 
04-05-2026	CU_Lucknow_Int_ADG1_Ad01	6 
04-05-2026	CU_Online_Admission	5 
04-05-2026	Amity_University_Mumbai	4 
04-05-2026	Amity_University_Gwalior	3 
04-05-2026	CU_Lucknow_Rem_Ad01	3 
04-05-2026	UG_Online_Admission_2026 _SF	2 
04-05-2026	CU_Lucknow_Rem_Ad02	1 
04-05-2026	CU_Mohali_Rem_ADG1_Ad01	1 
04-05-2026	Amity_University_Lucknow	1 
04-05-2026	Harsh Test	1 
04-05-2026	Amity_University_Raipur	1 
04-05-2026	23486463996	1 
04-05-2026	LPU_Online_V1	1 
04-05-2026	136715f6-74bf-4285-8955-97ab04c0170d	1 
04-05-2026	Amity_University_Gurugram	1

-- Regular Amity LMS
04-05-2026	G_P	348
04-05-2026	S_P	200
04-05-2026	G_F	47
04-05-2026	23748848361	38
04-05-2026	M_F	13
04-05-2026	S_F	6
04-05-2026	C_F	5
04-05-2026		3
04-05-2026	Amity_University_Mumbai	2
04-05-2026	23349276370	2
04-05-2026	23228113322	2
04-05-2026	IGNOU_Online_Courses_Admission_DFYD_Rest_Ad01	1
04-05-2026	CGC_BTECH_REGU_Rem_SF_AD_01	1
04-05-2026	F_UA01_{UG All Colleges 3.1} {INT 01} {C1.3}	1
04-05-2026	Galgotias_Leads_2026_P_Ad_01	1
04-05-2026	23486436393	1

-- Regular CGC LMS
04-05-2026	CGC_Mohali	7
04-05-2026	23349276370	5
04-05-2026	Galgotias_Leads_2026_P_Ad_01	3
04-05-2026	CGC_BTECH_REGU_SF_CR2	3
04-05-2026	23463111599	2
04-05-2026	UG_Online_Admission_2026 _SF	2
04-05-2026	IGNOU_ONLINE_Degree_CR1	1
04-05-2026	CGC_BTECH_REGU_Rem_SF_AD_01	1
04-05-2026	F_UA01_{UG All Colleges 3.1} {INT 01} {C1.3}	1
04-05-2026	G_P	1
04-05-2026	Panjab_Admissions	1
"""

# Extract May 4th leads and sum by campaign
# Handle both campaign name and campaign ID (digits)
campaign_leads = {}

for line in raw_data.split('\n'):
    if '04-05-2026' in line:
        parts = re.split(r'\t| {2,}', line.strip())
        if len(parts) >= 2:
            # Format: date campaign count OR date count (if campaign empty)
            if len(parts) == 2:
                campaign = ""
                count = int(parts[1])
            else:
                campaign = parts[1].strip()
                count = int(parts[-1])
            
            if campaign not in campaign_leads:
                campaign_leads[campaign] = 0
            campaign_leads[campaign] += count

# Load Meta data
meta_df = pd.read_csv('meta_may4_full_corrected.csv')

# Account mapping
account_map = {
    '2276414612586714': 'Degreefyd_B',
    '771369141855853': 'DegreeFYD',
    '943943398169185': 'University_Admit_01'
}

# Distribute LMS leads to ads
# We'll map by Campaign name or ID
# Note: LMS sometimes uses numeric IDs for utm_campaign

# Create a mapping from campaign ID to name using the meta_insights_all_dates.csv if available
campaign_id_to_name = {}
try:
    all_meta = pd.read_csv('meta_insights_all_dates.csv')
    for _, r in all_meta.iterrows():
        campaign_id_to_name[str(r['campaign_id'])] = r['campaign_name']
except:
    pass

final_rows = []
# Map campaign leads to names
mapped_leads = {}
for camp, count in campaign_leads.items():
    name = campaign_id_to_name.get(camp, camp)
    if name not in mapped_leads:
        mapped_leads[name] = 0
    mapped_leads[name] += count

seen_campaigns = set()
for _, row in meta_df.iterrows():
    campaign = row['Campaign']
    lms_lead = 0
    if campaign in mapped_leads and campaign not in seen_campaigns:
        lms_lead = mapped_leads[campaign]
        seen_campaigns.add(campaign)
    
    final_rows.append({
        'Platform': row['Platform'],
        'Platform Type': 'Social', # Meta
        'Account': row['Account'],
        'Date': row['Date'],
        'Campaign': row['Campaign'],
        'Ad Name': row['Ad Name'],
        'Spends (₹)': row['Spends'],
        'Panel Leads': row['Pannel_Lead'],
        'LMS Leads': lms_lead
    })

# Add rows for campaigns present in LMS but missing in Meta (if any)
for camp, count in mapped_leads.items():
    if camp and camp not in seen_campaigns and count > 0:
        final_rows.append({
            'Platform': 'Facebook',
            'Platform Type': 'Social',
            'Account': 'Unknown',
            'Date': '2026-05-04',
            'Campaign': camp,
            'Ad Name': 'N/A',
            'Spends (₹)': 0,
            'Panel Leads': 0,
            'LMS Leads': count
        })

df = pd.DataFrame(final_rows)
df.to_csv('may4_reflection_final_v3.csv', index=False)
print(f"Generated may4_reflection_final_v3.csv with {sum(mapped_leads.values())} total LMS leads from user data.")
