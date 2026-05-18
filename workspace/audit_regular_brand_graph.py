import os, sys, json, subprocess
import pandas as pd
GAPI_SCRIPT='/home/hermeswebui/.hermes/skills/productivity/google-workspace/scripts/google_api.py'
if not os.path.exists(GAPI_SCRIPT): GAPI_SCRIPT='/home/mohit/.hermes/skills/productivity/google-workspace/scripts/google_api.py'
SHEET_ID='1QQ_Z50FDAhuBbVX5ioCjfgyFjfhr3y0gMGbQqteQ1f8'
cmd=[sys.executable,GAPI_SCRIPT,'sheets','get',SHEET_ID,"'Day Wise CAC Report'!A1:S20000"]
r=subprocess.run(cmd,capture_output=True,text=True,timeout=120)
r.check_returncode()
raw=json.loads(r.stdout)
df=pd.DataFrame(raw[2:], columns=[str(c).strip() for c in raw[1]])
df['Date_Parsed']=pd.to_datetime(df['Date'],errors='coerce')
df=df.dropna(subset=['Date_Parsed'])
df=df[df['Platform'].astype(str).str.strip()!='']
for c in ['Spends','Pannel_Lead','Lead_LMS']:
    df[c]=pd.to_numeric(df[c].astype(str).str.replace(',',''),errors='coerce').fillna(0)
print('cols', df.columns.tolist())
print('rows', len(df), 'date', df.Date_Parsed.min().date(), df.Date_Parsed.max().date())
for col in ['Platform','Type','Account','Campaign','Ad Name']:
    if col in df.columns:
        vals=df[col].astype(str).fillna('')
        mask=vals.str.contains('brand|branded|search|generic|dsa', case=False, na=False, regex=True)
        print('\nCOL',col,'unique sample', vals.drop_duplicates().head(30).tolist())
        print('matches count', mask.sum())
        print(vals[mask].drop_duplicates().head(50).tolist())

def graph_count(pattern):
    masks=[]
    for col in ['Platform','Type','Account']:
        if col in df.columns:
            masks.append(df[col].astype(str).str.contains(pattern,case=False,na=False,regex=True))
    mask=masks[0]
    for m in masks[1:]: mask=mask|m
    sub=df[mask]
    daily=sub.groupby('Date_Parsed').agg(Spends=('Spends','sum'),PL=('Pannel_Lead','sum'),LL=('Lead_LMS','sum')).reset_index().sort_values('Date_Parsed') if not sub.empty else pd.DataFrame()
    if not daily.empty: daily=daily[(daily.PL>0)|(daily.Spends>0)].tail(10)
    print('\nPATTERN',pattern,'subrows',len(sub),'dailyrows',len(daily))
    if not daily.empty: print(daily.to_string(index=False))
for pat in ['Brand','brand|branded','Generic|DSA','Google']:
    graph_count(pat)
