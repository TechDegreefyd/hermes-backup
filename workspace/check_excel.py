import pandas as pd
import os

excel_path = "/home/mohit/workspace/Daily_Online_LMS_Reports_V2.xlsx"

def check_columns():
    with pd.ExcelFile(excel_path) as xls:
        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet)
            print(f"\nSheet: {sheet}")
            print(f"Columns: {df.columns.tolist()}")
            print(df.head(1))

if __name__ == "__main__":
    check_columns()
