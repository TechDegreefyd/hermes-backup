import os, json, base64, time, html
from datetime import datetime, timedelta
import pandas as pd
import requests
from dotenv import load_dotenv

BASE_DIR = os.environ.get('WORKSPACE_DIR', '/home/mohit/workspace')
load_dotenv(os.path.join(BASE_DIR, '.env'))
WHAPI_TOKEN = os.getenv('WHAPI_TOKEN')
WHATSAPP_GROUP = os.getenv('WHATSAPP_GROUP', '120363426619711887@g.us')
CONFIG_FILE = os.path.join(BASE_DIR, 'report_config.json')
EXCEL = os.path.join(BASE_DIR, 'Daily_Online_LMS_Reports_V2.xlsx')
OUT = os.path.join(BASE_DIR, 'Degreefyd_Online_LMS_HTML_Report.html')

now_ist = datetime.utcnow() + timedelta(hours=5, minutes=30)
report_date = __import__('datetime').datetime.strptime('2026-05-10', '%Y-%m-%d')
month_label = 'May 2026'

with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    config = json.load(f)
adm_targets = config.get('supervisor_admission_targets', {})
display_to_key = {'Varun':'Varun','Sunil':'Sunil','Siddhartha':'Siddarth Kumar','Siddarth Kumar':'Siddarth Kumar','Vishal':'Vishal Gaur','Vishal Gaur':'Vishal Gaur'}

xl = pd.ExcelFile(EXCEL)
sup_rev = xl.parse('Supervisor_Fee_Collected')
c_rev = xl.parse('Counsellor_Fee_Collected')
sup_adm = xl.parse('Supervisor_Admission')
c_adm = xl.parse('Counsellor_Admission')
college = xl.parse('College_Performance')

def esc(v): return html.escape(str(v))
def money(v):
    try: v=float(v)
    except Exception: return '—'
    if v == 0: return '₹0'
    if abs(v) >= 100000: return f'₹{v/100000:.1f}L'.replace('.0L','L')
    return f'₹{v:,.0f}'
def money_full(v):
    try: return f'₹{float(v):,.0f}' if float(v) else '₹0'
    except Exception: return '—'
def num(v):
    try:
        if pd.isna(v) or float(v)==0: return '—'
        return f'{int(float(v)):,}'
    except Exception: return esc(v)
def pct_value(s):
    text = str(s)
    try:
        if '/' in text:
            a, t = text.split('/', 1)
            a = float(a.replace('₹','').replace(',','').strip() or 0)
            t = float(t.replace('₹','').replace(',','').strip() or 0)
            return (a/t*100) if t else 0.0
        return float(text.replace('%',''))
    except Exception: return 0.0
def ratio_text(a, t):
    return f"{money_full(a) if abs(float(a or 0)) >= 1000 or abs(float(t or 0)) >= 1000 else int(float(a or 0))}/{money_full(t) if abs(float(a or 0)) >= 1000 or abs(float(t or 0)) >= 1000 else int(float(t or 0))}"
def pct_class(p, zero=False):
    if zero: return 'zero'
    if p >= 100: return 'green'
    if p >= 70: return 'amber'
    if p >= 40: return 'orange'
    return 'red'
def pill(pct, zero=False):
    p = pct_value(pct)
    return f'<span class="pct {pct_class(p, zero)}">{esc(pct)}</span>'

def ratio_text_full(a, t):
    try:
        a_f = float(a or 0)
        t_f = float(t or 0)
        if abs(a_f) >= 100000 or abs(t_f) >= 100000:
            return f"{money(a_f).replace('₹','')}/{money(t_f).replace('₹','')}"
        return f"{int(a_f)}/{int(t_f)}"
    except: return f"{a}/{t}"

gt = sup_rev[sup_rev['Supervisor'].astype(str).str.contains('Grand Total', na=False)].iloc[0]
gt_adm = sup_adm[sup_adm['Supervisor'].astype(str).str.contains('Grand Total', na=False)].iloc[0]
total_adm_target = sum(adm_targets.values())
adm_ach_pct = (float(gt_adm['Achieve']) / total_adm_target * 100) if total_adm_target else 0

def supervisor_cards():
    out=[]
    for _, r in sup_rev[~sup_rev['Supervisor'].astype(str).str.contains('Grand Total', na=False)].iterrows():
        name=str(r['Supervisor']); key=display_to_key.get(name,name)
        arow = sup_adm[sup_adm['Supervisor'].astype(str)==name]
        ach_adm = int(arow.iloc[0]['Achieve']) if not arow.empty else 0
        ftd_adm = int(arow.iloc[0]['FTD']) if not arow.empty else 0
        p=pct_value(r['Ach %']); cls=pct_class(p)
        adm_t = adm_targets.get(key,0)
        adm_p = (ach_adm/adm_t*100) if adm_t else 0
        style = min(max(p,0),100)
        out.append(f'''<div class="sup-card {name.lower().split()[0]}"><div class="sup-name"><small>Team Owner</small>{esc(name)}</div>
        <div class="sup-row"><span class="sup-metric">Fee Collected</span><span class="sup-val">{money(r['Fee Collected'])} / {money(r['Target'])}</span></div>
        <div class="sup-row"><span class="sup-metric">Fee Ach %</span><span class="sup-val {cls}">{p:.1f}%</span><div class="sup-ratio">{ratio_text_full(r['Fee Collected'], r['Target'])}</div></div>
        <div class="sup-row"><span class="sup-metric">Admissions</span><span class="sup-val">{ach_adm}/{adm_t}</span></div>
        <div class="sup-row"><span class="sup-metric">FTD</span><span class="sup-val">{ftd_adm} adm · {money(r['FTD'])}</span></div>
        <div class="sup-bar-bg"><div class="sup-bar" style="width:{style}%"></div></div></div>''')
    return '\n'.join(out)

def sup_summary_rows():
    rows=[]
    for _, r in sup_rev.iterrows():
        grand = 'grand-total' if 'Grand Total' in str(r['Supervisor']) else ''
        name = str(r['Supervisor']); key=display_to_key.get(name,name)
        arow = sup_adm[sup_adm['Supervisor'].astype(str)==name]
        ach_adm = int(arow.iloc[0]['Achieve']) if not arow.empty else int(gt_adm['Achieve']) if grand else 0
        ftd_adm = int(arow.iloc[0]['FTD']) if not arow.empty else int(gt_adm['FTD']) if grand else 0
        adm_t = total_adm_target if grand else adm_targets.get(key,0)
        adm_p = (ach_adm/adm_t*100) if adm_t else 0
        rows.append(f'<tr class="{grand}"><td class="left bold">{"⬟ " if grand else ""}{esc(name)}</td><td>{adm_t}</td><td>{ach_adm}</td><td>{esc(f"{ach_adm}/{adm_t}")}</td><td class="rev">{money_full(r["Target"])}</td><td class="rev">{money_full(r["Fee Collected"])}</td><td>{pill(r["Ach %"], float(r["Target"] or 0)==0)}</td><td class="ftd">{money_full(r["FTD"])}</td><td>{ftd_adm}</td></tr>')
    return '\n'.join(rows)

def fee_collected_rows():
    rows=[]
    for sup in c_rev['Supervisor'].dropna().unique():
        if str(sup).startswith('Total') or str(sup)=='Grand Total': continue
        rows.append(f'<tr class="sup-header"><td colspan="5">👤 {esc(sup)} Team</td></tr>')
        sdf=c_rev[c_rev['Supervisor']==sup]
        for _, r in sdf.iterrows():
            is_total = str(r['Supervisor']).startswith('Total') or str(r['Counsellor'])==''
            cls='sub-total' if is_total else ''
            rows.append(f'<tr class="{cls}"><td class="left">{esc(r["Counsellor"])}</td><td class="rev">{money_full(r["Target"])}</td><td class="rev">{money_full(r["Fee Collected"])}</td><td>{pill(r["Ach %"], float(r["Target"] or 0)==0)}</td><td class="ftd">{money_full(r["FTD"])}</td></tr>')
        # append matching total row from excel if present
        totals=c_rev[c_rev['Supervisor'].astype(str).eq(f'Total ({sup})')]
        for _, r in totals.iterrows():
            rows.append(f'<tr class="sub-total"><td class="left bold">Total ({esc(sup)})</td><td class="rev">{money_full(r["Target"])}</td><td class="rev">{money_full(r["Fee Collected"])}</td><td>{pill(r["Ach %"], float(r["Target"] or 0)==0)}</td><td class="ftd">{money_full(r["FTD"])}</td></tr>')
    gr=c_rev[c_rev['Supervisor'].astype(str).eq('Grand Total')]
    for _, r in gr.iterrows(): rows.append(f'<tr class="grand-total"><td class="left bold">⬟ Grand Total</td><td class="rev">{money_full(r["Target"])}</td><td class="rev">{money_full(r["Fee Collected"])}</td><td>{pill(r["Ach %"])}</td><td class="ftd">{money_full(r["FTD"])}</td></tr>')
    return '\n'.join(rows)

def admission_rows():
    rows=[]
    for sup in c_adm['Supervisor'].dropna().unique():
        if str(sup).startswith('Total') or str(sup)=='Grand Total': continue
        rows.append(f'<tr class="sup-header"><td colspan="3">👤 {esc(sup)} Team</td></tr>')
        for _, r in c_adm[c_adm['Supervisor']==sup].iterrows():
            rows.append(f'<tr><td class="left">{esc(r["Counsellor"])}</td><td>{num(r["Achieve"])}</td><td class="ftd">{num(r["FTD"])}</td></tr>')
        totals=c_adm[c_adm['Supervisor'].astype(str).eq(f'Total ({sup})')]
        for _, r in totals.iterrows(): rows.append(f'<tr class="sub-total"><td class="left bold">Total ({esc(sup)})</td><td>{num(r["Achieve"])}</td><td class="ftd">{num(r["FTD"])}</td></tr>')
    gr=c_adm[c_adm['Supervisor'].astype(str).eq('Grand Total')]
    for _, r in gr.iterrows(): rows.append(f'<tr class="grand-total"><td class="left bold">⬟ Grand Total</td><td>{num(r["Achieve"])}</td><td class="ftd">{num(r["FTD"])}</td></tr>')
    return '\n'.join(rows)

def college_rows():
    rows=[]
    for _, r in college.iterrows():
        grand='grand-total' if str(r['Colleges']).lower()=='total' else ''
        rows.append(f'<tr class="{grand}"><td class="left bold">{"⬟ " if grand else ""}{esc(r["Colleges"])}</td><td class="ytd">{num(r["YTD Forms"])}</td><td class="ytd">{num(r["YTD Admissions"])}</td><td>{pill(r["YTD F2A %"])}</td><td>{num(r["MTD Forms"])}</td><td>{num(r["MTD Admissions"])}</td><td>{pill(r["MTD F2A %"])}</td><td>{num(r["FTD Forms"])}</td><td>{num(r["FTD Admissions"])}</td><td>{pill(r["FTD F2A %"])}</td></tr>')
    return '\n'.join(rows)

CSS = r'''
.sup-ratio, .kpi-ratio { font-size: 11px; opacity: 0.8; margin-top: 2px; font-weight: 400; }
.sup-val-ratio { font-size: 10px; display: block; opacity: 0.7; }
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}:root{--white:#fff;--off:#f8f8f6;--border:#e8e4dc;--border-dark:#c8c0b4;--ink:#1a1a18;--ink-mid:#555550;--ink-light:#9a9590;--gold:#c8a84b;--gold-light:#f5ecd4;--green:#2d7a4f;--green-bg:#e8f5ee;--amber:#b86e1c;--amber-bg:#fdf3e4;--orange:#c05e0a;--orange-bg:#fde8d4;--red:#c0392b;--red-bg:#fdecea;--gray:#888880;--gray-bg:#f0efec;--blue:#1a4a8a;--blue-bg:#e8eef7;--radius:3px}body{background:var(--white);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;color:var(--ink);min-height:100vh}#t1,#t2,#t3,#t4{display:none}.shell{max-width:960px;margin:0 auto;padding:0 14px 48px}.header{padding:26px 0 18px;border-bottom:2px solid var(--ink);margin-bottom:22px}.header-top{display:flex;align-items:flex-end;justify-content:space-between;flex-wrap:wrap;gap:8px}.brand{font-size:10px;letter-spacing:.18em;text-transform:uppercase;color:var(--ink-light);margin-bottom:5px}.title{font-size:clamp(20px,4.5vw,30px);font-weight:400;letter-spacing:-.01em;line-height:1.15}.header-meta{text-align:right}.badge{display:inline-block;background:var(--ink);color:var(--white);font-size:9px;letter-spacing:.14em;text-transform:uppercase;padding:3px 8px;border-radius:var(--radius);margin-bottom:4px}.date{font-size:11px;color:var(--ink-light);letter-spacing:.04em}.tabs{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:22px}.tab-label{display:flex;align-items:center;justify-content:center;gap:6px;padding:11px 10px;cursor:pointer;font-size:12px;letter-spacing:.07em;text-transform:uppercase;color:var(--ink-mid);background:var(--off);border:1.5px solid var(--border-dark);border-radius:var(--radius);user-select:none;-webkit-tap-highlight-color:transparent}#t1:checked~.shell label[for=t1],#t2:checked~.shell label[for=t2],#t3:checked~.shell label[for=t3],#t4:checked~.shell label[for=t4]{background:var(--ink);color:var(--white);border-color:var(--ink)}.panel{display:none}#t1:checked~.shell #p1,#t2:checked~.shell #p2,#t3:checked~.shell #p3,#t4:checked~.shell #p4{display:block}.kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:22px}.kpi{background:var(--off);border:1px solid var(--border);border-radius:var(--radius);padding:13px 12px 11px}.kpi-label{font-size:9px;letter-spacing:.16em;text-transform:uppercase;color:var(--ink-light);margin-bottom:5px}.kpi-value{font-size:clamp(18px,4vw,26px);font-weight:400;line-height:1;color:var(--ink)}.kpi-sub{font-size:10px;color:var(--ink-light);margin-top:4px}.green{color:var(--green)}.amber{color:var(--amber)}.red{color:var(--red)}.orange{color:var(--orange)}.slabel{display:flex;align-items:center;gap:10px;margin-bottom:12px;margin-top:20px}.slabel span{font-size:9px;letter-spacing:.16em;text-transform:uppercase;color:var(--ink-light);white-space:nowrap}.slabel:after{content:'';flex:1;height:1px;background:var(--border)}.table-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch;border:1px solid var(--border);border-radius:var(--radius);margin-bottom:16px}table{width:100%;border-collapse:collapse;font-size:12.5px}thead tr{background:var(--ink)}th{padding:11px;font-size:8.5px;letter-spacing:.13em;text-transform:uppercase;color:rgba(255,255,255,.65);font-weight:400;white-space:nowrap;text-align:center}th.left{text-align:left;color:rgba(255,255,255,.9)}tbody tr{border-bottom:1px solid var(--border);background:var(--white)}tbody tr:nth-child(even){background:var(--off)}tr.sup-header td{background:#2c2c2a;color:rgba(255,255,255,.55);font-size:9px;letter-spacing:.18em;text-transform:uppercase;padding:6px 11px;border-bottom:none}tr.sub-total{background:#f0ede6!important;border-top:1.5px solid var(--border-dark);border-bottom:1.5px solid var(--border-dark)}tr.sub-total td{font-weight:600}tr.grand-total{background:var(--gold-light)!important;border-top:2px solid var(--gold);border-bottom:2px solid var(--gold)}tr.grand-total td{font-weight:700}td{padding:10px 11px;text-align:center;vertical-align:middle;font-variant-numeric:tabular-nums}td.left{text-align:left}.bold{font-weight:600}td.ytd{color:var(--blue);font-weight:600;background:var(--blue-bg)}.pct{display:inline-block;padding:2px 6px;border-radius:20px;font-size:11px;font-weight:600;white-space:nowrap}.pct.green{background:var(--green-bg);color:var(--green)}.pct.amber{background:var(--amber-bg);color:var(--amber)}.pct.orange{background:var(--orange-bg);color:var(--orange)}.pct.red{background:var(--red-bg);color:var(--red)}.pct.zero{background:var(--gray-bg);color:var(--gray)}td.rev{font-size:12px;letter-spacing:-.01em}td.ftd{color:var(--green);font-weight:600}.sup-cards{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-bottom:22px}.sup-card{border:1.5px solid var(--border);border-top:3px solid var(--gold);border-radius:var(--radius);padding:14px;background:var(--white)}.sup-name{font-size:14px;font-weight:400;letter-spacing:.02em;margin-bottom:10px}.sup-name small{display:block;font-size:9px;letter-spacing:.14em;text-transform:uppercase;color:var(--ink-light);margin-bottom:2px}.sup-row{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px;gap:8px}.sup-metric{font-size:9px;letter-spacing:.12em;text-transform:uppercase;color:var(--ink-light)}.sup-val{font-size:16px;color:var(--ink);text-align:right}.sup-bar-bg{height:4px;background:var(--border);border-radius:2px;margin-top:8px;overflow:hidden}.sup-bar{height:100%;border-radius:2px;background:var(--gold)}.legend{display:flex;gap:14px;flex-wrap:wrap;margin-bottom:22px;padding:11px 14px;background:var(--off);border:1px solid var(--border);border-radius:var(--radius)}.legend-item{display:flex;align-items:center;gap:5px;font-size:10.5px;color:var(--ink-mid)}.footer{border-top:1px solid var(--border);padding-top:14px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;margin-top:8px}.footer-note{font-size:10.5px;color:var(--ink-light)}.footer-brand{font-size:9px;letter-spacing:.14em;text-transform:uppercase;color:var(--border-dark)}@media(max-width:540px){.kpis{grid-template-columns:repeat(3,1fr);gap:6px}.kpi{padding:9px 8px}.kpi-value{font-size:16px}.sup-cards{grid-template-columns:1fr 1fr;gap:8px}.sup-val{font-size:13px}th,td{padding:8px 7px;font-size:11px}table{min-width:560px}}
'''

html_doc = f'''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Online Admissions Dashboard</title><style>{CSS}</style></head><body>
<input type="radio" name="dash" id="t1" checked><input type="radio" name="dash" id="t2"><input type="radio" name="dash" id="t3"><input type="radio" name="dash" id="t4"><div class="shell"><header class="header"><div class="header-top"><div><div class="brand">Performance Intelligence · Online</div><h1 class="title">Online Admissions &amp;<br>Fee Collected Tracker</h1></div><div class="header-meta"><div class="badge">Live Report</div><div class="date">{month_label} · FTD {report_date.strftime('%d %b')}</div></div></div></header><div class="tabs"><label class="tab-label" for="t1">📊 Overview</label><label class="tab-label" for="t2">💰 Fee Collected</label><label class="tab-label" for="t3">🎓 Admissions</label><label class="tab-label" for="t4">🏫 Colleges</label></div>
<section class="panel" id="p1"><div class="kpis"><div class="kpi"><div class="kpi-label">Total Fee Collected</div><div class="kpi-value orange">{money(gt['Fee Collected'])}</div><div class="kpi-sub">of {money(gt['Target'])} target</div></div><div class="kpi"><div class="kpi-label">Fee Ach %</div><div class="kpi-value orange">{pct_value(gt['Ach %']):.1f}%</div><div class="kpi-ratio">{ratio_text_full(gt['Fee Collected'], gt['Target'])}</div><div class="kpi-sub">Grand Total</div></div><div class="kpi"><div class="kpi-label">Admissions</div><div class="kpi-value">{adm_ach_pct:.1f}%</div><div class="kpi-ratio">{int(gt_adm['Achieve'])}/{total_adm_target}</div><div class="kpi-sub">Grand Total</div></div></div><div class="slabel"><span>Team Owner Snapshot</span></div><div class="sup-cards">{supervisor_cards()}</div><div class="slabel"><span>Team Owner Summary Table</span></div><div class="table-wrap"><table><thead><tr><th class="left">Team Owner</th><th>Adm TG</th><th>Adm Ach</th><th>Adm %</th><th>Fee TG</th><th>Fee Ach</th><th>Fee Ach %</th><th>FTD Fee</th><th>FTD Adm</th></tr></thead><tbody>{sup_summary_rows()}</tbody></table></div></section>
<section class="panel" id="p2"><div class="kpis"><div class="kpi"><div class="kpi-label">Fee Target</div><div class="kpi-value">{money(gt['Target'])}</div><div class="kpi-sub">{month_label}</div></div><div class="kpi"><div class="kpi-label">Achieved</div><div class="kpi-value orange">{money(gt['Fee Collected'])}</div><div class="kpi-sub">{pct_value(gt['Ach %']):.1f}% overall</div></div><div class="kpi"><div class="kpi-label">FTD</div><div class="kpi-value green">{money(gt['FTD'])}</div><div class="kpi-sub">Today's fee collected</div></div></div><div class="slabel"><span>Counsellor-wise Fee Collected Breakdown · Counsellor targets are intentionally zero</span></div><div class="table-wrap"><table><thead><tr><th class="left">Counsellor</th><th>Target</th><th>Achieved</th><th>Ach %</th><th>FTD</th></tr></thead><tbody>{fee_collected_rows()}</tbody></table></div></section>
<section class="panel" id="p3"><div class="kpis"><div class="kpi"><div class="kpi-label">Adm Target</div><div class="kpi-value">{total_adm_target}</div><div class="kpi-sub">{month_label}</div></div><div class="kpi"><div class="kpi-label">Achieved</div><div class="kpi-value">{int(gt_adm['Achieve'])}</div><div class="kpi-sub">{adm_ach_pct:.1f}%</div></div><div class="kpi"><div class="kpi-label">FTD</div><div class="kpi-value green">{int(gt_adm['FTD'])}</div><div class="kpi-sub">Today's closes</div></div></div><div class="slabel"><span>Counsellor-wise Admissions</span></div><div class="table-wrap"><table><thead><tr><th class="left">Counsellor</th><th>Achieved</th><th>FTD</th></tr></thead><tbody>{admission_rows()}</tbody></table></div></section>
<section class="panel" id="p4"><div class="kpis"><div class="kpi"><div class="kpi-label">YTD Forms</div><div class="kpi-value">{num(college.iloc[-1]['YTD Forms'])}</div><div class="kpi-sub">Total submitted</div></div><div class="kpi"><div class="kpi-label">YTD Admissions</div><div class="kpi-value">{num(college.iloc[-1]['YTD Admissions'])}</div><div class="kpi-sub">Converted</div></div><div class="kpi"><div class="kpi-label">YTD F2A %</div><div class="kpi-value amber">{college.iloc[-1]['YTD F2A %']}</div><div class="kpi-ratio">{int(college.iloc[-1]['YTD Admissions'])}/{int(college.iloc[-1]['YTD Forms'])}</div><div class="kpi-sub">Conversion rate</div></div></div><div class="slabel"><span>College-wise Performance · Forms to Admissions</span></div><div class="table-wrap"><table><thead><tr><th class="left" rowspan="2">College</th><th colspan="3">Year to Date</th><th colspan="3">Month to Date</th><th colspan="3">Fortnight to Date</th></tr><tr><th>Forms</th><th>Adm</th><th>F2A %</th><th>Forms</th><th>Adm</th><th>F2A %</th><th>Forms</th><th>Adm</th><th>F2A %</th></tr></thead><tbody>{college_rows()}</tbody></table></div></section><footer class="footer"><div class="footer-note">F2A = Forms to Admissions conversion. FTD = For The Day. Fee Collected in Indian ₹.</div><div class="footer-brand">Online · Performance · {month_label}</div></footer></div></body></html>'''

with open(OUT, 'w', encoding='utf-8-sig') as f: f.write(html_doc)
print(f'Generated HTML report at {OUT}')

def send_file(path):
    if not WHAPI_TOKEN: raise RuntimeError('WHAPI_TOKEN missing')
    with open(path,'rb') as f: b64=base64.b64encode(f.read()).decode('utf-8')
    media=f'data:text/html;name={os.path.basename(path)};base64,{b64}'
    headers={'accept':'application/json','authorization':f'Bearer {WHAPI_TOKEN}','content-type':'application/json'}
    payload={'to':WHATSAPP_GROUP,'media':media,'caption':'📊 *Interactive Online LMS HTML Report*\nVishal fee target corrected to ₹20 lakh. Fee collected wording and ratio format updated.'}
    last=None
    for i in range(3):
        try:
            r=requests.post('https://gate.whapi.cloud/messages/document',headers=headers,json=payload,timeout=30)
            print('Status:',r.status_code); print('Response:',r.text[:500])
            if 200 <= r.status_code < 300: return
            last=r.text
        except Exception as e:
            last=str(e); print('Attempt failed:', last); time.sleep(2)
    raise RuntimeError(f'WHAPI send failed: {last}')

if os.getenv('SKIP_SEND','0') != '1': send_file(OUT)
