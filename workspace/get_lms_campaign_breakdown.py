import json
import pandas as pd
from hermes_tools import mcp_lms_db_run_select_query

# I'll query Online LMS and Regular LMS for a breakdown of leads by campaign name.
# I'll use the 'meta_ads_leads' table which usually contains the direct mapping.

def get_campaign_leads(db_name):
    query = """
    SELECT 
        COALESCE(m.campaign_name, 'Unknown') as campaign,
        COUNT(DISTINCT s.id) as lead_count
    FROM students s
    LEFT JOIN meta_ads_leads m ON s.id = m.student_id
    WHERE s.created_at::date = '2026-05-04'
    AND (s.source ILIKE '%facebook%' OR s.source ILIKE '%meta%' OR m.campaign_name IS NOT NULL)
    GROUP BY 1
    ORDER BY 2 DESC
    """
    res = mcp_lms_db_run_select_query(db_name=db_name, query=query)
    return res.get('rows', [])

# Run for Online and Regular
online_leads = get_campaign_leads('online_lms')
regular_leads = get_campaign_leads('regular_lms')

print("--- Online LMS Campaigns ---")
for row in online_leads:
    print(f"{row['campaign']}: {row['lead_count']}")

print("\n--- Regular LMS Campaigns ---")
for row in regular_leads:
    print(f"{row['campaign']}: {row['lead_count']}")

