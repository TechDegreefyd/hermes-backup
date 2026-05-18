import json
import pandas as pd
from hermes_tools import mcp_lms_db_run_select_query

def get_leads(db_name):
    query = """
    SELECT 
        first_source_url as campaign,
        COUNT(DISTINCT student_id) as lead_count
    FROM students 
    WHERE created_at >= '2026-05-04 00:00:00+05:30' AND created_at < '2026-05-05 00:00:00+05:30'
    AND (source ILIKE '%facebook%' OR source ILIKE '%meta%')
    GROUP BY 1
    ORDER BY 2 DESC
    """
    res = mcp_lms_db_run_select_query(db_name=db_name, query=query)
    return res.get('rows', [])

online_leads = get_leads('online_lms')
regular_leads = get_leads('regular_lms')

# Format results for comparison
print("--- Corrected LMS Lead Counts by Campaign (first_source_url) ---")
all_leads = []
for row in online_leads:
    all_leads.append({'DB': 'Online', 'Campaign': row['campaign'], 'Leads': row['lead_count']})
for row in regular_leads:
    all_leads.append({'DB': 'Regular', 'Campaign': row['campaign'], 'Leads': row['lead_count']})

df = pd.DataFrame(all_leads)
print(df.to_string(index=False))
