import asyncio
import os
import pandas as pd
import asyncpg
from dotenv import load_dotenv

load_dotenv('/workspace/.env')

DB_CONFIGS = [
    {
        "name": "REGULAR",
        "host": os.getenv("REGULAR_LMS_DB_HOST"),
        "port": int(os.getenv("REGULAR_LMS_DB_PORT", "54321")),
        "database": os.getenv("REGULAR_LMS_DB_NAME"),
        "user": os.getenv("REGULAR_LMS_DB_USER"),
        "password": os.getenv("REGULAR_LMS_DB_PASSWORD")
    },
    {
        "name": "CGC",
        "host": os.getenv("REGULAR_CGC_LMS_DB_HOST"),
        "port": int(os.getenv("REGULAR_CGC_LMS_DB_PORT", "54321")),
        "database": os.getenv("REGULAR_CGC_LMS_DB_NAME"),
        "user": os.getenv("REGULAR_CGC_LMS_DB_USER"),
        "password": os.getenv("REGULAR_CGC_LMS_DB_PASSWORD")
    },
    {
        "name": "AMITY",
        "host": os.getenv("REGULAR_AMITY_LMS_DB_HOST"),
        "port": int(os.getenv("REGULAR_AMITY_LMS_DB_PORT", "54321")),
        "database": os.getenv("REGULAR_AMITY_LMS_DB_NAME"),
        "user": os.getenv("REGULAR_AMITY_LMS_DB_USER"),
        "password": os.getenv("REGULAR_AMITY_LMS_DB_PASSWORD")
    }
]

ADM_SQL = """
SELECT DISTINCT ON (s.student_id, uc.course_id)
    s.student_id,
    s.student_name,
    csj.created_at AT TIME ZONE 'Asia/Kolkata' AS admission_date,
    uc.course_id,
    uc.university_name AS college_name,
    uc.course_name,
    INITCAP(TRIM(csj.fee_type)) AS fee_type,
    uc.total_fees AS total_fee,
    uc.semester_fees AS sem_fee,
    uc.annual_fees AS annual_fee,
    csj.deposit_amount AS fee_deposit,
    uc.duration || ' ' || uc.duration_type AS course_duration,
    c.counsellor_name,
    c.counsellor_id,
    sup.counsellor_name AS supervisor_name
FROM students s
JOIN course_status_journeys csj ON s.student_id = csj.student_id
JOIN university_courses uc ON csj.course_id = uc.course_id
LEFT JOIN counsellors c ON s.assigned_counsellor_id = c.counsellor_id
LEFT JOIN counsellors sup ON c.assigned_to = sup.counsellor_id
WHERE csj.course_status = 'Admission'
  AND csj.fee_type NOT IN ('partial paid', 'Partially Paid', 'Partial Done', 'Partial Paid')
  AND s.student_id IN (SELECT student_id FROM students)
ORDER BY s.student_id, uc.course_id, csj.created_at ASC;
"""

FORM_SQL = """
SELECT DISTINCT ON (s.student_id, csj.course_id)
    s.student_id,
    s.student_name,
    s.student_email,
    csj.created_at AT TIME ZONE 'Asia/Kolkata' AS formfilled_date,
    csj.course_id,
    uc.university_name AS college_name,
    uc.course_name,
    csj.fee_type,
    uc.total_fees AS total_fee,
    uc.semester_fees AS sem_fee,
    uc.annual_fees AS annual_fee,
    csj.deposit_amount AS fee_deposit,
    uc.duration || ' ' || uc.duration_type AS course_duration,
    c.counsellor_name,
    c.counsellor_id,
    sup.counsellor_name AS supervisor_name
FROM students s
JOIN course_status_journeys csj ON s.student_id = csj.student_id
JOIN university_courses uc ON csj.course_id = uc.course_id
LEFT JOIN counsellors c ON csj.counsellor_id = c.counsellor_id
LEFT JOIN counsellors sup ON c.assigned_to = sup.counsellor_id
WHERE csj.course_status in ('Form Submitted – Portal Pending',
                          'Form Submitted – Completed',
                          'Walkin Completed',
                          'Exam/Interview Scheduled',
                          'Offer Letter/Results Pending',
                          'Offer Letter/Results Released',
                          'Ready For Admission')
  AND s.student_id IN (SELECT student_id FROM students)
ORDER BY s.student_id, csj.course_id, csj.created_at Asc;
"""

async def fetch_all():
    all_adm = []
    all_form = []
    for db in DB_CONFIGS:
        print(f"Connecting to {db['name']}...")
        try:
            conn = await asyncpg.connect(
                host=db['host'], port=db['port'], database=db['database'], user=db['user'], password=db['password']
            )
            adm_rows = await conn.fetch(ADM_SQL)
            form_rows = await conn.fetch(FORM_SQL)
            await conn.close()
            
            df_adm = pd.DataFrame([dict(r) for r in adm_rows])
            df_form = pd.DataFrame([dict(r) for r in form_rows])
            df_adm['source_db'] = db['name']
            df_form['source_db'] = db['name']
            
            all_adm.append(df_adm)
            all_form.append(df_form)
            print(f"Fetched {len(df_adm)} admissions and {len(df_form)} forms from {db['name']}.")
        except Exception as e:
            print(f"Error fetching from {db['name']}: {e}")
            
    df_adm_all = pd.concat(all_adm, ignore_index=True) if all_adm else pd.DataFrame()
    df_form_all = pd.concat(all_form, ignore_index=True) if all_form else pd.DataFrame()
    
    return df_adm_all, df_form_all

async def main():
    df_adm, df_form = await fetch_all()

    print("\n--- Counselors Found ---")
    if not df_adm.empty:
        print(df_adm['counsellor_name'].unique())

    print("\n--- Supervisors Found ---")
    if not df_adm.empty:
        print(df_adm['supervisor_name'].unique())

    print("\n--- Colleges Found ---")
    if not df_adm.empty:
        print(df_adm['college_name'].unique())

if __name__ == "__main__":
    asyncio.run(main())
