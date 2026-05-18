import psycopg2
import os
import pandas as pd
from datetime import timedelta, date, datetime
from dotenv import load_dotenv
import math

load_dotenv('/home/mohit/workspace/.env')

dbs = {
    "regular": {"host": os.getenv("REGULAR_LMS_DB_HOST"), "port": os.getenv("REGULAR_LMS_DB_PORT"), "dbname": os.getenv("REGULAR_LMS_DB_NAME"), "user": os.getenv("REGULAR_LMS_DB_USER"), "password": os.getenv("REGULAR_LMS_DB_PASSWORD")},
    "cgc": {"host": os.getenv("REGULAR_CGC_LMS_DB_HOST"), "port": os.getenv("REGULAR_CGC_LMS_DB_PORT"), "dbname": os.getenv("REGULAR_CGC_LMS_DB_NAME"), "user": os.getenv("REGULAR_CGC_LMS_DB_USER"), "password": os.getenv("REGULAR_CGC_LMS_DB_PASSWORD")},
    "amity": {"host": os.getenv("REGULAR_AMITY_LMS_DB_HOST"), "port": os.getenv("REGULAR_AMITY_LMS_DB_PORT"), "dbname": os.getenv("REGULAR_AMITY_LMS_DB_NAME"), "user": os.getenv("REGULAR_AMITY_LMS_DB_USER"), "password": os.getenv("REGULAR_AMITY_LMS_DB_PASSWORD")}
}

def run_query(db_key, sql):
    conn = psycopg2.connect(**dbs[db_key])
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]
    cur.close()
    conn.close()
    return pd.DataFrame([dict(zip(cols, row)) for row in rows])

end_date = (datetime.now() - timedelta(days=1)).date()
start_date = end_date - timedelta(days=14)
dates = [start_date + timedelta(days=i) for i in range(15)]
labels = [d.strftime('%-d%b').upper() for d in dates]
subtitle_date = f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}"

q_adm = f"""
WITH raw_adm AS (
    SELECT DISTINCT ON (s.student_id, uc.course_id)
        s.student_id,
        DATE(csj.created_at AT TIME ZONE 'Asia/Kolkata') as dt,
        uc.university_name AS college_name
    FROM students s
    JOIN course_status_journeys csj ON s.student_id = csj.student_id
    JOIN university_courses uc ON csj.course_id = uc.course_id
    WHERE csj.course_status = 'Admission'
      AND csj.fee_type NOT IN ('partial paid', 'Partially Paid', 'Partial Done','Partial Paid')
      AND s.student_id IN (SELECT student_id FROM students)
    ORDER BY s.student_id, uc.course_id, csj.created_at ASC
)
SELECT dt as date, college_name, COUNT(*) as adm
FROM raw_adm
WHERE dt BETWEEN '{start_date}' AND '{end_date}'
GROUP BY 1, 2
"""

q_forms = f"""
WITH raw_forms AS (
    SELECT 
        s.student_id,
        uc.university_name AS college_name,
        DATE(MIN(csj.created_at AT TIME ZONE 'Asia/Kolkata')) as dt
    FROM students s 
    JOIN course_status_journeys csj ON s.student_id = csj.student_id 
    JOIN university_courses uc ON csj.course_id = uc.course_id 
    WHERE csj.course_status IN (
        'Form Submitted – Portal Pending', 
        'Form Submitted – Completed', 
        'Walkin Completed', 
        'Walkin Marked', 
        'Exam/Interview Scheduled', 
        'Offer Letter/Results Pending', 
        'Offer Letter/Results Released', 
        'Ready For Admission'
    )
      AND s.student_id IN (SELECT student_id FROM students)
    GROUP BY s.student_id, uc.university_name
)
SELECT dt as date, college_name, COUNT(*) as forms
FROM raw_forms
WHERE dt BETWEEN '{start_date}' AND '{end_date}'
GROUP BY 1, 2
"""

adm_reg = run_query("regular", q_adm)
forms_reg = run_query("regular", q_forms)
adm_cgc = run_query("cgc", q_adm)
forms_cgc = run_query("cgc", q_forms)
adm_amity = run_query("amity", q_adm)
forms_amity = run_query("amity", q_forms)

forms_all = pd.concat([forms_reg, forms_cgc, forms_amity], ignore_index=True)
adm_all = pd.concat([adm_reg, adm_cgc, adm_amity], ignore_index=True)

def standardize(name):
    name = str(name).lower()
    if 'amity' in name: return 'Amity'
    if 'lovely' in name or 'lpu' in name: return 'LPU'
    if 'mohali' in name: return 'CU Mohali'
    if 'lucknow' in name: return 'CU Lucknow'
    if 'cgc' in name or 'landran' in name: return 'CGC Landran'
    return 'Other'

forms_all['College'] = forms_all['college_name'].apply(standardize)
adm_all['College'] = adm_all['college_name'].apply(standardize)

forms_agg = forms_all[forms_all['College'] != 'Other'].groupby(['College', 'date'])['forms'].sum().reset_index()
adm_agg = adm_all[adm_all['College'] != 'Other'].groupby(['College', 'date'])['adm'].sum().reset_index()

colleges = ['Amity', 'LPU', 'CU Mohali', 'CGC Landran', 'CU Lucknow']
results = {}
for c in colleges:
    c_f = forms_agg[forms_agg['College'] == c].set_index('date')['forms']
    c_a = adm_agg[adm_agg['College'] == c].set_index('date')['adm']
    daily_forms = [int(c_f.get(d, 0)) for d in dates]
    daily_adm = [int(c_a.get(d, 0)) for d in dates]
    results[c] = {'forms': daily_forms, 'adm': daily_adm, 'total_forms': sum(daily_forms), 'total_adm': sum(daily_adm)}

def generate_svg(values, color, stroke_color):
    max_v = max(values) if values else 0
    if max_v == 0: max_v = 1
    if max_v <= 5: max_y = 5
    elif max_v <= 10: max_y = 10
    elif max_v <= 50: max_y = math.ceil(max_v/10)*10
    elif max_v <= 100: max_y = math.ceil(max_v/20)*20
    elif max_v <= 200: max_y = math.ceil(max_v/20)*20
    elif max_v <= 500: max_y = math.ceil(max_v/50)*50
    else: max_y = math.ceil(max_v/100)*100
    mid_y = max_y / 2
    x_step = 444 / 14
    pts, circles, text_labels = [], [], []
    for i, v in enumerate(values):
        x = round(32 + i * x_step, 1)
        y = round(118 - (v / max_y) * 110, 1)
        pts.append(f"{x},{y}")
        circles.append(f'<circle cx="{x}" cy="{y}" r="3.5" fill="{stroke_color}" stroke="#0f172a" stroke-width="1.5"/>')
        text_y = y - 8 if y > 20 else y + 12
        text_labels.append(f'<text x="{x}" y="{text_y}" text-anchor="middle" font-size="8" fill="#93c5fd">{v}</text>')
    pts_str = " ".join(pts)
    poly_pts = f"32,118 {pts_str} 476,118 32,118"
    svg = f"""<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:100%">
      <line x1="32" y1="8" x2="32" y2="118" stroke="#334155" stroke-width="1"/>
      <line x1="32" y1="118" x2="476" y2="118" stroke="#334155" stroke-width="1"/>
      <line x1="32" y1="8" x2="476" y2="8" stroke="#334155" stroke-width=".4" stroke-dasharray="3,3"/>
      <line x1="32" y1="63" x2="476" y2="63" stroke="#334155" stroke-width=".4" stroke-dasharray="3,3"/>
      <text x="28" y="12" text-anchor="end" font-size="9" fill="#475569">{int(max_y)}</text>
      <text x="28" y="67" text-anchor="end" font-size="9" fill="#475569">{int(mid_y)}</text>
      <text x="28" y="122" text-anchor="end" font-size="9" fill="#475569">0</text>
      <polygon points="{poly_pts}" fill="{color}" fill-opacity=".12"/>
      <polyline points="{pts_str}" fill="none" stroke="{stroke_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      {''.join(circles)}"""
    for i, lbl in enumerate(labels):
        x = round(32 + i * x_step, 1)
        svg += f'<text x="{x}" y="135" text-anchor="middle" font-size="8.5" fill="#475569">{lbl}</text>\n'
    svg += f"""{''.join(text_labels)}
      <line x1="237" y1="8" x2="237" y2="118" stroke="#334155" stroke-width="1" stroke-dasharray="4,2"/>
    </svg>"""
    return svg

colors = {
    'Amity': {'f': '#3b82f6', 'f_s': '#60a5fa', 'a': '#10b981', 'a_s': '#34d399'},
    'LPU': {'f': '#8b5cf6', 'f_s': '#a78bfa', 'a': '#10b981', 'a_s': '#34d399'},
    'CU Mohali': {'f': '#06b6d4', 'f_s': '#22d3ee', 'a': '#10b981', 'a_s': '#34d399'},
    'CGC Landran': {'f': '#f59e0b', 'f_s': '#fbbf24', 'a': '#10b981', 'a_s': '#34d399'},
    'CU Lucknow': {'f': '#10b981', 'f_s': '#4ade80', 'a': '#10b981', 'a_s': '#34d399'}
}

panels_html = ""
for i, c in enumerate(colleges):
    p_id = f"p{i+1}"
    cd = results[c]
    conv = f"{(cd['total_adm'] / cd['total_forms'] * 100):.1f}%" if cd['total_forms'] > 0 else "0.0%"
    svg_f = generate_svg(cd['forms'], colors[c]['f'], colors[c]['f_s'])
    svg_a = generate_svg(cd['adm'], colors[c]['a'], colors[c]['a_s'])
    panels_html += f"""
  <div id="{p_id}" class="panel">
    <div class="stats">
      <div class="stat"><div class="stat-label">Forms</div><div class="stat-val col-f">{cd['total_forms']:,}</div></div>
      <div class="stat"><div class="stat-label">Admissions</div><div class="stat-val col-a">{cd['total_adm']:,}</div></div>
      <div class="stat"><div class="stat-label">Conv</div><div class="stat-val col-c">{conv}</div></div>
    </div>
    <div class="card">
      <div class="card-title">Forms — Daily</div>
      <div class="chart-wrap"><div class="chart-inner">{svg_f}</div></div>
    </div>
    <div class="card">
      <div class="card-title">Admissions — Daily</div>
      <div class="chart-wrap"><div class="chart-inner">{svg_a}</div></div>
    </div>
  </div>"""

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Regular College Dashboard</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0f172a;color:#e2e8f0;padding:14px}}
h1{{text-align:center;font-size:17px;font-weight:700;color:#f8fafc;margin-bottom:2px;padding-top:6px}}
.subtitle{{text-align:center;font-size:11px;color:#475569;margin-bottom:16px}}
input[type=radio]{{position:absolute;opacity:0;width:0;height:0}}
.tabs{{display:flex;gap:5px;flex-wrap:wrap;margin-bottom:16px;justify-content:center}}
.tab-label{{padding:7px 13px;font-size:12px;font-weight:500;border-radius:20px;border:1.5px solid #334155;cursor:pointer;color:#94a3b8;background:#1e293b;white-space:nowrap}}
#t1:checked ~ .container .tabs label[for=t1]{{background:#3b82f6;border-color:#3b82f6;color:#fff}}
#t2:checked ~ .container .tabs label[for=t2]{{background:#8b5cf6;border-color:#8b5cf6;color:#fff}}
#t3:checked ~ .container .tabs label[for=t3]{{background:#06b6d4;border-color:#06b6d4;color:#fff}}
#t4:checked ~ .container .tabs label[for=t4]{{background:#f59e0b;border-color:#f59e0b;color:#fff}}
#t5:checked ~ .container .tabs label[for=t5]{{background:#10b981;border-color:#10b981;color:#fff}}
.panel{{display:none}}
#t1:checked ~ .container #p1{{display:block}}
#t2:checked ~ .container #p2{{display:block}}
#t3:checked ~ .container #p3{{display:block}}
#t4:checked ~ .container #p4{{display:block}}
#t5:checked ~ .container #p5{{display:block}}
.stats{{display:flex;gap:8px;margin-bottom:14px}}
.stat{{flex:1;background:#1e293b;border-radius:10px;padding:11px 8px;text-align:center;border:1px solid #1e3a5f}}
.stat-label{{font-size:10px;color:#64748b;margin-bottom:4px;text-transform:uppercase;letter-spacing:.4px}}
.stat-val{{font-size:22px;font-weight:700}}
.col-f{{color:#60a5fa}}.col-a{{color:#34d399}}.col-c{{color:#fbbf24}}
.card{{background:#1e293b;border-radius:12px;padding:14px 12px;margin-bottom:14px;border:1px solid #1e3a5f}}
.card-title{{font-size:11px;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:.5px;margin-bottom:10px}}
.chart-wrap{{width:100%;overflow-x:auto;-webkit-overflow-scrolling:touch}}
.chart-inner{{min-width:480px;height:160px;position:relative}}
</style>
</head>
<body>
<h1>📊 Regular Admissions Tracker</h1>
<p class="subtitle">{subtitle_date}</p>
<input type="radio" name="tab" id="t1" checked>
<input type="radio" name="tab" id="t2">
<input type="radio" name="tab" id="t3">
<input type="radio" name="tab" id="t4">
<input type="radio" name="tab" id="t5">
<div class="container">
  <div class="tabs">
    <label class="tab-label" for="t1">Amity</label>
    <label class="tab-label" for="t2">LPU</label>
    <label class="tab-label" for="t3">CU Mohali</label>
    <label class="tab-label" for="t4">CGC Landran</label>
    <label class="tab-label" for="t5">CU Lucknow</label>
  </div>
  {panels_html}
</div>
</body>
</html>"""

with open('/home/mohit/workspace/true_regular_daily_dashboard_exact.html', 'w') as f:
    f.write(html)
print("Regular HTML generated.")
