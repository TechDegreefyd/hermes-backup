import pandas as pd
df = pd.read_csv("lms_leads_activity_may3.csv")
print(df[df['source_db'] == 'regular_amity_lms'])
