import psycopg2
import os
import pandas as pd
from datetime import timedelta, date, datetime
from dotenv import load_dotenv
import math

load_dotenv('/home/mohit/workspace/.env')
db_online = {"host": os.getenv("ONLINE_LMS_DB_HOST"), "port": os.getenv("ONLINE_LMS_DB_PORT"), "dbname": os.getenv("ONLINE_LMS_DB_NAME"), "user": os.getenv("ONLINE_LMS_DB_USER"), "password": os.getenv("ONLINE_LMS_DB_PASSWORD")}

def run_query(sql):
    conn = psycopg2.connect(**db_online)
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
    SELECT DISTINCT ON (s.student_id)
        s.student_id,
        DATE(csj.created_at AT TIME ZONE 'Asia/Kolkata') as dt,
        uc.university_name AS college_name
    FROM students s
    JOIN course_status_journeys csj ON s.student_id = csj.student_id
    JOIN university_courses uc ON csj.course_id = uc.course_id
    WHERE csj.course_status = 'Application'
    ORDER BY s.student_id, uc.course_id, csj.created_at ASC
)
SELECT dt as date, college_name, COUNT(*) as forms
FROM raw_forms
WHERE dt BETWEEN '{start_date}' AND '{end_date}'
GROUP BY 1, 2
"""

df_forms = run_query(q_forms)
df_adm = run_query(q_adm)

target_colleges = [
    "Amity University Online", "Sikkim Manipal University Online", "Manipal University Online",
    "Galgotias University Online", "Chandigarh University Online", "Shoolini University online",
    "Lovely Professional University Online", "GLA University Online", "Vivekanand Global University Online",
    "Mangalayatan University online", "Jaypee Institute of Information Technology, Noida"
]

results = {}
for c in target_colleges:
    c_f = df_forms[df_forms['college_name'].str.lower() == c.lower()]
    c_f = c_f.set_index('date')['forms'] if not c_f.empty else pd.Series()
    c_a = df_adm[df_adm['college_name'].str.lower() == c.lower()]
    c_a = c_a.set_index('date')['adm'] if not c_a.empty else pd.Series()
    daily_forms = [int(c_f.get(d, 0)) for d in dates]
    daily_adm = [int(c_a.get(d, 0)) for d in dates]
    short_name = c.replace(' University Online', '').replace(' University online', '').replace(' Online', '')
    if 'Jaypee' in c: short_name = 'Jaypee (JIIT)'
    elif 'Lovely' in c: short_name = 'LPU'
    results[short_name] = {'full_name': c, 'forms': daily_forms, 'adm': daily_adm, 'total_forms': sum(daily_forms), 'total_adm': sum(daily_adm)}

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

palette = [('#3b82f6', '#60a5fa'), ('#8b5cf6', '#a78bfa'), ('#06b6d4', '#22d3ee'), ('#f59e0b', '#fbbf24'), ('#10b981', '#34d399'), ('#ec4899', '#f472b6'), ('#f43f5e', '#fb7185'), ('#84cc16', '#a3e635'), ('#6366f1', '#818cf8'), ('#14b8a6', '#2dd4bf'), ('#d946ef', '#e879f9')]
colleges = list(results.keys())

radio_inputs, tab_labels, css_rules, panels_html = "", "", "", ""
for i, c in enumerate(colleges):
    idx = i + 1
    chk = " checked" if i == 0 else ""
    radio_inputs += f'<input type="radio" name="tab" id="t{idx}"{chk}>\n'
    tab_labels += f'<label class="tab-label" for="t{idx}">{c}</label>\n'
    color_base, color_stroke = palette[i % len(palette)]
    css_rules += f'#t{{idx}}:checked ~ .container .tabs label[for=t{{idx}}]{{background:{{color_base}};border-color:{{color_base}};color:#fff}}\n'.format(idx=idx, color_base=color_base)
    css_rules += f'#t{{idx}}:checked ~ .container #p{{idx}}{{display:block}}\n'.format(idx=idx)
    cd = results[c]
    conv = f"{(cd['total_adm'] / cd['total_forms'] * 100):.1f}%" if cd['total_forms'] > 0 else "0.0%"
    svg_f = generate_svg(cd['forms'], color_base, color_stroke)
    svg_a = generate_svg(cd['adm'], '#10b981', '#34d399')
    panels_html += f"""
  <div id="p{idx}" class="panel">
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
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Online College Dashboard</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0f172a;color:#e2e8f0;padding:14px}}
h1{{text-align:center;font-size:17px;font-weight:700;color:#f8fafc;margin-bottom:2px;padding-top:6px}}
.subtitle{{text-align:center;font-size:11px;color:#475569;margin-bottom:16px}}
input[type=radio]{{position:absolute;opacity:0;width:0;height:0}}
.tabs{{display:flex;gap:5px;flex-wrap:wrap;margin-bottom:16px;justify-content:center}}
.tab-label{{padding:7px 13px;font-size:12px;font-weight:500;border-radius:20px;border:1.5px solid #334155;cursor:pointer;color:#94a3b8;background:#1e293b;white-space:nowrap;transition:0.2s;}}
{css_rules}
.panel{{display:none}}
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
<h1>📊 Online Admissions Tracker</h1>
<p class="subtitle">{subtitle_date}</p>
{radio_inputs}
<div class="container">
  <div class="tabs">{tab_labels}</div>
  {panels_html}
</div>
</body>
</html>"""

with open('/home/mohit/workspace/online_daily_dashboard_exact.html', 'w') as f:
    f.write(html)
print("Online HTML generated.")
