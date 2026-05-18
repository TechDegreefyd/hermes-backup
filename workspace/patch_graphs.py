import re

with open('/workspace/build_master_fixed.py', 'r') as f:
    content = f.read()

# Fix create_trend_charts signature
old_func = """def create_trend_charts(df_full, platform_pattern, label):
    try:
        mask = df_full['Platform'].str.contains(platform_pattern, case=False, na=False)"""

new_func = """def create_trend_charts(df_full, pattern, label, col='Type'):
    try:
        mask = df_full[col].str.contains(pattern, case=False, na=False)"""
content = content.replace(old_func, new_func)

# Fix the calls
old_calls = "dl, dc = create_trend_charts(df_full, 'DSA', 'DSA'); bl, bc = create_trend_charts(df_full, 'Brand', 'Brand'); ml, mc = create_trend_charts(df_full, 'Meta', 'Meta Ads')"
new_calls = "dl, dc = create_trend_charts(df_full, 'DSA', 'DSA', 'Type'); bl, bc = create_trend_charts(df_full, 'Brand', 'Brand', 'Type'); ml, mc = create_trend_charts(df_full, 'Meta', 'Meta Ads', 'Platform')"
content = content.replace(old_calls, new_calls)

with open('/workspace/build_master_fixed.py', 'w') as f:
    f.write(content)

