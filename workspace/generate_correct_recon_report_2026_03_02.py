import os
import csv
import json
import html
import base64
import datetime as dt
from pathlib import Path
from collections import defaultdict

import psycopg2
import psycopg2.extras
import requests
from dotenv import load_dotenv

WORKDIR = Path('/home/mohit/workspace')
load_dotenv(WORKDIR / '.env')

REPORT_DATE = '2026-03-02'
WHATSAPP_GROUP = '120363426619711887@g.us'

# USER-CORRECTED SOURCE QUERY. Do not add DB filters/joins beyond this query.
QUERY = """
SELECT 
    scass.*,
    sla.utm_campaign
FROM student_college_api_sent_status scass
LEFT JOIN (
    SELECT DISTINCT ON (student_id)
        student_id,
        utm_campaign
    FROM student_lead_activities
    ORDER BY student_id, created_at DESC
) sla
ON scass.student_id = sla.student_id
WHERE DATE(scass.created_at AT TIME ZONE 'Asia/Kolkata') = '2026-03-02';
"""


def connect():
    return psycopg2.connect(
        host=os.getenv('REGULAR_LMS_DB_HOST'),
        port=os.getenv('REGULAR_LMS_DB_PORT', '5432'),
        dbname=os.getenv('REGULAR_LMS_DB_NAME') or os.getenv('REGULAR_LMS_DB_DATABASE') or 'regular_lms',
        user=os.getenv('REGULAR_LMS_DB_USER'),
        password=os.getenv('REGULAR_LMS_DB_PASSWORD'),
    )


def fetch_rows():
    with connect() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(QUERY)
            return [dict(r) for r in cur.fetchall()]


def norm_status(status):
    s = (status or '').strip().lower()
    if s == 'proceed':
        return 'proceed'
    if 'technical issues' in s or 'failed' in s:
        return 'failed'
    if s == 'do not proceed' or 'dnp' in s or 'do not' in s:
        return 'dnp'
    return 'other'


def norm_sent_type(sent_type):
    s = (sent_type or '').strip().lower()
    if s == 'auto':
        return 'auto'
    if s == 'manual':
        return 'manual'
    return 'other'


def safe_dt(v):
    if isinstance(v, (dt.datetime, dt.date)):
        return v.isoformat(sep=' ')
    return v


def write_raw_csv(rows, out_path):
    if not rows:
        out_path.write_text('No data found\n', encoding='utf-8')
        return
    keys = list(rows[0].keys())
    with out_path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for row in rows:
            w.writerow({k: safe_dt(row.get(k)) for k in keys})


def build_summary(rows):
    data = defaultdict(lambda: {
        'auto': {'proceed': 0, 'failed': 0, 'dnp': 0, 'other': 0},
        'manual': {'proceed': 0, 'failed': 0, 'dnp': 0, 'other': 0},
        'other': {'proceed': 0, 'failed': 0, 'dnp': 0, 'other': 0},
        'campaigns': defaultdict(int),
    })
    seen = set()
    duplicates = 0
    for r in rows:
        college = r.get('college_name') or r.get('college') or r.get('college_for_applied') or 'Unknown'
        sent = norm_sent_type(r.get('sent_type'))
        status = norm_status(r.get('api_sent_status'))
        sid = r.get('student_id')
        # Count records from the query, but track duplicate student IDs separately for audit.
        if sid is not None:
            if sid in seen:
                duplicates += 1
            seen.add(sid)
        data[college][sent][status] += 1
        campaign = (r.get('utm_campaign') or 'No UTM').strip() or 'No UTM'
        data[college]['campaigns'][campaign] += 1
    return data, len(seen), duplicates


def pct(n, d):
    return f'{(n / d * 100):.1f}%' if d else '0.0%'


def build_html(rows, data, unique_students, duplicate_records):
    totals = {
        'auto': {'proceed': 0, 'failed': 0, 'dnp': 0, 'other': 0},
        'manual': {'proceed': 0, 'failed': 0, 'dnp': 0, 'other': 0},
        'other': {'proceed': 0, 'failed': 0, 'dnp': 0, 'other': 0},
    }
    body = []
    for college in sorted(data):
        d = data[college]
        for st in totals:
            for ss in totals[st]:
                totals[st][ss] += d[st][ss]
        a = d['auto']; m = d['manual']; o = d['other']
        total_proceed = a['proceed'] + m['proceed'] + o['proceed']
        total_failed = a['failed'] + m['failed'] + o['failed']
        total_dnp = a['dnp'] + m['dnp'] + o['dnp']
        total_other = a['other'] + m['other'] + o['other']
        college_total = sum(a.values()) + sum(m.values()) + sum(o.values())
        top_campaigns = sorted(d['campaigns'].items(), key=lambda x: x[1], reverse=True)[:3]
        campaign_html = '<br>'.join(f'{html.escape(k)} <b>{v}</b>' for k, v in top_campaigns)
        body.append(f"""
        <tr>
          <td class="college">{html.escape(str(college))}</td>
          <td>{a['proceed']}</td><td>{a['failed']}</td><td>{a['dnp']}</td><td>{a['other']}</td>
          <td>{m['proceed']}</td><td>{m['failed']}</td><td>{m['dnp']}</td><td>{m['other']}</td>
          <td>{total_proceed}</td><td>{total_failed}</td><td>{total_dnp}</td><td>{total_other}</td>
          <td class="total">{college_total}</td>
          <td class="campaign">{campaign_html}</td>
        </tr>
        """)
    auto_total = sum(totals['auto'].values())
    manual_total = sum(totals['manual'].values())
    other_total = sum(totals['other'].values())
    grand_total = auto_total + manual_total + other_total
    gp = totals['auto']['proceed'] + totals['manual']['proceed'] + totals['other']['proceed']
    gf = totals['auto']['failed'] + totals['manual']['failed'] + totals['other']['failed']
    gd = totals['auto']['dnp'] + totals['manual']['dnp'] + totals['other']['dnp']
    go = totals['auto']['other'] + totals['manual']['other'] + totals['other']['other']
    generated = dt.datetime.now().strftime('%d %b %Y %I:%M %p')
    query_block = html.escape(QUERY.strip())
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Correct Recon Report {REPORT_DATE}</title>
<style>
body{{margin:0;background:#0f172a;color:#e2e8f0;font-family:Inter,Arial,sans-serif;padding:24px}}
.wrap{{max-width:1400px;margin:auto}}
h1{{margin:0;color:#38bdf8;font-size:26px}} .sub{{color:#94a3b8;margin:8px 0 22px}}
.cards{{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:20px}}
.card{{background:#1e293b;border:1px solid #334155;border-radius:14px;padding:14px}}
.label{{font-size:11px;text-transform:uppercase;color:#94a3b8;letter-spacing:.08em}} .val{{font-size:26px;font-weight:800;margin-top:6px;color:white}}
table{{width:100%;border-collapse:separate;border-spacing:0;background:#1e293b;border:1px solid #334155;border-radius:14px;overflow:hidden}}
th{{position:sticky;top:0;background:#020617;color:#93c5fd;font-size:11px;text-transform:uppercase;padding:10px 8px;border-bottom:1px solid #334155}}
td{{padding:10px 8px;border-bottom:1px solid #334155;border-right:1px solid #334155;text-align:center;font-size:13px}}
.college{{text-align:left;font-weight:700;color:#f8fafc;min-width:250px;background:#172033}} .campaign{{text-align:left;font-size:11px;color:#cbd5e1;min-width:260px}}
.total{{font-weight:800;color:#38bdf8}} .grand td{{background:#020617;color:#38bdf8;font-weight:800}}
pre{{white-space:pre-wrap;background:#020617;border:1px solid #334155;border-radius:12px;padding:14px;color:#cbd5e1;font-size:12px}}
.note{{color:#fbbf24;font-weight:700}}
</style></head><body><div class="wrap">
<h1>Correct Regular LMS Recon Report</h1>
<div class="sub">Date: {REPORT_DATE} IST | Generated: {generated} | Source: exactly the user-corrected query below.</div>
<div class="cards">
 <div class="card"><div class="label">Query Records</div><div class="val">{grand_total}</div></div>
 <div class="card"><div class="label">Unique Students</div><div class="val">{unique_students}</div></div>
 <div class="card"><div class="label">Auto Total</div><div class="val">{auto_total}</div></div>
 <div class="card"><div class="label">Manual Total</div><div class="val">{manual_total}</div></div>
 <div class="card"><div class="label">Proceed Rate</div><div class="val">{pct(gp, grand_total)}</div></div>
</div>
<table><thead>
<tr><th rowspan="2">College</th><th colspan="4">Auto Recon</th><th colspan="4">Manual Recon</th><th colspan="4">Total Status</th><th rowspan="2">Total</th><th rowspan="2">Top UTM Campaigns</th></tr>
<tr><th>Proceed</th><th>Failed</th><th>DNP</th><th>Other</th><th>Proceed</th><th>Failed</th><th>DNP</th><th>Other</th><th>Proceed</th><th>Failed</th><th>DNP</th><th>Other</th></tr>
</thead><tbody>{''.join(body)}
<tr class="grand"><td class="college">Grand Total</td><td>{totals['auto']['proceed']}</td><td>{totals['auto']['failed']}</td><td>{totals['auto']['dnp']}</td><td>{totals['auto']['other']}</td><td>{totals['manual']['proceed']}</td><td>{totals['manual']['failed']}</td><td>{totals['manual']['dnp']}</td><td>{totals['manual']['other']}</td><td>{gp}</td><td>{gf}</td><td>{gd}</td><td>{go}</td><td>{grand_total}</td><td>Duplicate student records in query: {duplicate_records}</td></tr>
</tbody></table>
<h2>Exact Query Used</h2><pre>{query_block}</pre>
<div class="sub note">No branded/source filters, no extra DB query, no replacement logic. This report is built only from the returned rows of the query above.</div>
</div></body></html>"""


def send_whatsapp_document(path, caption):
    token = os.getenv('WHAPI_TOKEN')
    if not token:
        return {'skipped': True, 'reason': 'WHAPI_TOKEN missing'}
    b64 = base64.b64encode(path.read_bytes()).decode('utf-8')
    media = f'data:text/html;name={path.name};base64,{b64}'
    resp = requests.post(
        'https://gate.whapi.cloud/messages/document',
        headers={'accept': 'application/json', 'authorization': f'Bearer {token}', 'content-type': 'application/json'},
        json={'to': WHATSAPP_GROUP, 'media': media, 'caption': caption},
        timeout=30,
    )
    return {'status_code': resp.status_code, 'text': resp.text[:1000]}


def main():
    rows = fetch_rows()
    html_path = WORKDIR / f'Correct_Recon_Report_{REPORT_DATE}.html'
    csv_path = WORKDIR / f'Correct_Recon_Raw_Query_Data_{REPORT_DATE}.csv'
    write_raw_csv(rows, csv_path)
    data, unique_students, duplicate_records = build_summary(rows)
    html_path.write_text(build_html(rows, data, unique_students, duplicate_records), encoding='utf-8')
    caption = f'✅ Correct Regular LMS Recon Report\n📅 Date: {REPORT_DATE} IST\nSource: only the corrected query provided by Mohit.\nRecords: {len(rows)} | Unique Students: {unique_students}'
    wa = send_whatsapp_document(html_path, caption)
    print(json.dumps({
        'query_records': len(rows),
        'unique_students': unique_students,
        'duplicate_student_records': duplicate_records,
        'html_report': str(html_path),
        'raw_csv': str(csv_path),
        'whatsapp_result': wa,
    }, indent=2))

if __name__ == '__main__':
    main()
