import os, sys, json, subprocess
import pandas as pd

GAPI_SCRIPT = '/home/hermeswebui/.hermes/skills/productivity/google-workspace/scripts/google_api.py'
if not os.path.exists(GAPI_SCRIPT):
    GAPI_SCRIPT = '/home/mohit/.hermes/skills/productivity/google-workspace/scripts/google_api.py'
SHEET_ID = '1QQ_Z50FDAhuBbVX5ioCjfgyFjfhr3y0gMGbQqteQ1f8'

def pnum(v):
    try:
        s=str(v).replace(',','').replace('₹','').strip()
        if s in ('','-','N/A','—','nan','None'):
            return 0.0
        return float(s)
    except Exception:
        return 0.0

def get(rng):
    cmd=[sys.executable,GAPI_SCRIPT,'sheets','get',SHEET_ID,rng]
    r=subprocess.run(cmd,capture_output=True,text=True,timeout=120)
    if r.returncode:
        print(r.stderr)
        raise SystemExit(1)
    return json.loads(r.stdout)

raw=get("'FFH " + chr(38) + " Above'!A1:Z5000")
df=pd.DataFrame(raw[1:], columns=[str(c).strip() for c in raw[0]])
for col in ['Form Date','Admission Date','Campaign Name','Student Name','Lead Id','Invoicing Variable','Fee Submitted','Total Variable']:
    if col not in df.columns:
        print('missing', col)
        print(df.columns.tolist())
        raise SystemExit(1)
df['F_Date']=pd.to_datetime(df['Form Date'],format='%d/%b/%Y',errors='coerce')
df['A_Date']=pd.to_datetime(df['Admission Date'],format='%d/%b/%Y',errors='coerce')
df['Inv']=df['Invoicing Variable'].apply(pnum)
may_start=pd.Timestamp('2026-05-01')
may_end=pd.Timestamp('2026-05-31')
form_may=df[(df.F_Date>=may_start)&(df.F_Date<=may_end)]
adm_may=df[(df.A_Date>=may_start)&(df.A_Date<=may_end)]
form_may_adm_any=form_may[form_may.A_Date.notna()]
form_may_adm_may=form_may[(form_may.A_Date>=may_start)&(form_may.A_Date<=may_end)]
same_day_may=df[(df.F_Date>=may_start)&(df.F_Date<=may_end)&(df.F_Date==df.A_Date)]
print('REGULAR MAY audit')
for name, sub in [
    ('Form Date May rows (FFH MTD)', form_may),
    ('Admission Date May rows (current full MTD admissions/inv)', adm_may),
    ('Form Date May + any Admission Date', form_may_adm_any),
    ('Form Date May + Admission Date May', form_may_adm_may),
    ('Same-day May admissions only', same_day_may),
]:
    print(f'{name}: rows={len(sub)} inv=₹{sub.Inv.sum():,.0f}')
print('\nAdmission Date May rows with Inv > 0:')
cols=['Form Date','Admission Date','Lead Id','Student Name','Campaign Name','Invoicing Variable','Inv']
print(adm_may[adm_may.Inv>0][cols].to_string(index=False))
print('\nForm Date May + Admission Date May rows with Inv > 0:')
print(form_may_adm_may[form_may_adm_may.Inv>0][cols].to_string(index=False))
