import pandas as pd
import json
import os

def get_online_forms():
    path = 'Daily_Online_LMS_Reports_V2.xlsx'
    if not os.path.exists(path):
        return {"error": "File not found"}
    try:
        # Load all sheets to see what's inside
        xls = pd.ExcelFile(path)
        summary = {}
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(path, sheet_name=sheet_name)
            # Find relevant columns
            # In Online reports, it's usually College-wise or Counselor-wise
            # Let's look for 'Forms' or 'FTD' or 'MTD'
            relevant_cols = [c for c in df.columns if 'Form' in str(c) or 'FTD' in str(c) or 'MTD' in str(c) or 'College' in str(c)]
            if relevant_cols:
                # Get the sum of achievements if possible, or just the whole table if small
                summary[sheet_name] = df[relevant_cols].to_dict(orient='records')
        return summary
    except Exception as e:
        return {"error": str(e)}

def get_regular_forms():
    path = 'Daily_Regular_LMS_Reports.xlsx'
    if not os.path.exists(path):
        return {"error": "File not found"}
    try:
        df = pd.read_excel(path, sheet_name='Forms Data')
        # Typical columns: College | YTD Ach | Apr Target | Apr Ach | Apr Ach % | Week Target | Week Ach | Week Ach % | FTD Target | FTD Ach | FTD Ach %
        summary = df[['College', 'FTD Ach', 'Apr Ach', 'Week Ach']].to_dict(orient='records')
        return summary
    except Exception as e:
        return {"error": str(e)}

result = {
    "online": get_online_forms(),
    "regular": get_regular_forms()
}

print(json.dumps(result, indent=2))
