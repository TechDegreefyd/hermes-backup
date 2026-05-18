import pandas as pd
from hermes_tools import mcp_lms_db_run_select_query

DATE = "2026-05-05"
queries = {
    "online_lms": f"SELECT first_source_url, count(*) as leads FROM students WHERE created_at::date = '{DATE}' GROUP BY 1",
    "regular_lms": f"SELECT first_source_url, count(*) as leads FROM students WHERE created_at::date = '{DATE}' GROUP BY 1",
    "regular_cgc_lms": f"SELECT first_source_url, count(*) as leads FROM students WHERE created_at::date = '{DATE}' GROUP BY 1",
    "regular_amity_lms": f"SELECT first_source_url, count(*) as leads FROM students WHERE created_at::date = '{DATE}' GROUP BY 1"
}

all_leads = []
for db, q in queries.items():
    res = mcp_lms_db_run_select_query(db_name=db, query=q)
    if "rows" in res:
        for row in res["rows"]:
            row["db"] = db
            all_leads.append(row)

pd.DataFrame(all_leads).to_csv("may5_lms_leads_raw.csv", index=False)
print("Saved May 5 LMS leads.")
