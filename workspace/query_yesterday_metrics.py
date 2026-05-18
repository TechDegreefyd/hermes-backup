#!/usr/bin/env python3
"""Query online LMS for counsellor-wise daily metrics on May 13, 2026."""
import asyncio, asyncpg, os

from datetime import date
TARGET_DATE = date(2026, 5, 13)

async def main():
    # Load .env
    for line in open('/workspace/.env'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        k, _, v = line.partition('=')
        os.environ[k.strip()] = v.strip()

    conn = await asyncpg.connect(
        host=os.environ['ONLINE_LMS_DB_HOST'],
        port=int(os.environ['ONLINE_LMS_DB_PORT']),
        user=os.environ['ONLINE_LMS_DB_USER'],
        password=os.environ['ONLINE_LMS_DB_PASSWORD'],
        database=os.environ['ONLINE_LMS_DB_NAME']
    )

    # 1) Total Students with Remarks (counsellor-wise)
    print("=== METRIC 1: Students with Remarks ===")
    rows = await conn.fetch("""
        SELECT sr.counsellor_id, c.counsellor_name,
               COUNT(DISTINCT sr.student_id) AS students_with_remarks
        FROM student_remarks sr
        LEFT JOIN counsellors c ON sr.counsellor_id = c.counsellor_id
        WHERE (sr.created_at AT TIME ZONE 'Asia/Kolkata')::date = $1
          AND sr.isdisabled = false
        GROUP BY sr.counsellor_id, c.counsellor_name
        ORDER BY students_with_remarks DESC
    """, TARGET_DATE)
    for r in rows:
        print(f"  {r['counsellor_name'] or r['counsellor_id']}: {r['students_with_remarks']}")
    print(f"  TOTAL: {sum(r['students_with_remarks'] for r in rows)}")

    # 2) First Connected — first-ever Connected call per student, attributed to who made it
    print("\n=== METRIC 2: First Connected ===")
    rows = await conn.fetch("""
        WITH first_conn AS (
            SELECT student_id, MIN(created_at) AS first_connected_at
            FROM student_remarks
            WHERE calling_status = 'Connected' AND isdisabled = false
            GROUP BY student_id
        ),
        first_conn_detail AS (
            SELECT DISTINCT ON (fc.student_id)
                fc.student_id, fc.first_connected_at, fc_r.counsellor_id
            FROM first_conn fc
            JOIN student_remarks fc_r
                ON fc.student_id = fc_r.student_id
               AND fc_r.created_at = fc.first_connected_at
               AND fc_r.calling_status = 'Connected'
               AND fc_r.isdisabled = false
        )
        SELECT fc_d.counsellor_id, c.counsellor_name, COUNT(*) AS first_connected
        FROM first_conn_detail fc_d
        LEFT JOIN counsellors c ON fc_d.counsellor_id = c.counsellor_id
        WHERE (fc_d.first_connected_at AT TIME ZONE 'Asia/Kolkata')::date = $1
        GROUP BY fc_d.counsellor_id, c.counsellor_name
        ORDER BY first_connected DESC
    """, TARGET_DATE)
    for r in rows:
        print(f"  {r['counsellor_name'] or r['counsellor_id']}: {r['first_connected']}")
    print(f"  TOTAL: {sum(r['first_connected'] for r in rows)}")

    # 3) First ICC — students whose first_Icc_Date falls on target day
    # Attributed to the assigned counsellor (owner of the lead)
    print("\n=== METRIC 3: First ICC ===")
    rows = await conn.fetch("""
        SELECT COALESCE(c.counsellor_name, s.assigned_counsellor_id::text) AS counsellor,
               COUNT(DISTINCT s.student_id) AS first_icc
        FROM students s
        LEFT JOIN counsellors c ON s.assigned_counsellor_id = c.counsellor_id AND c.role = 'l2'
        WHERE s."first_Icc_Date" >= $1::date - INTERVAL '1 day' + INTERVAL '18 hours 30 minutes'
          AND s."first_Icc_Date" < $1::date + INTERVAL '18 hours 30 minutes'
          AND s.assigned_counsellor_id IS NOT NULL
        GROUP BY s.assigned_counsellor_id, c.counsellor_name
        ORDER BY first_icc DESC
    """, TARGET_DATE)
    for r in rows:
        print(f"  {r['counsellor']}: {r['first_icc']}")
    print(f"  TOTAL: {sum(r['first_icc'] for r in rows)}")

    # 4) First NI — first-ever remark of currently-NI students, on target day
    print("\n=== METRIC 4: First NI ===")
    rows = await conn.fetch("""
        WITH first_ni AS (
            SELECT sr.counsellor_id, COUNT(DISTINCT sr.student_id) AS first_ni
            FROM (
                SELECT DISTINCT ON (sr.student_id)
                    sr.student_id, sr.counsellor_id, sr.created_at AS first_remark_at
                FROM student_remarks sr
                INNER JOIN students s ON sr.student_id = s.student_id
                WHERE s.current_student_status = 'NotInterested'
                  AND sr.isdisabled = false
                ORDER BY sr.student_id, sr.created_at ASC
            ) sr
            WHERE (sr.first_remark_at AT TIME ZONE 'Asia/Kolkata')::date = $1
            GROUP BY sr.counsellor_id
        )
        SELECT COALESCE(c.counsellor_name, fn.counsellor_id::text) AS counsellor, fn.first_ni
        FROM first_ni fn
        LEFT JOIN counsellors c ON fn.counsellor_id = c.counsellor_id AND c.role = 'l2'
        ORDER BY first_ni DESC
    """, TARGET_DATE)
    for r in rows:
        print(f"  {r['counsellor']}: {r['first_ni']}")
    print(f"  TOTAL: {sum(r['first_ni'] for r in rows)}")

    await conn.close()

asyncio.run(main())
