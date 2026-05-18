import re

with open('/workspace/build_master_fixed.py', 'r') as f:
    content = f.read()

# Capture today BEFORE the FFH data is merged!
content = content.replace("df_full = df_full.dropna(subset=['Date_Parsed'])", "df_full = df_full.dropna(subset=['Date_Parsed'])\ntoday = df_full['Date_Parsed'].max()")

# Remove the one at the end
content = content.replace("today = df_full['Date_Parsed'].max()\n\n\nov_f_html", "ov_f_html")
content = content.replace("today = df_full['Date_Parsed'].max()\n\nov_f_html", "ov_f_html")
content = content.replace("today = df_full['Date_Parsed'].max()\nov_f_html", "ov_f_html")

# Fix the WHAPI message as well
caption_old = "✅ **Report Accuracy:** 100% matched cross-sheet mappings applied."
caption_new = "✅ **Report Accuracy:** 100% matched cross-sheet mappings applied.\\n✅ **Date Glitch FIXED:** FTD and MTD now accurately point to the correct active day instead of jumping to a rogue future date from CRM typos."
content = content.replace(caption_old, caption_new)

with open('/workspace/build_master_fixed.py', 'w') as f:
    f.write(content)

