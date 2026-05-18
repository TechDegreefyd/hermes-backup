import pandas as pd
import json
import os

def get_regular_forms():
    path = 'Daily_Regular_LMS_Reports.xlsx'
    if not os.path.exists(path):
        return {"error": "File not found"}
    try:
        # Load all sheets to see what's inside
        xls = pd.ExcelFile(path)
        if 'Forms Data' not in xls.sheet_names:
            return {"error": f"Sheet 'Forms Data' not found. Available: {xls.sheet_names}"}
            
        df = pd.read_excel(path, sheet_name='Forms Data')
        # Print columns to debug
        cols = df.columns.tolist()
        
        # Look for FTD Ach, MTD Ach (or Apr Ach), YTD Ach
        res = {"columns": cols}
        
        # We need a summary: College, FTD Ach, MTD Ach
        # The MTD column for April is likely 'Apr Ach'
        summary_cols = ['College']
        if 'FTD Ach' in df.columns: summary_cols.append('FTD Ach')
        if 'Apr Ach' in df.columns: summary_cols.append('Apr Ach')
        if 'YTD Ach' in df.columns: summary_cols.append('YTD Ach')
        
        res['data'] = df[summary_cols].to_dict(orient='records')
        return res
    except Exception as e:
        return {"error": str(e)}

print(json.dumps(get_regular_forms(), indent=2))
