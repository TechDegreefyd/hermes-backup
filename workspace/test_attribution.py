import json, pandas as pd

df_ffh = pd.DataFrame(json.load(open('/workspace/ffh_full.json'))[1:], columns=[str(c).strip() for c in json.load(open('/workspace/ffh_full.json'))[0]])

# Parse dates
df_ffh['Form Date P'] = pd.to_datetime(df_ffh['Form Date'], format='%d/%b/%Y', errors='coerce')
df_ffh['Adm Date P'] = pd.to_datetime(df_ffh['Admission Date'], format='%d/%b/%Y', errors='coerce')

# Filter for May
may_forms = df_ffh[df_ffh['Form Date P'].dt.month == 5]
may_adms = df_ffh[df_ffh['Adm Date P'].dt.month == 5]

print("FFH (Forms) in May:", len(may_forms))
print("Admissions in May:", len(may_adms))

inv = pd.to_numeric(may_adms['Invoicing Variable'].replace(['', '-', 'N/A', ' '], '0'), errors='coerce').fillna(0)
print("Invoicing in May:", inv.sum())
print("Invoicing numbers in May:", inv[inv > 0].tolist())
