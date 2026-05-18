import pandas as pd
df_lms = pd.read_csv("lms_leads_activity_may3.csv")
# Logic from the script
def is_numeric(s):
    try:
        float(s)
        return True
    except:
        return False

meta_related = df_lms[df_lms['utm_campaign'].apply(lambda x: 
    is_numeric(str(x)) or 
    any(k in str(x) for k in ['FaceBook', 'Meta', 'UA', 'F_UA', 'DegreeFyd'])
)]
print(f"Total Meta-related lead count (Activity): {meta_related['lead_count'].sum()}")
print("Top Meta-related campaigns:")
print(meta_related.sort_values('lead_count', ascending=False).head(10))

print("\nNon-Meta campaigns:")
non_meta = df_lms[~df_lms['utm_campaign'].isin(meta_related['utm_campaign'])]
print(non_meta.sort_values('lead_count', ascending=False).head(10))
