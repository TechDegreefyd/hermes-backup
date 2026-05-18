import os, asyncpg, asyncio
from datetime import date
from dotenv import load_dotenv
load_dotenv()

TARGET = date(2026, 5, 13)
TARGET_STR = '2026-05-13'

async def main():
    conn = await asyncpg.connect(
        host=os.environ['ONLINE_LMS_DB_HOST'],
        port=int(os.environ['ONLINE_LMS_DB_PORT']),
        database=os.environ['ONLINE_LMS_DB_NAME'],
        user=os.environ['ONLINE_LMS_DB_USER'],
        password=os.environ['ONLINE_LMS_DB_PASSWORD']
    )
    
    # 1. LEADS on May 13 by source
    leads = await conn.fetch('''
        SELECT COALESCE(NULLIF(TRIM(s.source), ''), 'Unknown') AS source,
               COUNT(*) AS cnt
        FROM students s
        WHERE (s.created_at AT TIME ZONE 'Asia/Kolkata')::date = $1
        GROUP BY COALESCE(NULLIF(TRIM(s.source), ''), 'Unknown')
        ORDER BY cnt DESC
    ''', TARGET)
    
    lead_map = {r['source']: r['cnt'] for r in leads}
    total_leads = sum(lead_map.values())
    
    # Get student_id -> source mapping for May 13
    lead_ids_rows = await conn.fetch('''
        SELECT s.student_id, COALESCE(NULLIF(TRIM(s.source), ''), 'Unknown') AS source
        FROM students s
        WHERE (s.created_at AT TIME ZONE 'Asia/Kolkata')::date = $1
    ''', TARGET)
    
    lead_ids = [r['student_id'] for r in lead_ids_rows]
    lead_source_map = {r['student_id']: r['source'] for r in lead_ids_rows}
    
    # 2. ATTEMPTED (any remark exists)
    attempted_ids = set()
    if lead_ids:
        attempted_rows = await conn.fetch('''
            SELECT DISTINCT sr.student_id
            FROM student_remarks sr
            WHERE sr.student_id = ANY($1::varchar[])
        ''', lead_ids)
        attempted_ids = set(r['student_id'] for r in attempted_rows)
    
    # 3. FIRST CONNECTED on May 13
    first_conn_rows = await conn.fetch('''
        WITH first_conn AS (
            SELECT student_id, MIN(created_at) AS first_connected_at
            FROM student_remarks
            WHERE calling_status = 'Connected'
            GROUP BY student_id
        )
        SELECT fc.student_id
        FROM first_conn fc
        WHERE (fc.first_connected_at AT TIME ZONE 'Asia/Kolkata')::date = $1
    ''', TARGET)
    first_conn_ids = set(r['student_id'] for r in first_conn_rows)
    
    # 4. FIRST ICC on May 13
    icc_rows = await conn.fetch('''
        SELECT s.student_id
        FROM students s
        WHERE (s."first_Icc_Date" AT TIME ZONE 'Asia/Kolkata')::date = $1
    ''', TARGET)
    icc_ids = set(r['student_id'] for r in icc_rows)
    
    # 5. FORMS on May 13
    form_rows = await conn.fetch('''
        SELECT DISTINCT ON (s.student_id) s.student_id
        FROM students s
        JOIN course_status_journeys csj ON s.student_id = csj.student_id
        WHERE csj.course_status = 'Application'
          AND (csj.created_at AT TIME ZONE 'Asia/Kolkata')::date = $1
        ORDER BY s.student_id, csj.created_at ASC
    ''', TARGET)
    form_ids = set(r['student_id'] for r in form_rows)
    
    # 6. ADMISSIONS on May 13
    adm_rows = await conn.fetch('''
        SELECT DISTINCT ON (s.student_id, uc.course_id) s.student_id
        FROM students s
        JOIN course_status_journeys csj ON s.student_id = csj.student_id
        JOIN university_courses uc ON csj.course_id = uc.course_id
        WHERE csj.course_status = 'Admission'
          AND csj.fee_type NOT ILIKE '%partial%'
          AND (csj.created_at AT TIME ZONE 'Asia/Kolkata')::date = $1
        ORDER BY s.student_id, uc.course_id, csj.created_at ASC
    ''', TARGET)
    adm_ids = set(r['student_id'] for r in adm_rows)
    
    # 7. PRE NI on May 13
    ni_rows = await conn.fetch('''
        WITH ni_students AS (
            SELECT student_id FROM students
            WHERE current_student_status = 'NotInterested'
        ),
        first_remark AS (
            SELECT DISTINCT ON (sr.student_id)
                sr.student_id, sr.created_at AS first_remark_at
            FROM student_remarks sr
            JOIN ni_students ns ON sr.student_id = ns.student_id
            ORDER BY sr.student_id, sr.created_at ASC
        )
        SELECT fr.student_id
        FROM first_remark fr
        JOIN ni_students ns ON fr.student_id = ns.student_id
        WHERE (fr.first_remark_at AT TIME ZONE 'Asia/Kolkata')::date = $1
    ''', TARGET)
    ni_ids = set(r['student_id'] for r in ni_rows)
    
    # Build per-source data
    sources = sorted(lead_map.keys(), key=lambda s: lead_map[s], reverse=True)
    source_data = {}
    for src in sources:
        src_lead_ids = [sid for sid, s in lead_source_map.items() if s == src]
        n = len(src_lead_ids)
        source_data[src] = {
            'leads': n,
            'attempted': sum(1 for sid in src_lead_ids if sid in attempted_ids),
            'connected': sum(1 for sid in src_lead_ids if sid in first_conn_ids),
            'icc': sum(1 for sid in src_lead_ids if sid in icc_ids),
            'forms': sum(1 for sid in src_lead_ids if sid in form_ids),
            'admissions': sum(1 for sid in src_lead_ids if sid in adm_ids),
            'pre_ni': sum(1 for sid in src_lead_ids if sid in ni_ids),
        }
    
    # Print table
    header = f"{'Source':<25} {'Leads':>6} {'Att':>5} {'Conn':>5} {'ICC':>5} {'Forms':>6} {'Adm':>5} {'PreNI':>6}  {'Conn%':>7} {'ICC%':>6} {'L>F%':>6} {'F>A%':>6} {'L>A%':>6} {'PNI%':>6}"
    print(header)
    print('-' * len(header))
    
    totals = {'leads':0,'attempted':0,'connected':0,'icc':0,'forms':0,'admissions':0,'pre_ni':0}
    for src in sources:
        d = source_data[src]
        for k in totals:
            totals[k] += d[k]
        cp = d['connected']/d['leads']*100 if d['leads'] else 0
        ip = d['icc']/d['leads']*100 if d['leads'] else 0
        lf = d['forms']/d['leads']*100 if d['leads'] else 0
        fa = d['admissions']/d['forms']*100 if d['forms'] else 0
        la = d['admissions']/d['leads']*100 if d['leads'] else 0
        np = d['pre_ni']/d['leads']*100 if d['leads'] else 0
        print(f"{src:<25} {d['leads']:>6} {d['attempted']:>5} {d['connected']:>5} {d['icc']:>5} {d['forms']:>6} {d['admissions']:>5} {d['pre_ni']:>6}  {cp:>6.1f}% {ip:>5.1f}% {lf:>5.1f}% {fa:>5.1f}% {la:>5.1f}% {np:>5.1f}%")
    
    print('-' * len(header))
    t = totals
    cp = t['connected']/t['leads']*100 if t['leads'] else 0
    ip = t['icc']/t['leads']*100 if t['leads'] else 0
    lf = t['forms']/t['leads']*100 if t['leads'] else 0
    fa = t['admissions']/t['forms']*100 if t['forms'] else 0
    la = t['admissions']/t['leads']*100 if t['leads'] else 0
    np = t['pre_ni']/t['leads']*100 if t['leads'] else 0
    print(f"{'TOTAL':<25} {t['leads']:>6} {t['attempted']:>5} {t['connected']:>5} {t['icc']:>5} {t['forms']:>6} {t['admissions']:>5} {t['pre_ni']:>6}  {cp:>6.1f}% {ip:>5.1f}% {lf:>5.1f}% {fa:>5.1f}% {la:>5.1f}% {np:>5.1f}%")
    
    print()
    print("COLUMN LEGEND:")
    print(f"  Leads  = students created on {TARGET_STR}")
    print(f"  Att    = leads with ≥1 remark (attempted)")
    print(f"  Conn   = first ever Connected call happened on {TARGET_STR}")
    print(f"  ICC    = first_Icc_Date falls on {TARGET_STR}")
    print(f"  Forms  = Application status on {TARGET_STR}")
    print(f"  Adm    = Admission (excl partial) on {TARGET_STR}")
    print(f"  PreNI  = NI student whose first remark falls on {TARGET_STR}")
    print(f"  Conn%  = Connected / Leads")
    print(f"  ICC%   = ICC / Leads")
    print(f"  L>F%   = Lead to Form %")
    print(f"  F>A%   = Form to Admission %")
    print(f"  L>A%   = Lead to Admission %")
    print(f"  PNI%   = Pre NI %")

    await conn.close()

asyncio.run(main())
