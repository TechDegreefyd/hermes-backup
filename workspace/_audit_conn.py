import asyncio, asyncpg, os
from dotenv import load_dotenv
load_dotenv('/workspace/.env')

async def main():
    conn = await asyncpg.connect(
        host=os.environ['ONLINE_LMS_DB_HOST'],
        port=int(os.environ['ONLINE_LMS_DB_PORT']),
        user=os.environ['ONLINE_LMS_DB_USER'],
        password=os.environ['ONLINE_LMS_DB_PASSWORD'],
        database=os.environ['ONLINE_LMS_DB_NAME']
    )
    
    q = """
    SELECT c.counsellor_name, 
           COALESCE(to_c.counsellor_name, 'No Supervisor') AS team_owner,
           COUNT(*) AS total_remarks,
           COUNT(*) FILTER (WHERE sr.calling_status = 'Connected') AS conn_by_remark,
           COUNT(*) FILTER (WHERE sr.isdisabled IS NULL) AS null_disabled,
           COUNT(*) FILTER (WHERE sr.isdisabled = true) AS true_disabled,
           COUNT(*) FILTER (WHERE sr.isdisabled = false) AS false_disabled
    FROM student_remarks sr
    JOIN counsellors c ON sr.counsellor_id = c.counsellor_id
    LEFT JOIN counsellors to_c ON c.assigned_to = to_c.counsellor_id AND to_c.role = 'to'
    WHERE (sr.created_at AT TIME ZONE 'Asia/Kolkata')::date = '2026-05-13'
    GROUP BY c.counsellor_name, to_c.counsellor_name
    ORDER BY team_owner, c.counsellor_name
    """
    rows = await conn.fetch(q)
    print(f"COUNSELLOR\t\tTEAM\t\tREMARKS\tCONN\tNULL_DIS\tT_DIS\tF_DIS")
    print("-"*80)
    for r in rows:
        d = dict(r)
        print(f"{d['counsellor_name']:22}\t{d['team_owner']:16}\t{d['total_remarks']:>4}\t{d['conn_by_remark']:>4}\t{d['null_disabled']:>4}\t\t{d['true_disabled']:>4}\t{d['false_disabled']:>4}")

    # Total connected without any isdisabled filter
    total = await conn.fetchrow("""
    SELECT COUNT(*) as all_remarks,
           COUNT(*) FILTER (WHERE calling_status = 'Connected') as all_connected,
           COUNT(*) FILTER (WHERE calling_status = 'Connected' AND (isdisabled IS NULL OR isdisabled = false)) as active_connected
    FROM student_remarks sr
    WHERE (sr.created_at AT TIME ZONE 'Asia/Kolkata')::date = '2026-05-13'
    """)
    print(f"\nTotal without isdisabled filter: {total['all_remarks']} remarks, {total['all_connected']} connected")
    print(f"Active (null/false) connected: {total['active_connected']}")

    await conn.close()

asyncio.run(main())
