import pandas as pd

df = pd.read_csv("may3_reflection_final_distributed_v4.csv")
total_spend = df['Spends'].sum()
total_panel = df['Pannel_Lead'].sum()
total_lms = df['lead_LMS'].sum()

summary = f"""*May 3rd Corrected Reflection Summary*
Total Spend: ₹{total_spend:,.2f}
Total Panel Leads: {total_panel}
Total LMS Leads: {total_lms}

*Breakdown by Account:*
"""
for acc in df['Account'].unique():
    acc_df = df[df['Account'] == acc]
    summary += f"- {acc}: ₹{acc_df['Spends'].sum():,.2f} | Panel: {acc_df['Pannel_Lead'].sum()} | LMS: {acc_df['lead_LMS'].sum()}\n"

print(summary)
