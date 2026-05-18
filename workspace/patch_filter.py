with open('/workspace/build_master_fixed.py', 'r') as f:
    content = f.read()

# Filter out rogue future dates!
logic_to_insert = """
if new_rows:
    df_full = pd.concat([df_full, pd.DataFrame(new_rows)], ignore_index=True)

# Drop any rogue future dates accidentally entered in the CRM that exceed the current CAC max date
df_full = df_full[df_full['Date_Parsed'] <= today]
"""

content = content.replace("if new_rows:\n    df_full = pd.concat([df_full, pd.DataFrame(new_rows)], ignore_index=True)", logic_to_insert)

with open('/workspace/build_master_fixed.py', 'w') as f:
    f.write(content)

