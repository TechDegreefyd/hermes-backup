import json
import pandas as pd
with open('ytd_sheet.json', 'r') as f:
    raw = json.load(f)
df = pd.DataFrame(raw[1:], columns=[str(c).strip() for c in raw[0]])
gt = df[df[df.columns[0]] == 'Grand Total']
print("Grand Total ADM from 'Campaign Wise - YTD' sheet:", gt['ADM'].iloc[0] if not gt.empty else "Not found")
