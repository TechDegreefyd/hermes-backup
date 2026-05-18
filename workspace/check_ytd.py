import json
import pandas as pd
with open('ytd_sheet.json', 'r') as f:
    raw = json.load(f)
df = pd.DataFrame(raw[1:], columns=[str(c).strip() for c in raw[0]])
print("Columns:", df.columns)
print("Grand Total row:")
print(df[df[df.columns[0]] == 'Grand Total'])
