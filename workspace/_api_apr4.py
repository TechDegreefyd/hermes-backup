import os, asyncpg, asyncio
from datetime import date
from dotenv import load_dotenv
load_dotenv()

TARGET = date(2026, 4, 4)

async def main():
    conn = await asyncpg.connect(
        host=os.environ['REGULAR_LMS_DB_HOST'],
        port=int(os.environ['REGULAR_LMS_DB_PORT']),
        database=os.environ['REGULAR_LMS_DB_NAME'],
        user=os.environ['REGULAR_LMS_DB_USER'],
        password=os.environ['REGULAR_LMS_DB_PASSWORD']
    )

    # Raw pivot: sent_type x api_sent_status x COUNT(DISTINCT student_id)
    rows = await conn.fetch('''
        SELECT sent_type, api_sent_status, COUNT(DISTINCT student_id) AS cnt
        FROM student_college_api_sent_status
        WHERE DATE(created_at AT TIME ZONE 'Asia/Kolkata') = $1
        GROUP BY sent_type, api_sent_status
        ORDER BY sent_type, cnt DESC
    ''', TARGET)

    # Total unique students
    total = await conn.fetchval('''
        SELECT COUNT(DISTINCT student_id)
        FROM student_college_api_sent_status
        WHERE DATE(created_at AT TIME ZONE 'Asia/Kolkata') = $1
    ''', TARGET)

    # --- Print raw pivot ---
    print(f"=== API DISPOSITION PIVOT — April 4, 2026 ===")
    print(f"Total unique students: {total}")
    print()
    print(f"{'sent_type':<12} {'api_sent_status':<30} {'count':>6}")
    print("-" * 52)
    for r in rows:
        print(f"{r['sent_type']:<12} {r['api_sent_status']:<30} {r['cnt']:>6}")

    # --- Rolled-up by disposition ---
    disposition = {"Success": 0, "Fail": 0, "DNP": 0}
    for r in rows:
        status = (r['api_sent_status'] or '').strip()
        if status == 'Proceed':
            disposition["Success"] += r['cnt']
        elif 'fail' in status.lower() or 'technical' in status.lower():
            disposition["Fail"] += r['cnt']
        else:
            disposition["DNP"] += r['cnt']

    print()
    print("=== SUMMARY BY DISPOSITION ===")
    print(f"{'Success (Proceed)':<25} {disposition['Success']:>6}")
    print(f"{'Fail (Tech/Failed)':<25} {disposition['Fail']:>6}")
    print(f"{'DNP (Do Not Proceed)':<25} {disposition['DNP']:>6}")
    print(f"{'TOTAL':<25} {total:>6}")

    await conn.close()

asyncio.run(main())
