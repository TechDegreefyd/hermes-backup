import pandas as pd

df = pd.read_csv("may3_marketing_raw_parsed.csv")
total_spend = df['Spends'].sum()
total_panel = df['Pannel_Lead'].sum()
total_lms = df['lead_LMS'].sum()

summary = f"""*May 3rd & 4th RAW Marketing Data Summary*
Total Rows: {len(df)}
Total Spend: ₹{total_spend:,.2f}
Total Panel Leads: {total_panel}
Total LMS Leads: {total_lms}

*Note:* This data was parsed directly from the raw text provided by Marketing.
"""
print(summary)
