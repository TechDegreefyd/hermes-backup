import pandas as pd
from hermes_tools import mcp_lms_db_send_whatsapp_text

df = pd.read_csv('may5_reflection_final.csv')
total_spends = df['Spends'].sum()
total_panel = df['Pannel_Lead'].sum()
total_lms = df['LMS Leads'].sum()

msg = f"*May 5th Reflection Update*\n\n" \
      f"Total Spends: ₹{total_spends:,.2f}\n" \
      f"Total Panel Leads: {total_panel}\n" \
      f"Total LMS Leads: {total_lms}\n\n" \
      f"Data has been synced to the Dashboard Sheet (May 5 Reflection)."

print(msg)
