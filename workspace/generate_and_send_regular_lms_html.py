import os, base64, time, html
from datetime import datetime, timedelta
import pandas as pd
import requests
from dotenv import load_dotenv

BASE_DIR='.'
load_dotenv(os.path.join(BASE_DIR,'.env'))
WHAPI_TOKEN=os.getenv('WHAPI_TOKEN')
WHATSAPP_GROUP=os.getenv('WHATSAPP_GROUP','120363426619711887@g.us')
EXCEL=os.path.join(BASE_DIR,'Daily_Regular_LMS_Reports.xlsx')
OUT=os.path.join(BASE_DIR,'Degreefyd_Regular_LMS_HTML_Report.html')
now_ist=datetime.utcnow()+timedelta(hours=5,minutes=30)
report_date=now_ist-timedelta(days=1) if now_ist.hour<6 else now_ist
month_label=report_date.strftime('%B %Y')
month_short=report_date.strftime('%b')
xl=pd.ExcelFile(EXCEL)
adm=xl.parse('Admissions Data')
forms=xl.parse('Forms Data')

def esc(v): return html.escape(str(v))
def n(v):
    try:
        if pd.isna(v): return '—'
        return f'{int(float(v)):,}'
    except Exception: return esc(v)
def pv(x):
    text=str(x)
    try:
        if '/' in text:
            a,t=text.split('/',1)
            a=float(a.replace(',','').strip() or 0); t=float(t.replace(',','').strip() or 0)
            return (a/t*100) if t else 0.0
        return float(text.replace('%',''))
    except Exception: return 0.0
def pc(p):
    p=pv(p)
    if p>=100: return 'green'
    if p>=70: return 'amber'
    return 'red'
def pill(p): return f'<span class="pct {pc(p)}">{pv(p):.1f}%</span>'
def row_html(r):
    college=str(r['College'])
    grand=college.lower()=='total'
    name_map={'Chandigarh University, Mohali':'CU','Lovely Professional University':'LPU','Chandigarh University, Lucknow':'CU Lucknow','Chandigarh Group of Colleges, Landran (CGC)':'Landran','Amity University (All Campuses)':'Amity'}
    name='⬟ Total' if grand else name_map.get(college,college)
    cls='total-row' if grand else ''
    vals=[r.iloc[i] for i in range(1,11)]
    return f'<tr class="{cls}"><td class="college-name {"bold" if grand else ""}">{esc(name)}</td><td class="num ytd">{n(vals[0])}</td><td class="num">{n(vals[1])}</td><td class="num">{n(vals[2])}</td><td>{pill(vals[3])}</td><td class="num">{n(vals[4])}</td><td class="num">{n(vals[5])}</td><td>{pill(vals[6])}</td><td class="num">{n(vals[7])}</td><td class="num">{n(vals[8])}</td><td>{pill(vals[9])}</td></tr>'
def rows(df): return '\n'.join(row_html(r) for _,r in df.iterrows())

def total(df): return df.iloc[-1]
admt=total(adm); formt=total(forms)
CSS=r'''
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}:root{--white:#fff;--off:#f8f8f6;--border:#e8e4dc;--border-dark:#c8c0b4;--ink:#1a1a18;--ink-mid:#555550;--ink-light:#9a9590;--gold:#c8a84b;--gold-light:#f5ecd4;--green:#2d7a4f;--green-bg:#e8f5ee;--amber:#b86e1c;--amber-bg:#fdf3e4;--red:#c0392b;--red-bg:#fdecea;--blue:#1a4a8a;--blue-bg:#e8eef7;--radius:3px}body{background:var(--white);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;color:var(--ink);min-height:100vh}#tab-admissions,#tab-forms{display:none}.shell{max-width:900px;margin:0 auto;padding:0 16px 40px}.header{padding:28px 0 20px;border-bottom:2px solid var(--ink);margin-bottom:24px}.header-top{display:flex;align-items:flex-end;justify-content:space-between;flex-wrap:wrap;gap:8px}.brand{font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:var(--ink-light);margin-bottom:6px}.title{font-size:clamp(22px,5vw,32px);font-weight:400;letter-spacing:-.01em;line-height:1.1;color:var(--ink)}.header-meta{text-align:right}.badge{display:inline-block;background:var(--gold);color:var(--white);font-size:9px;letter-spacing:.14em;text-transform:uppercase;padding:3px 8px;border-radius:var(--radius);margin-bottom:4px}.date{font-size:12px;color:var(--ink-light);letter-spacing:.04em}.tabs{display:flex;gap:0;margin-bottom:24px;border:1.5px solid var(--border-dark);border-radius:var(--radius);overflow:hidden}.tab-label{flex:1;display:flex;align-items:center;justify-content:center;gap:8px;padding:12px 16px;cursor:pointer;font-size:13px;letter-spacing:.08em;text-transform:uppercase;color:var(--ink-mid);background:var(--off);user-select:none;-webkit-tap-highlight-color:transparent}.tab-label:first-of-type{border-right:1.5px solid var(--border-dark)}#tab-admissions:checked~.shell .tab-label[for=tab-admissions],#tab-forms:checked~.shell .tab-label[for=tab-forms]{background:var(--ink);color:var(--white)}.panel{display:none}#tab-admissions:checked~.shell #panel-admissions,#tab-forms:checked~.shell #panel-forms{display:block}.kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:24px}.kpi{background:var(--off);border:1px solid var(--border);border-radius:var(--radius);padding:14px 14px 12px}.kpi-label{font-size:9px;letter-spacing:.16em;text-transform:uppercase;color:var(--ink-light);margin-bottom:6px}.kpi-value{font-size:clamp(22px,5vw,30px);font-weight:400;line-height:1;color:var(--ink)}.kpi-sub{font-size:11px;color:var(--ink-light);margin-top:4px}.green{color:var(--green)}.amber{color:var(--amber)}.red{color:var(--red)}.section-label{display:flex;align-items:center;gap:12px;margin-bottom:14px}.section-label span{font-size:10px;letter-spacing:.16em;text-transform:uppercase;color:var(--ink-light);white-space:nowrap}.section-label:after{content:'';flex:1;height:1px;background:var(--border)}.table-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch;border:1px solid var(--border);border-radius:var(--radius);margin-bottom:20px}table{width:100%;border-collapse:collapse;font-size:13px;min-width:680px}thead tr{background:var(--ink)}th{padding:12px;text-align:left;font-size:9px;letter-spacing:.14em;text-transform:uppercase;color:rgba(255,255,255,.7);font-weight:400;white-space:nowrap}th:first-child{color:#fff}th:not(:first-child){text-align:center}.th-group{background:#2a2a28;color:rgba(255,255,255,.45)!important;font-size:8px!important;letter-spacing:.18em!important;padding:5px 12px!important;border-bottom:1px solid rgba(255,255,255,.08)}tbody tr{border-bottom:1px solid var(--border);background:var(--white)}tbody tr:nth-child(even){background:var(--off)}tbody tr.total-row{background:var(--gold-light)!important;border-top:2px solid var(--gold);border-bottom:2px solid var(--gold)}td{padding:11px 12px;color:var(--ink);text-align:center;vertical-align:middle}td:first-child{text-align:left;font-size:13px;color:var(--ink);max-width:200px}td.college-name{text-align:left;color:var(--ink);line-height:1.35}td.college-name.bold{font-style:normal;font-weight:600;color:var(--ink)}td.num{font-variant-numeric:tabular-nums;letter-spacing:.02em}.pct{display:inline-block;padding:2px 7px;border-radius:20px;font-size:12px;font-weight:600;letter-spacing:.01em}.pct.green{background:var(--green-bg);color:var(--green)}.pct.amber{background:var(--amber-bg);color:var(--amber)}.pct.red{background:var(--red-bg);color:var(--red)}td.ytd{font-weight:600;color:var(--blue);background:var(--blue-bg)}tr.total-row td.ytd{background:rgba(26,74,138,.1)}.legend{display:flex;gap:18px;flex-wrap:wrap;margin-bottom:28px;padding:12px 16px;background:var(--off);border:1px solid var(--border);border-radius:var(--radius)}.legend-item{display:flex;align-items:center;gap:6px;font-size:11px;color:var(--ink-mid)}.dot{width:8px;height:8px;border-radius:50%;display:inline-block}.dot.green{background:var(--green)}.dot.amber{background:var(--amber)}.dot.red{background:var(--red)}.footer{border-top:1px solid var(--border);padding-top:16px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px}.footer-note{font-size:11px;color:var(--ink-light)}.footer-brand{font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--border-dark)}@media(max-width:600px){.kpis{grid-template-columns:repeat(3,1fr);gap:8px}.kpi{padding:10px 10px 8px}.kpi-value{font-size:20px}th,td{padding:9px 8px;font-size:12px}.tab-label{font-size:11px;padding:10px}}
'''
html_doc=f'''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Regular Admissions Dashboard</title><style>{CSS}</style></head><body><input type="radio" name="view" id="tab-admissions" checked><input type="radio" name="view" id="tab-forms"><div class="shell"><header class="header"><div class="header-top"><div><div class="brand">Performance Intelligence</div><h1 class="title">Regular Admissions &amp; Forms Tracker</h1></div><div class="header-meta"><div class="badge">Live Report</div><div class="date">{month_label} · FTD {report_date.strftime('%d %b')}</div></div></div></header><div class="tabs"><label class="tab-label" for="tab-admissions">🎓 Admissions</label><label class="tab-label" for="tab-forms">📋 Forms</label></div>
<section class="panel" id="panel-admissions"><div class="kpis"><div class="kpi"><div class="kpi-label">YTD Total</div><div class="kpi-value">{n(admt['YTD Ach'])}</div><div class="kpi-sub">Admissions</div></div><div class="kpi"><div class="kpi-label">{month_short} Ach %</div><div class="kpi-value {pc(admt.iloc[4])}">{pv(admt.iloc[4]):.1f}%</div><div class="kpi-ratio" style="font-size:11px;opacity:0.8">{admt.iloc[3]}/{admt.iloc[2]}</div><div class="kpi-sub">vs {n(admt.iloc[2])} target</div></div><div class="kpi"><div class="kpi-label">Week Ach %</div><div class="kpi-value {pc(admt.iloc[7])}">{pv(admt.iloc[7]):.1f}%</div><div class="kpi-ratio" style="font-size:11px;opacity:0.8">{admt.iloc[6]}/{admt.iloc[5]}</div><div class="kpi-sub">{n(admt.iloc[6])} of {n(admt.iloc[5])}</div></div></div><div class="section-label"><span>College-wise Breakdown</span></div><div class="table-wrap"><table><thead><tr><th rowspan="2" style="width:30%;vertical-align:middle;border-right:1px solid rgba(255,255,255,.12)">College</th><th rowspan="2" style="vertical-align:middle;color:rgba(255,255,255,.9);border-right:1px solid rgba(255,255,255,.12)">YTD</th><th colspan="3" class="th-group">{month_short}</th><th colspan="3" class="th-group">Week</th><th colspan="3" class="th-group">FTD</th></tr><tr><th>Target</th><th>Ach</th><th>Ach %</th><th>Target</th><th>Ach</th><th>Ach %</th><th>Target</th><th>Ach</th><th>Ach %</th></tr></thead><tbody>{rows(adm)}</tbody></table></div><div class="legend"><div class="legend-item"><span class="dot green"></span> ≥ 100% — Exceeding</div><div class="legend-item"><span class="dot amber"></span> 70–99% — On Track</div><div class="legend-item"><span class="dot red"></span> &lt; 70% — Needs Attention</div></div></section>
<section class="panel" id="panel-forms"><div class="kpis"><div class="kpi"><div class="kpi-label">YTD Total</div><div class="kpi-value">{n(formt['YTD Ach'])}</div><div class="kpi-sub">Forms</div></div><div class="kpi"><div class="kpi-label">{month_short} Ach %</div><div class="kpi-value {pc(formt.iloc[4])}">{pv(formt.iloc[4]):.1f}%</div><div class="kpi-ratio" style="font-size:11px;opacity:0.8">{formt.iloc[3]}/{formt.iloc[2]}</div><div class="kpi-sub">vs {n(formt.iloc[2])} target</div></div><div class="kpi"><div class="kpi-label">Week Ach %</div><div class="kpi-value {pc(formt.iloc[7])}">{pv(formt.iloc[7]):.1f}%</div><div class="kpi-ratio" style="font-size:11px;opacity:0.8">{formt.iloc[6]}/{formt.iloc[5]}</div><div class="kpi-sub">{n(formt.iloc[6])} of {n(formt.iloc[5])}</div></div></div><div class="section-label"><span>College-wise Breakdown</span></div><div class="table-wrap"><table><thead><tr><th rowspan="2" style="width:30%;vertical-align:middle;border-right:1px solid rgba(255,255,255,.12)">College</th><th rowspan="2" style="vertical-align:middle;color:rgba(255,255,255,.9);border-right:1px solid rgba(255,255,255,.12)">YTD</th><th colspan="3" class="th-group">{month_short}</th><th colspan="3" class="th-group">Week</th><th colspan="3" class="th-group">FTD</th></tr><tr><th>Target</th><th>Ach</th><th>Ach %</th><th>Target</th><th>Ach</th><th>Ach %</th><th>Target</th><th>Ach</th><th>Ach %</th></tr></thead><tbody>{rows(forms)}</tbody></table></div><div class="legend"><div class="legend-item"><span class="dot green"></span> ≥ 100% — Exceeding</div><div class="legend-item"><span class="dot amber"></span> 70–99% — On Track</div><div class="legend-item"><span class="dot red"></span> &lt; 70% — Needs Attention</div></div></section><footer class="footer"><div class="footer-note">Percentages show achievement vs target. Ratios shown in KPIs. FTD = For The Day.</div><div class="footer-brand">Regular · Performance · {month_label}</div></footer></div></body></html>'''
with open(OUT,'w',encoding='utf-8-sig') as f:f.write(html_doc)
print(f'Generated HTML report at {OUT}')

def send(path):
    if not WHAPI_TOKEN: raise RuntimeError('WHAPI_TOKEN missing')
    with open(path,'rb') as f:b64=base64.b64encode(f.read()).decode('utf-8')
    headers={'accept':'application/json','authorization':f'Bearer {WHAPI_TOKEN}','content-type':'application/json'}
    payload={'to':WHATSAPP_GROUP,'media':f'data:text/html;name={os.path.basename(path)};base64,{b64}','caption':'📊 *Interactive Regular LMS HTML Report*\nMay college targets updated. Short college names used.'}
    last=None
    for i in range(3):
        try:
            r=requests.post('https://gate.whapi.cloud/messages/document',headers=headers,json=payload,timeout=30)
            print('Status:',r.status_code); print('Response:',r.text[:500])
            if 200<=r.status_code<300:return
            last=r.text
        except Exception as e:last=str(e);print('Attempt failed:',last);time.sleep(2)
    raise RuntimeError(f'WHAPI send failed: {last}')
if os.getenv('SKIP_SEND','0')!='1':send(OUT)
