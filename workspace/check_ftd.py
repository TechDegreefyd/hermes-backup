import json, pandas as pd

# Let's see what the current script outputs for FTD (May 4)
# Run the logic up to FTD table creation
with open('/workspace/build_master_fixed.py', 'r') as f:
    code = f.read()

# I want to extract the exact dataframe being used for FTD.
# Let's just print df_full[df_full['Date_Parsed'] == today] summary
print("Running check_ftd...")
