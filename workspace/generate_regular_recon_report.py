"""
Regular API Recon Report Generator
Generates two reports: ALL Sources and Branded Campaigns
"""
import os
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
import re

from dotenv import load_dotenv
load_dotenv()

# Connection string
DB_CONFIG = {
    'host': os.getenv('REGULAR_LMS_DB_HOST', 'storage.bhugoal.cloud'),
    'port': int(os.getenv('REGULAR_LMS_DB_PORT', 54321)),
    'dbname': os.getenv('REGULAR_LMS_DB_NAME', 'degreefyd_regular_lms'),
    'user': os.getenv('REGULAR_LMS_DB_USER', 'postgres'),
    'password': os.getenv('REGULAR_LMS_DB_PASSWORD')
}

# Report date
yesterday = datetime.now() - timedelta(days=1)
REPORT_DATE = yesterday.strftime('%Y-%m-%d')
print(f"Generating report for: {REPORT_DATE}")

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def fetch_all_sources_report(date_str):
    """
    ALL Sources Query - no filter
    """
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    query = """
    SELECT 
        r.college_name, 
        r.sent_type, 
        r.api_sent_status, 
        COUNT(DISTINCT r.student_id) as lead_count
    FROM student_college_api_sent_status r
    WHERE DATE(r.created_at AT TIME ZONE 'Asia/Kolkata') = %s
    GROUP BY 1,2,3
    ORDER BY 1,2,3
    """
    cur.execute(query, (date_str,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def fetch_branded_student_ids(date_str):
    """
    Get student_ids from branded campaigns for yesterday
    Uses latest_utm (DISTINCT ON student_id) from student_lead_activities
    Returns set of student_ids that match branded patterns
    """
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # First, get all student_ids that have recon entries for yesterday
    recon_query = """
    SELECT DISTINCT r.student_id
    FROM student_college_api_sent_status r
    WHERE DATE(r.created_at AT TIME ZONE 'Asia/Kolkata') = %s
    """
    cur.execute(recon_query, (date_str,))
    recon_students = [row['student_id'] for row in cur.fetchall()]
    
    if not recon_students:
        cur.close()
        conn.close()
        return set()
    
    # Get latest UTM data for these students (DISTINCT ON student_id)
    utm_query = """
    SELECT DISTINCT ON (student_id) 
        student_id, 
        utm_campaign, 
        utm_campaign_id
    FROM student_lead_activities
    WHERE student_id = ANY(%s)
    ORDER BY student_id, created_at DESC
    """
    cur.execute(utm_query, (recon_students,))
    utm_rows = cur.fetchall()
    cur.close()
    conn.close()
    
    # Branded campaign name patterns (case-insensitive)
    branded_patterns = [
        'LPU_Online', 'CU_Online', 'cu_online', 'Amity_Online', 
        'Amity_University', 'Partner_Amity', 'Shoolini_Online', 
        'Galgotias', 'VGU_Online', 'Manipal_Online', 'GLA_Online', 
        'GLA_University', 'IGNOU', 'UA_MBA', 'F_UA'
    ]
    
    # Branded campaign IDs (exact match)
    branded_campaign_ids = {
        '23659350616', '23807086200', '23810994645', '23814823859',
        '23820721369', '23821027168', '23228113322', '23794794232',
        '23794010280', '23772025619', '23779002914', '23794940566',
        '23767340817', '23798269338', '23772157658', '23803352159',
        '23470383548', '23502437890', '23676777747', '23534722448',
        '23486436393', '23486463996', '23675435222'
    }
    
    branded_student_ids = set()
    branded_info = {}
    
    for row in utm_rows:
        sid = row['student_id']
        campaign = (row['utm_campaign'] or '') 
        camp_id = str(row['utm_campaign_id'] or '')
        
        is_branded = False
        matched_pattern = None
        
        # Check campaign name patterns
        for pattern in branded_patterns:
            if pattern.lower() in campaign.lower():
                is_branded = True
                matched_pattern = f"campaign:{pattern}"
                break
        
        # Check campaign IDs
        if not is_branded and camp_id in branded_campaign_ids:
            is_branded = True
            matched_pattern = f"campaign_id:{camp_id}"
        
        if is_branded:
            branded_student_ids.add(sid)
            branded_info[sid] = {
                'utm_campaign': campaign,
                'utm_campaign_id': camp_id,
                'matched_by': matched_pattern
            }
    
    print(f"\nBranded matching results:")
    print(f"  Total recon students: {len(recon_students)}")
    print(f"  Students with UTM data: {len(utm_rows)}")
    print(f"  Branded matched students: {len(branded_student_ids)}")
    
    # Print sample branded matches for verification
    sample_count = 0
    for sid, info in list(branded_info.items())[:10]:
        print(f"  {sid}: campaign='{info['utm_campaign']}' id='{info['utm_campaign_id']}' match={info['matched_by']}")
        sample_count += 1
    
    return branded_student_ids

def fetch_branded_recon(date_str, branded_student_ids):
    """
    Get recon status counts for branded students only
    """
    if not branded_student_ids:
        return []
    
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    query = """
    SELECT 
        r.college_name, 
        r.sent_type, 
        r.api_sent_status, 
        COUNT(DISTINCT r.student_id) as lead_count
    FROM student_college_api_sent_status r
    WHERE DATE(r.created_at AT TIME ZONE 'Asia/Kolkata') = %s
      AND r.student_id = ANY(%s)
    GROUP BY 1,2,3
    ORDER BY 1,2,3
    """
    cur.execute(query, (date_str, list(branded_student_ids)))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def fetch_lms_lead_counts(date_str, branded_student_ids=None):
    """
    Fetch LMS leads per college from student_lead_activities
    JOINed with student_college_api_sent_status for the branded students
    """
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    if branded_student_ids:
        # Only count leads from branded students
        query = """
        SELECT 
            r.college_name,
            COUNT(DISTINCT la.student_id) as lms_leads
        FROM student_lead_activities la
        INNER JOIN student_college_api_sent_status r 
            ON la.student_id = r.student_id
        WHERE DATE(r.created_at AT TIME ZONE 'Asia/Kolkata') = %s
          AND r.student_id = ANY(%s)
        GROUP BY r.college_name
        ORDER BY r.college_name
        """
        cur.execute(query, (date_str, list(branded_student_ids)))
    else:
        # All sources
        query = """
        SELECT 
            r.college_name,
            COUNT(DISTINCT la.student_id) as lms_leads
        FROM student_lead_activities la
        INNER JOIN student_college_api_sent_status r 
            ON la.student_id = r.student_id
        WHERE DATE(r.created_at AT TIME ZONE 'Asia/Kolkata') = %s
        GROUP BY r.college_name
        ORDER BY r.college_name
        """
        cur.execute(query, (date_str,))
    
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def transform_to_matrix(rows):
    """
    Transform flat rows into college-wise matrix:
    {college: {sent_type: {status: count}}}
    """
    matrix = {}
    for row in rows:
        college = row['college_name']
        sent_type = row['sent_type']
        status = row['api_sent_status']
        count = row['lead_count']
        
        if college not in matrix:
            matrix[college] = {'auto': {}, 'manual': {}}
        
        # Normalize status
        if status == 'Proceed':
            short_status = 'Proceed'
        elif status in ('Do not Proceed', 'Do not Proceed (Still) '):
            short_status = 'Do not Proceed'
        elif status == 'Failed due to Technical Issues':
            short_status = 'Failed'
        elif status == 'Field Missing':
            short_status = 'Field Missing'
        else:
            short_status = status
        
        matrix[college][sent_type][short_status] = matrix[college][sent_type].get(short_status, 0) + count
    
    return matrix

def generate_html(matrix, report_date, lms_leads, title, filename):
    """
    Generate an HTML report with Barlow font, dark theme
    """
    # Status order for columns
    status_order = ['Proceed', 'Failed', 'Do not Proceed', 'Field Missing']
    
    # Build table rows
    table_rows = []
    total_auto_proceed = 0
    total_auto_fail = 0
    total_auto_dnp = 0
    total_auto_fm = 0
    total_manual_proceed = 0
    total_manual_fail = 0
    total_manual_dnp = 0
    total_manual_fm = 0
    
    colleges = sorted(matrix.keys())
    
    for college in colleges:
        data = matrix[college]
        auto = data['auto']
        manual = data['manual']
        
        ap = auto.get('Proceed', 0)
        af = auto.get('Failed', 0)
        ad = auto.get('Do not Proceed', 0)
        afm = auto.get('Field Missing', 0)
        
        mp = manual.get('Proceed', 0)
        mf = manual.get('Failed', 0)
        md = manual.get('Do not Proceed', 0)
        mfm = manual.get('Field Missing', 0)
        
        total_p = ap + mp
        total_f = af + mf
        total_d = ad + md
        total_fm = afm + mfm
        
        total_all = total_p + total_f + total_d + total_fm
        
        total_auto_proceed += ap
        total_auto_fail += af
        total_auto_dnp += ad
        total_auto_fm += afm
        total_manual_proceed += mp
        total_manual_fail += mf
        total_manual_dnp += md
        total_manual_fm += mfm
        
        lms = 0
        for l in lms_leads:
            if l['college_name'] == college:
                lms = l['lms_leads']
                break
        
        table_rows.append(f"""
        <tr>
            <td class="college-name">{college}</td>
            <td>{ap}</td>
            <td>{af}</td>
            <td>{ad}</td>
            <td>{afm}</td>
            <td>{mp}</td>
            <td>{mf}</td>
            <td>{md}</td>
            <td>{mfm}</td>
            <td class="total-proceed">{total_p}</td>
            <td class="total-fail">{total_f}</td>
            <td class="total-dnp">{total_d}</td>
            <td class="total-fm">{total_fm}</td>
            <td class="total-all">{total_all}</td>
            <td class="lms-leads">{lms}</td>
        </tr>
        """)
    
    # Totals row
    total_lms = sum(l['lms_leads'] for l in lms_leads)
    total_all_val = total_auto_proceed + total_auto_fail + total_auto_dnp + total_auto_fm + total_manual_proceed + total_manual_fail + total_manual_dnp + total_manual_fm
    
    totals_row = f"""
    <tr class="totals-row">
        <td class="college-name"><strong>TOTAL</strong></td>
        <td><strong>{total_auto_proceed}</strong></td>
        <td><strong>{total_auto_fail}</strong></td>
        <td><strong>{total_auto_dnp}</strong></td>
        <td><strong>{total_auto_fm}</strong></td>
        <td><strong>{total_manual_proceed}</strong></td>
        <td><strong>{total_manual_fail}</strong></td>
        <td><strong>{total_manual_dnp}</strong></td>
        <td><strong>{total_manual_fm}</strong></td>
        <td class="total-proceed"><strong>{total_auto_proceed + total_manual_proceed}</strong></td>
        <td class="total-fail"><strong>{total_auto_fail + total_manual_fail}</strong></td>
        <td class="total-dnp"><strong>{total_auto_dnp + total_manual_dnp}</strong></td>
        <td class="total-fm"><strong>{total_auto_fm + total_manual_fm}</strong></td>
        <td class="total-all"><strong>{total_all_val}</strong></td>
        <td class="lms-leads"><strong>{total_lms}</strong></td>
    </tr>
    """
    
    table_body = '\n'.join(table_rows)
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Regular API Recon Report — {report_date}</title>
    <link href="https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Barlow', sans-serif;
            background-color: #0b1623;
            color: #e2e8f0;
            padding: 32px;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 32px;
            border-bottom: 1px solid #1e293b;
            padding-bottom: 16px;
        }}
        .header h1 {{
            font-size: 28px;
            font-weight: 700;
            color: #f1f5f9;
        }}
        .header .subtitle {{
            font-size: 14px;
            color: #94a3b8;
        }}
        .header .date-badge {{
            background: #1e293b;
            padding: 8px 20px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            color: #3b82f6;
        }}
        .summary-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 32px;
        }}
        .card {{
            background: linear-gradient(145deg, #0f1a2e, #141f35);
            border: 1px solid #1e293b;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        }}
        .card .card-label {{
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #64748b;
            margin-bottom: 8px;
        }}
        .card .card-value {{
            font-size: 32px;
            font-weight: 700;
        }}
        .card .card-value.proceed {{ color: #3ddc84; }}
        .card .card-value.fail {{ color: #ef4444; }}
        .card .card-value.dnp {{ color: #f59e0b; }}
        .card .card-value.total {{ color: #3b82f6; }}
        .card .card-value.lms {{ color: #a78bfa; }}
        
        .section-title {{
            font-size: 20px;
            font-weight: 600;
            color: #f1f5f9;
            margin-bottom: 16px;
            margin-top: 32px;
        }}
        
        .table-container {{
            overflow-x: auto;
            border-radius: 12px;
            border: 1px solid #1e293b;
            background: #0d1829;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            white-space: nowrap;
        }}
        thead {{
            background: #111d31;
        }}
        th {{
            padding: 12px 8px;
            text-align: center;
            font-weight: 600;
            color: #94a3b8;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 2px solid #1e293b;
            position: sticky;
            top: 0;
            z-index: 1;
            background: #111d31;
        }}
        th:first-child {{
            text-align: left;
            padding-left: 16px;
            min-width: 220px;
        }}
        th.col-header {{
            background: #162240;
        }}
        th.proceed {{ color: #3ddc84; }}
        th.fail {{ color: #ef4444; }}
        th.dnp {{ color: #f59e0b; }}
        th.fm {{ color: #f97316; }}
        th.total {{ color: #3b82f6; }}
        th.lms {{ color: #a78bfa; }}
        
        td {{
            padding: 10px 8px;
            text-align: center;
            border-bottom: 1px solid #152032;
            font-weight: 500;
        }}
        td:first-child {{
            text-align: left;
            padding-left: 16px;
            font-weight: 500;
        }}
        .college-name {{
            color: #e2e8f0;
        }}
        
        tr:hover {{
            background: rgba(59, 130, 246, 0.05);
        }}
        
        .totals-row {{
            background: #111d31 !important;
            border-top: 2px solid #1e293b;
        }}
        .totals-row td {{
            padding: 12px 8px;
            font-weight: 600;
            color: #f1f5f9;
        }}
        
        .total-proceed {{ color: #3ddc84; font-weight: 600; }}
        .total-fail {{ color: #ef4444; font-weight: 600; }}
        .total-dnp {{ color: #f59e0b; font-weight: 600; }}
        .total-fm {{ color: #f97316; font-weight: 600; }}
        .total-all {{ color: #3b82f6; font-weight: 600; }}
        .lms-leads {{ color: #a78bfa; font-weight: 600; }}
        
        .group-header {{
            font-size: 11px;
            color: #64748b;
            background: #0f1a2e !important;
            text-align: center !important;
            padding-top: 16px !important;
        }}
        
        .footer {{
            margin-top: 32px;
            text-align: center;
            color: #475569;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1>{title}</h1>
            <div class="subtitle">Regular LMS API Recon Report</div>
        </div>
        <div class="date-badge">{report_date}</div>
    </div>
    
    <div class="summary-cards">
        <div class="card">
            <div class="card-label">Total Proceed</div>
            <div class="card-value proceed">{total_auto_proceed + total_manual_proceed}</div>
        </div>
        <div class="card">
            <div class="card-label">Total Failed</div>
            <div class="card-value fail">{total_auto_fail + total_manual_fail}</div>
        </div>
        <div class="card">
            <div class="card-label">Total Do Not Proceed</div>
            <div class="card-value dnp">{total_auto_dnp + total_manual_dnp}</div>
        </div>
        <div class="card">
            <div class="card-label">Field Missing</div>
            <div class="card-value fail">{total_auto_fm + total_manual_fm}</div>
        </div>
        <div class="card">
            <div class="card-label">Total Recon</div>
            <div class="card-value total">{total_all_val}</div>
        </div>
        <div class="card">
            <div class="card-label">Total LMS Leads</div>
            <div class="card-value lms">{total_lms}</div>
        </div>
    </div>
    
    <div class="section-title">College-Wise Recon Status</div>
    
    <div class="table-container">
        <table>
            <thead>
                <tr>
                    <th rowspan="2">College Name</th>
                    <th colspan="4" class="col-header">Auto Recon</th>
                    <th colspan="4" class="col-header">Manual Recon</th>
                    <th colspan="5" class="col-header">Total</th>
                    <th rowspan="2" class="lms">Total<br>Leads</th>
                </tr>
                <tr>
                    <th class="proceed">Proc</th>
                    <th class="fail">Fail</th>
                    <th class="dnp">DNP</th>
                    <th class="fm">FM</th>
                    <th class="proceed">Proc</th>
                    <th class="fail">Fail</th>
                    <th class="dnp">DNP</th>
                    <th class="fm">FM</th>
                    <th class="proceed">Proc</th>
                    <th class="fail">Fail</th>
                    <th class="dnp">DNP</th>
                    <th class="fm">FM</th>
                    <th class="total">Total</th>
                </tr>
            </thead>
            <tbody>
                {table_body}
                {totals_row}
            </tbody>
        </table>
    </div>
    
    <div class="footer">
        Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} IST &middot; Regular LMS API Recon Report
    </div>
</body>
</html>"""
    
    # Save to file
    filepath = f'/home/mohit/workspace/{filename}'
    with open(filepath, 'w') as f:
        f.write(html)
    
    stats = {
        'total_proceed': total_auto_proceed + total_manual_proceed,
        'total_fail': total_auto_fail + total_manual_fail,
        'total_dnp': total_auto_dnp + total_manual_dnp,
        'total_fm': total_auto_fm + total_manual_fm,
        'total_all': total_all_val,
        'total_lms': total_lms,
        'colleges': len(colleges),
        'filepath': filepath
    }
    
    return filepath, stats


# ===== MAIN EXECUTION =====
print("=" * 60)
print(f"REGULAR API RECON REPORT — {REPORT_DATE}")
print("=" * 60)

# 1. ALL Sources
print("\n--- STEP 1: Fetching ALL Sources data ---")
all_rows = fetch_all_sources_report(REPORT_DATE)
print(f"  Found {len(all_rows)} rows")
for r in all_rows:
    print(f"  {r['college_name']} | {r['sent_type']} | {r['api_sent_status']} | {r['lead_count']}")

all_matrix = transform_to_matrix(all_rows)
print(f"  Colleges: {len(all_matrix)}")

all_lms = fetch_lms_lead_counts(REPORT_DATE)
print(f"  LMS leads records: {len(all_lms)}")
for l in all_lms:
    print(f"  {l['college_name']}: {l['lms_leads']}")

all_file, all_stats = generate_html(all_matrix, REPORT_DATE, all_lms, "Regular API Recon — All Sources", f"Regular_Recon_All_{REPORT_DATE}.html")
print(f"\n✅ ALL Sources report saved: {all_file}")

# 2. Branded Campaigns
print("\n--- STEP 2: Fetching Branded Campaign data ---")
branded_student_ids = fetch_branded_student_ids(REPORT_DATE)
print(f"  Branded student IDs: {len(branded_student_ids)}")

branded_rows = fetch_branded_recon(REPORT_DATE, branded_student_ids)
print(f"  Found {len(branded_rows)} rows")
for r in branded_rows:
    print(f"  {r['college_name']} | {r['sent_type']} | {r['api_sent_status']} | {r['lead_count']}")

branded_matrix = transform_to_matrix(branded_rows)
print(f"  Colleges: {len(branded_matrix)}")

branded_lms = fetch_lms_lead_counts(REPORT_DATE, branded_student_ids)
print(f"  Branded LMS leads records: {len(branded_lms)}")
for l in branded_lms:
    print(f"  {l['college_name']}: {l['lms_leads']}")

branded_file, branded_stats = generate_html(branded_matrix, REPORT_DATE, branded_lms, "Regular API Recon — Branded Campaigns", f"Regular_Recon_Branded_{REPORT_DATE}.html")
print(f"\n✅ Branded report saved: {branded_file}")

# 3. Print summary for Telegram
print("\n" + "=" * 60)
print("SUMMARY STATS")
print("=" * 60)
print(f"\n📊 ALL SOURCES — {REPORT_DATE}")
print(f"  Total Proceed:     {all_stats['total_proceed']}")
print(f"  Total Fail:        {all_stats['total_fail']}")
print(f"  Total DNP:         {all_stats['total_dnp']}")
print(f"  Field Missing:     {all_stats['total_fm']}")
print(f"  Total Recon:       {all_stats['total_all']}")
print(f"  Total LMS Leads:   {all_stats['total_lms']}")
print(f"  Colleges:          {all_stats['colleges']}")

print(f"\n🎯 BRANDED CAMPAIGNS — {REPORT_DATE}")
print(f"  Total Proceed:     {branded_stats['total_proceed']}")
print(f"  Total Fail:        {branded_stats['total_fail']}")
print(f"  Total DNP:         {branded_stats['total_dnp']}")
print(f"  Field Missing:     {branded_stats['total_fm']}")
print(f"  Total Recon:       {branded_stats['total_all']}")
print(f"  Total LMS Leads:   {branded_stats['total_lms']}")
print(f"  Colleges:          {branded_stats['colleges']}")

print(f"\n📁 Files saved:")
print(f"  All Sources:       {all_file}")
print(f"  Branded Campaigns: {branded_file}")

# Output JSON for parsing by the delivery step
import json
print(f"\n---JSON_OUTPUT---")
print(json.dumps({
    'report_date': REPORT_DATE,
    'all_sources': all_stats,
    'branded': branded_stats,
    'files': {
        'all_sources': all_file,
        'branded': branded_file
    }
}))
print("---JSON_OUTPUT_END---")
