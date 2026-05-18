import re

with open('/workspace/build_master_fixed.py', 'r') as f:
    content = f.read()

old_func = """def create_trend_charts(df_full, platform_pattern, label):
    try:
        mask = df_full['Platform'].str.contains(platform_pattern, case=False, na=False)"""

new_func = """def create_trend_charts(df_full, platform_pattern, label):
    try:
        mask1 = df_full['Platform'].str.contains(platform_pattern, case=False, na=False)
        mask2 = df_full['Type'].str.contains(platform_pattern, case=False, na=False)
        mask3 = df_full['Account'].str.contains(platform_pattern, case=False, na=False)
        mask = mask1 | mask2 | mask3"""

content = content.replace(old_func, new_func)

with open('/workspace/build_master_fixed.py', 'w') as f:
    f.write(content)

