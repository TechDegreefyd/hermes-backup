import pandas as pd
import json
import os

def extract_online():
    path = '/workspace/Daily_Online_LMS_Reports_V2.xlsx'
    if not os.path.exists(path):
        return {}
    
    # Load sheets
    df_c_rev = pd.read_excel(path, sheet_name='Counsellor_Revenue')
    df_s_rev = pd.read_excel(path, sheet_name='Supervisor_Revenue')
    df_col = pd.read_excel(path, sheet_name='College_Performance')
    
    # Convert to dict, handle NaNs
    def clean_df(df):
        return df.where(pd.notnull(df), None).to_dict(orient='records')
    
    return {
        "counsellor_revenue": clean_df(df_c_rev),
        "supervisor_revenue": clean_df(df_s_rev),
        "college_performance": clean_df(df_col)
    }

def extract_regular():
    path = '/workspace/Daily_Regular_LMS_Reports.xlsx'
    if not os.path.exists(path):
        return {}
    
    df_adm = pd.read_excel(path, sheet_name='Admissions Data')
    df_form = pd.read_excel(path, sheet_name='Forms Data')
    
    def clean_df(df):
        return df.where(pd.notnull(df), None).to_dict(orient='records')
    
    return {
        "admissions": clean_df(df_adm),
        "forms": clean_df(df_form)
    }

def main():
    data = {
        "online": extract_online(),
        "regular": extract_regular()
    }
    
    with open('/workspace/full_report_data.json', 'w') as f:
        json.dump(data, f, indent=2)
    print("full_report_data.json updated successfully.")

if __name__ == "__main__":
    main()
