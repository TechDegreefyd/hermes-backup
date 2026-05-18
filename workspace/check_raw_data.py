import pandas as pd
df = pd.read_csv('meta_may4_final.csv')
print("--- Raw Meta API Data (May 4th) ---")
print(df[['Account', 'Campaign', 'Ad Name', 'Spends', 'Pannel_Lead']])
