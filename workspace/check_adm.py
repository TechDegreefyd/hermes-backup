import json
import pandas as pd

def pnum(v):
    try:
        s = str(v).replace(',', '').strip().replace('%', '').replace('₹', '')
        if s == '-' or s == '' or s == 'N/A' or s == '\u2014': return 0.0
        return float(s)
    except: return 0.0

with open('latest_cac.json', 'r') as f:
    raw = json.load(f)

df = pd.DataFrame(raw[2:], columns=[str(c).strip() for c in raw[1]])
df['Adm_num'] = df['Adm'].apply(pnum)
print("Total Adm in sheet:", df['Adm_num'].sum())

df['Date_Parsed'] = pd.to_datetime(df['Date'], errors='coerce')
print("Total Adm (valid dates):", df[df['Date_Parsed'].notnull()]['Adm_num'].sum())
print("Total Adm (null dates):", df[df['Date_Parsed'].isnull()]['Adm_num'].sum())

print("Min date:", df['Date_Parsed'].min(), "Max date:", df['Date_Parsed'].max())

print("\nMissing from YTD 2026:")
ytd_mask = df['Date_Parsed'] >= pd.to_datetime('2026-01-01')
print("Total Adm (YTD 2026):", df[ytd_mask]['Adm_num'].sum())

