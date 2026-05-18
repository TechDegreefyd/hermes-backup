#!/usr/bin/env python3
"""
May 13 Lead Cohort Funnel — Source-Wise Breakdown
==================================================
Federated across 3 Regular LMS DBs: leads, attempted, connected, ICC, forms,
admissions, pre-NI — all broken down by UTM source.
"""
import asyncio
import os
import asyncpg
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv('/workspace/.env')

TARGET_DATE = '2026-05-13'

DB_CONFIGS = [
    {
        "name": "REGULAR", "source_table": "student_lead_activities",
        "host": os.getenv("REGULAR_LMS_DB_HOST"),
        "port": int(os.getenv("REGULAR_LMS_DB_PORT", "54321")),
        "database": os.getenv("REGULAR_LMS_DB_NAME"),
        "user": os.getenv("REGULAR_LMS_DB_USER"),
        "password": os.getenv("REGULAR_LMS_DB_PASSWORD"),
    },
    {
        "name": "CGC", "source_table": "student_lead_activities",
        "host": os.getenv("REGULAR_CGC_LMS_DB_HOST"),
        "port": int(os.getenv("REGULAR_CGC_LMS_DB_PORT", "54321")),
        "database": os.getenv("REGULAR_CGC_LMS_DB_NAME"),
        "user": os.getenv("REGULAR_CGC_LMS_DB_USER"),
        "password": os.getenv("REGULAR_CGC_LMS_DB_PASSWORD"),
    },
    {
        "name": "AMITY", "source_table": "student_lead_activities",
        "host": os.getenv("REGULAR_AMITY_LMS_DB_HOST"),
        "port": int(os.getenv("REGULAR_AMITY_LMS_DB_PORT", "54321")),
        "database": os.getenv("REGULAR_AMITY_LMS_DB_NAME"),
        "user": os.getenv("REGULAR_AMITY_LMS_DB_USER"),
        "password": os.getenv("REGULAR_AMITY_LMS_DB_PASSWORD"),
    },
]

# ─── SQL Queries ─────────────────────────────────────────────────────────────

# 0. Leads + source — get student_id + utm_source
LEADS_WITH_SOURCE_SQL = f"""
SELECT s.student_id, COALESCE(sla.utm_source, 'Unknown') AS utm_source
FROM students s
LEFT JOIN LATERAL (
    SELECT sla.utm_source
    FROM student_lead_activities sla
    WHERE sla.student_id = s.student_id
    ORDER BY sla.created_at ASC
    LIMIT 1
) sla ON true
WHERE (s.created_at AT TIME ZONE 'Asia/Kolkata')::date = '{TARGET_DATE}'
"""

# 1. Attempted — any remark for these leads
ATTEMPTED_SQL_TEMPLATE = """
SELECT sr.student_id
FROM student_remarks sr
WHERE sr.student_id = ANY($1::text[])
GROUP BY sr.student_id
"""

# 2. Connected — first connected on target date
CONNECTED_SQL_TEMPLATE = f"""
WITH first_conn AS (
    SELECT student_id, MIN(created_at) AS first_connected_at
    FROM student_remarks
    WHERE calling_status = 'Connected'
      AND student_id = ANY($1::text[])
    GROUP BY student_id
)
SELECT student_id
FROM first_conn
WHERE (first_connected_at AT TIME ZONE 'Asia/Kolkata')::date = '{TARGET_DATE}'
"""

# 3. ICC — first_icc_date on target date
ICC_SQL_TEMPLATE = f"""
SELECT student_id
FROM students
WHERE (first_icc_date AT TIME ZONE 'Asia/Kolkata')::date = '{TARGET_DATE}'
  AND student_id = ANY($1::text[])
"""

# 4. Forms — per DB method
FORM_REGULAR_SQL = f"""
SELECT DISTINCT s.student_id
FROM students s
JOIN student_college_api_sent_status scas ON s.student_id = scas.student_id
WHERE scas.api_sent_status = 'Proceed'
  AND (scas.created_at AT TIME ZONE 'Asia/Kolkata')::date = '{TARGET_DATE}'
  AND s.student_id = ANY($1::text[])
"""

FORM_PIPELINE_SQL = f"""
SELECT DISTINCT s.student_id
FROM students s
JOIN course_status_journeys csj ON s.student_id = csj.student_id
WHERE csj.course_status IN (
    'Form Submitted – Portal Pending', 'Form Submitted – Completed',
    'Walkin Completed', 'Walkin Marked',
    'Exam/Interview Scheduled', 'Offer Letter/Results Pending',
    'Offer Letter/Results Released', 'Ready For Admission'
)
AND (csj.created_at AT TIME ZONE 'Asia/Kolkata')::date = '{TARGET_DATE}'
AND s.student_id = ANY($1::text[])
"""

# 5. Admissions
ADM_SQL_TEMPLATE = f"""
SELECT DISTINCT s.student_id
FROM students s
JOIN course_status_journeys csj ON s.student_id = csj.student_id
WHERE csj.course_status = 'Admission'
  AND COALESCE(csj.fee_type, '') NOT ILIKE '%partial%'
  AND (csj.created_at AT TIME ZONE 'Asia/Kolkata')::date = '{TARGET_DATE}'
  AND s.student_id = ANY($1::text[])
"""

# 6. Pre NI
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
SELECT student_id
FROM first_remark
WHERE (first_remark_at AT TIME ZONE 'Asia/Kolkata')::date = '{TARGET_DATE}'
"""


async def fetch_set(conn, sql, lead_ids):
    """Return set of student_ids matching the query."""
    rows = await conn.fetch(sql, lead_ids)
    return {str(r["student_id"]) for r in rows}


async def main():
    # source → {leads, attempted, connected, icc, forms, admissions, pre_ni} SETS
    sources = defaultdict(lambda: {
        "leads": set(), "attempted": set(), "connected": set(),
        "icc": set(), "forms": set(), "admissions": set(), "pre_ni": set()
    })

    for db in DB_CONFIGS:
        name = db["name"]
        print(f"Querying {name} DB...", flush=True)

        conn = await asyncpg.connect(
            host=db["host"], port=db["port"],
            database=db["database"], user=db["user"], password=db["password"]
        )

        # Get leads + source
        rows = await conn.fetch(LEADS_WITH_SOURCE_SQL)
        lead_source_map = {str(r["student_id"]): (r["utm_source"] or "Unknown") for r in rows}
        lead_ids = list(lead_source_map.keys())

        if not lead_ids:
            print(f"  No leads")
            await conn.close()
            continue

        print(f"  Leads: {len(lead_ids)}", flush=True)

        # Assign leads to source
        for sid, src in lead_source_map.items():
            src_key = src.strip() if src.strip() else "Unknown"
            sources[src_key]["leads"].add(f"{name}:{sid}")

        # Attempted
        attempted = await fetch_set(conn, ATTEMPTED_SQL_TEMPLATE, lead_ids)
        for sid in attempted:
            src = lead_source_map.get(sid, "Unknown")
            src = src.strip() or "Unknown"
            sources[src]["attempted"].add(f"{name}:{sid}")

        # Connected
        connected = await fetch_set(conn, CONNECTED_SQL_TEMPLATE, lead_ids)
        for sid in connected:
            src = lead_source_map.get(sid, "Unknown")
            src = src.strip() or "Unknown"
            sources[src]["connected"].add(f"{name}:{sid}")

        # ICC
        icc = await fetch_set(conn, ICC_SQL_TEMPLATE, lead_ids)
        for sid in icc:
            src = lead_source_map.get(sid, "Unknown")
            src = src.strip() or "Unknown"
            sources[src]["icc"].add(f"{name}:{sid}")

        # Forms
        if name == "REGULAR":
            forms = await fetch_set(conn, FORM_REGULAR_SQL, lead_ids)
        else:
            forms = await fetch_set(conn, FORM_PIPELINE_SQL, lead_ids)
        for sid in forms:
            src = lead_source_map.get(sid, "Unknown")
            src = src.strip() or "Unknown"
            sources[src]["forms"].add(f"{name}:{sid}")

        # Admissions
        adm = await fetch_set(conn, ADM_SQL_TEMPLATE, lead_ids)
        for sid in adm:
            src = lead_source_map.get(sid, "Unknown")
            src = src.strip() or "Unknown"
            sources[src]["admissions"].add(f"{name}:{sid}")

        # Pre NI
        ni = await fetch_set(conn, PRE_NI_SQL_TEMPLATE, lead_ids)
        for sid in ni:
            src = lead_source_map.get(sid, "Unknown")
            src = src.strip() or "Unknown"
            sources[src]["pre_ni"].add(f"{name}:{sid}")

        await conn.close()

    # ─── Print Summary Table ─────────────────────────────────────────────────
    print()
    print(f"{'='*120}")
    print(f"  MAY 13 2026 — LEAD COHORT FUNNEL BY SOURCE")
    print(f"{'='*120}")
    print(f"{'Source':<30s} {'Leads':>6s} {'Attempt':>7s} {'Conn':>5s} {'ICC':>5s} {'Forms':>6s} {'Adm':>5s} {'PreNI':>6s} │ {'Conn%':>6s} {'ICC%':>6s} {'L→F%':>6s} {'F→A%':>6s} {'L→A%':>6s} {'PreNI%':>6s}")
    print(f"{'─'*120}")

    total = {"leads": 0, "attempted": 0, "connected": 0, "icc": 0, "forms": 0, "admissions": 0, "pre_ni": 0}

    for src in sorted(sources.keys(), key=lambda s: len(sources[s]["leads"]), reverse=True):
        d = sources[src]
        L = len(d["leads"])
        A = len(d["attempted"])
        C = len(d["connected"])
        I = len(d["icc"])
        F = len(d["forms"])
        AD = len(d["admissions"])
        NI = len(d["pre_ni"])

        conn_pct = f"{(C/A*100):.0f}%" if A else "-"
        icc_pct = f"{(I/L*100):.0f}%" if L else "-"
        l2f_pct = f"{(F/L*100):.0f}%" if L else "-"
        f2a_pct = f"{(AD/F*100):.0f}%" if F else "-"
        l2a_pct = f"{(AD/L*100):.0f}%" if L else "-"
        ni_pct = f"{(NI/L*100):.0f}%" if L else "-"

        print(f"{src:<30s} {L:>6d} {A:>7d} {C:>5d} {I:>5d} {F:>6d} {AD:>5d} {NI:>6d} │ {conn_pct:>6s} {icc_pct:>6s} {l2f_pct:>6s} {f2a_pct:>6s} {l2a_pct:>6s} {ni_pct:>6s}")

        for k_key in ["leads", "attempted", "connected", "icc", "forms", "admissions", "pre_ni"]:
            total[k_key] += {"leads": L, "attempted": A, "connected": C, "icc": I, "forms": F, "admissions": AD, "pre_ni": NI}[k_key]

    # Total row
    L, A, C, I, F, AD, NI = total.values()
    conn_pct = f"{(C/A*100):.1f}%" if A else "-"
    icc_pct = f"{(I/L*100):.1f}%" if L else "-"
    l2f_pct = f"{(F/L*100):.1f}%" if L else "-"
    f2a_pct = f"{(AD/F*100):.1f}%" if F else "-"
    l2a_pct = f"{(AD/L*100):.1f}%" if L else "-"
    ni_pct = f"{(NI/L*100):.1f}%" if L else "-"

    print(f"{'─'*120}")
    print(f"{'TOTAL':<30s} {L:>6d} {A:>7d} {C:>5d} {I:>5d} {F:>6d} {AD:>5d} {NI:>6d} │ {conn_pct:>6s} {icc_pct:>6s} {l2f_pct:>6s} {f2a_pct:>6s} {l2a_pct:>6s} {ni_pct:>6s}")
    print(f"{'='*120}")


if __name__ == "__main__":
    asyncio.run(main())
