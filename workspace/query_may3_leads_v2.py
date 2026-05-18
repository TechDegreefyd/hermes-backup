from hermes_tools import mcp_lms_db_run_select_query
import pandas as pd
import json

dbs = ["online_lms", "regular_lms", "regular_cgc_lms", "regular_amity_lms"]
date = "2026-05-03"
all_leads = []

query = f"""
SELECT 
    DATE(created_at) as created_date,
    utm_campaign,
    COUNT(*) as lead_count
FROM students
WHERE DATE(created_at) = '{date}'
GROUP BY 1, 2
"""

for db in dbs:
    try:
        res = mcp_lms_db_run_select_query(db_name=db, query=query)
        # Handle list of dicts from MCP
        if isinstance(res, list):
            for row in res:
                row['source_db'] = db
                all_leads.append(row)
        elif isinstance(res, dict) and 'rows' in res:
             for row in res['rows']:
                row['source_db'] = db
                all_leads.append(row)
    except Exception as e:
        print(f"Error querying {db}: {e}")

df = pd.DataFrame(all_leads)
df.to_csv("lms_leads_may3_detailed.csv", index=False)
print(f"Found {df['lead_count'].sum() if not df.empty else 0} leads for May 3rd.")
