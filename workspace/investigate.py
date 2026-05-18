import json, pandas as pd

ffh_raw = json.load(open('/workspace/ffh_raw.json'))
df_ffh = pd.DataFrame(ffh_raw[1:], columns=[str(c).strip() for c in ffh_raw[0]])

# Print rows that match the invoicing values
inv_vals = [11424, 48825, 54180, 4375, 54180, 18500, 27709.5, 26775, 17500, 17500, 58187.5, 73150]
inv_vals_str = [str(x) for x in inv_vals] + [str(int(x)) for x in inv_vals if int(x) == x]

print("Matches for these invoicing values in May:")
for idx, r in df_ffh.iterrows():
    val = str(r.get('Invoicing Variable', '')).strip()
    if val in inv_vals_str:
        print(f"Lead Date: {r.get('Lead Date')}, Form Date: {r.get('Form Date')}, Adm Date: {r.get('Admission Date')}, Inv: {val}")

