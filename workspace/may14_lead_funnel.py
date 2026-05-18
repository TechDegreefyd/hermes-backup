#!/usr/bin/env python3
"""
May 14 Lead Cohort Funnel Report
================================
Query all 3 Regular LMS databases for leads created on 2026-05-14,
then count: Attempts, Connected, ICC, Forms, Admissions, Pre-NI.
"""
import asyncio
import os
import sys
import asyncpg
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv('/workspace/.env')

TARGET_DATE = '2026-05-13'

DB_CONFIGS = [
    {
        "name": "REGULAR",
        "host": os.getenv("REGULAR_LMS_DB_HOST"),
        "port": int(os.getenv("REGULAR_LMS_DB_PORT", "54321")),
        "database": os.getenv("REGULAR_LMS_DB_NAME"),
        "user": os.getenv("REGULAR_LMS_DB_USER"),
        "password": os.getenv("REGULAR_LMS_DB_PASSWORD"),
    },
    {
        "name": "CGC",
        "host": os.getenv("REGULAR_CGC_LMS_DB_HOST"),
        "port": int(os.getenv("REGULAR_CGC_LMS_DB_PORT", "54321")),
        "database": os.getenv("REGULAR_CGC_LMS_DB_NAME"),
        "user": os.getenv("REGULAR_CGC_LMS_DB_USER"),
        "password": os.getenv("REGULAR_CGC_LMS_DB_PASSWORD"),
    },
    {
        "name": "AMITY",
        "host": os.getenv("REGULAR_AMITY_LMS_DB_HOST"),
        "port": int(os.getenv("REGULAR_AMITY_LMS_DB_PORT", "54321")),
        "database": os.getenv("REGULAR_AMITY_LMS_DB_NAME"),
        "user": os.getenv("REGULAR_AMITY_LMS_DB_USER"),
        "password": os.getenv("REGULAR_AMITY_LMS_DB_PASSWORD"),
    },
]

# ─── Queries ─────────────────────────────────────────────────────────────────

# 1. LEADS created on target date
LEADS_SQL = f"""
SELECT student_id
FROM students
WHERE (created_at AT TIME ZONE 'Asia/Kolkata')::date = '{TARGET_DATE}'
"""

# 2. ATTEMPTED — any remark exists for these leads
ATTEMPTED_SQL_TEMPLATE = """
SELECT COUNT(DISTINCT sr.student_id) AS cnt
FROM student_remarks sr
WHERE sr.student_id = ANY($1::text[])
"""

# 3. CONNECTED — first connected (MIN created_at for calling_status='Connected') on target date
CONNECTED_SQL_TEMPLATE = f"""
WITH first_conn AS (
    SELECT student_id, MIN(created_at) AS first_connected_at
    FROM student_remarks
    WHERE calling_status = 'Connected'
      AND student_id = ANY($1::text[])
    GROUP BY student_id
)
SELECT COUNT(*) AS cnt
FROM first_conn
WHERE (first_connected_at AT TIME ZONE 'Asia/Kolkata')::date = '{TARGET_DATE}'
"""

# 4. ICC — first_icc_date on target date (lowercase for Regular)
ICC_SQL_TEMPLATE = f"""
SELECT COUNT(*) AS cnt
FROM students
WHERE (first_icc_date AT TIME ZONE 'Asia/Kolkata')::date = '{TARGET_DATE}'
  AND student_id = ANY($1::text[])
"""

# 5. FORMS — per DB method
# Regular: api_sent_status = 'Proceed'
FORM_REGULAR_SQL = f"""
SELECT COUNT(DISTINCT s.student_id) AS cnt
FROM students s
JOIN student_college_api_sent_status scas ON s.student_id = scas.student_id
WHERE scas.api_sent_status = 'Proceed'
  AND (scas.created_at AT TIME ZONE 'Asia/Kolkata')::date = '{TARGET_DATE}'
  AND s.student_id = ANY($1::text[])
"""

# CGC & Amity: pipeline statuses
FORM_PIPELINE_SQL = f"""
SELECT COUNT(DISTINCT s.student_id) AS cnt
FROM students s
JOIN course_status_journeys csj ON s.student_id = csj.student_id
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
AND (csj.created_at AT TIME ZONE 'Asia/Kolkata')::date = '{TARGET_DATE}'
AND s.student_id = ANY($1::text[])
"""

# 6. ADMISSIONS
ADM_SQL_TEMPLATE = f"""
SELECT COUNT(DISTINCT s.student_id) AS cnt
FROM students s
JOIN course_status_journeys csj ON s.student_id = csj.student_id
WHERE csj.course_status = 'Admission'
  AND COALESCE(csj.fee_type, '') NOT ILIKE '%partial%'
  AND (csj.created_at AT TIME ZONE 'Asia/Kolkata')::date = '{TARGET_DATE}'
  AND s.student_id = ANY($1::text[])
"""

# 7. PRE NI — students who went NotInterested on target date
PRE_NI_SQL_TEMPLATE = f"""
WITH ni_students AS (
    SELECT student_id FROM students
    WHERE current_student_status = 'NotInterested'
      AND student_id = ANY($1::text[])
),
first_remark AS (
    SELECT DISTINCT ON (sr.student_id) sr.student_id, sr.created_at AS first_remark_at
    FROM student_remarks sr
    JOIN ni_students ns ON sr.student_id = ns.student_id
    ORDER BY sr.student_id, sr.created_at ASC
)
SELECT COUNT(*) AS cnt
FROM first_remark
WHERE (first_remark_at AT TIME ZONE 'Asia/Kolkata')::date = '{TARGET_DATE}'
"""


async def main():
    all_leads = []
    results = {"regular": {}, "cgc": {}, "amity": {}}

    for db in DB_CONFIGS:
        name = db["name"]
        print(f"\n{'='*60}")
        print(f"  Querying {name} DB...")
        print(f"{'='*60}")

        conn = await asyncpg.connect(
            host=db["host"], port=db["port"],
            database=db["database"], user=db["user"], password=db["password"]
        )

        # 1. Get lead IDs
        rows = await conn.fetch(LEADS_SQL)
        lead_ids = [str(r["student_id"]) for r in rows]
        all_leads.extend(lead_ids)
        print(f"  Leads created on {TARGET_DATE}: {len(lead_ids)}")

        if not lead_ids:
            results[name.lower()] = {
                "leads": 0, "attempted": 0, "connected": 0,
                "icc": 0, "forms": 0, "admissions": 0, "pre_ni": 0
            }
            await conn.close()
            continue

        # 2. Attempted
        row = await conn.fetchrow(ATTEMPTED_SQL_TEMPLATE, lead_ids)
        attempted = row["cnt"]
        print(f"  Attempted (any remark): {attempted}")

        # 3. Connected (first connected on target date)
        row = await conn.fetchrow(CONNECTED_SQL_TEMPLATE, lead_ids)
        connected = row["cnt"]
        print(f"  Connected (first on {TARGET_DATE}): {connected}")

        # 4. ICC
        row = await conn.fetchrow(ICC_SQL_TEMPLATE, lead_ids)
        icc = row["cnt"]
        print(f"  ICC Done (first_icc_date={TARGET_DATE}): {icc}")

        # 5. Forms (per-DB method)
        if name == "REGULAR":
            row = await conn.fetchrow(FORM_REGULAR_SQL, lead_ids)
        else:
            row = await conn.fetchrow(FORM_PIPELINE_SQL, lead_ids)
        forms = row["cnt"]
        print(f"  Forms: {forms}")

        # 6. Admissions
        row = await conn.fetchrow(ADM_SQL_TEMPLATE, lead_ids)
        admissions = row["cnt"]
        print(f"  Admissions: {admissions}")

        # 7. Pre NI
        row = await conn.fetchrow(PRE_NI_SQL_TEMPLATE, lead_ids)
        pre_ni = row["cnt"]
        print(f"  Pre NI: {pre_ni}")

        results[name.lower()] = {
            "leads": len(lead_ids),
            "attempted": attempted,
            "connected": connected,
            "icc": icc,
            "forms": forms,
            "admissions": admissions,
            "pre_ni": pre_ni,
        }

        await conn.close()

    # ─── Combine totals ─────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  COMBINED TOTALS (All 3 DBs)")
    print(f"{'='*60}")

    totals = {}
    for k in ["leads", "attempted", "connected", "icc", "forms", "admissions", "pre_ni"]:
        totals[k] = sum(results[db][k] for db in results)

    L = totals["leads"]
    A = totals["attempted"]
    C = totals["connected"]
    I = totals["icc"]
    F = totals["forms"]
    AD = totals["admissions"]
    NI = totals["pre_ni"]

    # Connected among leads that had attempts
    pre_ni_pct = f"{(NI / L * 100):.1f}%" if L else "N/A"
    conn_pct = f"{(C / A * 100):.1f}%" if A else "N/A"
    icc_pct = f"{(I / L * 100):.1f}%" if L else "N/A"
    l2f_pct = f"{(F / L * 100):.1f}%" if L else "N/A"
    f2a_pct = f"{(AD / F * 100):.1f}%" if F else "N/A"
    l2a_pct = f"{(AD / L * 100):.1f}%" if L else "N/A"

    print(f"\n{'─'*55}")
    print(f"  May 14 Lead Cohort Funnel — FINAL SUMMARY")
    print(f"{'─'*55}")
    print(f"  Total Leads (May 14):              {L:>6}")
    print(f"  └─ Attempted (any remark):         {A:>6}")
    print(f"     └─ Connected (first today):     {C:>6}   → {conn_pct} of Attempted")
    print(f"  └─ ICC Done (today):               {I:>6}   → {icc_pct} of Leads")
    print(f"  └─ Forms (today):                  {F:>6}   → {l2f_pct} of Leads")
    print(f"     └─ Admissions (today):          {AD:>6}   → {f2a_pct} of Forms")
    print(f"  └─ Pre NI (today):                 {NI:>6}   → {pre_ni_pct} of Leads")
    print(f"{'─'*55}")
    print(f"  Lead → Form:                        {l2f_pct}")
    print(f"  Form → Admission:                   {f2a_pct}")
    print(f"  Lead → Admission:                   {l2a_pct}")
    print(f"  Pre NI %:                           {pre_ni_pct}")
    print(f"  Connected % (of attempted):         {conn_pct}")
    print(f"  ICC % (of leads):                   {icc_pct}")
    print(f"{'─'*55}")

    # DB breakdown
    for db_name in ["regular", "cgc", "amity"]:
        r = results[db_name]
        print(f"  {db_name.upper():8s} → L={r['leads']:4d}  A={r['attempted']:4d}  C={r['connected']:4d}  ICC={r['icc']:4d}  F={r['forms']:4d}  AD={r['admissions']:4d}  NI={r['pre_ni']:4d}")


if __name__ == "__main__":
    asyncio.run(main())
