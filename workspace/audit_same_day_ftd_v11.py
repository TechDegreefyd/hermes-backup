import json, subprocess, sys
import pandas as pd

GAPI_SCRIPT = '/home/hermeswebui/.hermes/skills/productivity/google-workspace/scripts/google_api.py'
import os
if not os.path.exists(GAPI_SCRIPT):
    GAPI_SCRIPT = '/home/mohit/.hermes/skills/productivity/google-workspace/scripts/google_api.py'

SHEETS = {
    'ONLINE': '1jzgnRxmmLIe_DAZ7nwHSRXeO6sI4CRxlTatc0T88ukY',
    'REGULAR': '1QQ_Z50FDAhuBbVX5ioCjfgyFjfhr3y0gMGbQqteQ1f8',
}

def pnum(v):
    try:
        s = str(v).replace(',', '').replace('₹', '').replace('%', '').strip()
        if s in ('', '-', 'N/A', '—'):
            return 0.0
        return float(s)
    except Exception:
        return 0.0

def get(sheet_id, rng):
    cmd = [sys.executable, GAPI_SCRIPT, 'sheets', 'get', sheet_id, rng]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if r.returncode:
        raise RuntimeError(r.stderr)
    return json.loads(r.stdout)

for label, sid in SHEETS.items():
    cac = get(sid, "'Day Wise CAC Report'!A1:S20000")
    df = pd.DataFrame(cac[2:], columns=[str(c).strip() for c in cac[1]])
    df['Date_Parsed'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date_Parsed'])
    df = df[df['Platform'].astype(str).str.strip() != '']
    today = df['Date_Parsed'].max().date()

    crm = get(sid, "'FFH " + chr(38) + " Above'!A1:Z5000")
    c = pd.DataFrame(crm[1:], columns=[str(x).strip() for x in crm[0]])
    c['F_Date'] = pd.to_datetime(c['Form Date'], format='%d/%b/%Y', errors='coerce')
    c['A_Date'] = pd.to_datetime(c['Admission Date'], format='%d/%b/%Y', errors='coerce')
    c['Inv_Val'] = c['Invoicing Variable'].apply(pnum)

    ftd_ffh = c[c['F_Date'].dt.date == today]
    same_day = c[(c['F_Date'].dt.date == today) & (c['A_Date'].dt.date == today)]
    old_today = c[(c['A_Date'].dt.date == today) & (c['F_Date'].dt.date != today)]
    print(f"{label} anchor {today}")
    print(f"  Raw FTD FFH (Form Date=today): {len(ftd_ffh)}")
    print(f"  Raw FTD ADM/Inv SAME-DAY ONLY (Form Date=today and Admission Date=today): {len(same_day)} | ₹{same_day['Inv_Val'].sum():,.0f}")
    print(f"  Old-pipeline admissions excluded from FTD (Admission Date=today but Form Date!=today): {len(old_today)} | ₹{old_today['Inv_Val'].sum():,.0f}")
