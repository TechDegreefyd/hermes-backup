import pandas as pd
import sys
import json
import os

def extract_totals(file_path):
    if not os.path.exists(file_path):
        return None
    
    try:
        # Load the Supervisor_Revenue sheet as it has the clearest totals
        df = pd.read_excel(file_path, sheet_name='Supervisor_Revenue')
        # Find the Grand Total row
        total_row = df[df.iloc[:, 0] == 'Grand Total']
        
        # Also get admissions from Counsellor_Admission sheet
        df_adm = pd.read_excel(file_path, sheet_name='Counsellor_Admission')
        adm_total_row = df_adm[df_adm.iloc[:, 0] == 'Grand Total']
        
        if not total_row.empty:
            return {
                "target": float(total_row['Target'].values[0]),
                "revenue_achieved": float(total_row['Achieved'].values[0]),
                "revenue_ftd": float(total_row['FTD'].values[0]),
                "admissions_total": int(adm_total_row['Achieve'].values[0]) if not adm_total_row.empty else 0,
                "admissions_ftd": int(adm_total_row['FTD'].values[0]) if not adm_total_row.empty else 0
            }
    except Exception as e:
        return {"error": str(e)}
    return None

if __name__ == "__main__":
    result = {
        "current": extract_totals('/workspace/Daily_Online_LMS_Reports_V2.xlsx'),
        "previous": extract_totals('/workspace/Daily_Online_LMS_Reports_Prev.xlsx')
    }
    print(json.dumps(result, indent=2))
