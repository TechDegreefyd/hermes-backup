import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('REGULAR_LMS_DB_HOST', 'storage.bhugoal.cloud'),
    port=int(os.getenv('REGULAR_LMS_DB_PORT', 54321)),
    dbname=os.getenv('REGULAR_LMS_DB_NAME', 'degreefyd_regular_lms'),
    user=os.getenv('REGULAR_LMS_DB_USER', 'postgres'),
    password=os.getenv('REGULAR_LMS_DB_PASSWORD')
)
cur = conn.cursor()

print("=== student_college_api_sent_status ===")
cur.execute("""SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'student_college_api_sent_status' ORDER BY ordinal_position""")
for r in cur.fetchall():
    print(f'{r[0]}: {r[1]}')

print("\n=== student_lead_activities ===")
cur.execute("""SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'student_lead_activities' ORDER BY ordinal_position""")
for r in cur.fetchall():
    print(f'{r[0]}: {r[1]}')

print("\n=== UTM columns in student_lead_activities ===")
cur.execute("""SELECT column_name FROM information_schema.columns WHERE table_name = 'student_lead_activities' AND column_name LIKE '%utm%'""")
for r in cur.fetchall():
    print(f'UTM: {r[0]}')

print("\n=== Tables with utm/campaign ===")
cur.execute("""SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND (table_name LIKE '%utm%' OR table_name LIKE '%campaign%' OR table_name LIKE '%lead%source%')""")
for r in cur.fetchall():
    print(f'Table: {r[0]}')

print("\n=== sent_type values ===")
cur.execute("SELECT DISTINCT sent_type FROM student_college_api_sent_status")
for r in cur.fetchall():
    print(f'sent_type: {r[0]}')

print("\n=== api_sent_status values ===")
cur.execute("SELECT DISTINCT api_sent_status FROM student_college_api_sent_status")
for r in cur.fetchall():
    print(f'api_sent_status: {r[0]}')

print("\n=== Sample data (5 rows) ===")
cur.execute("SELECT * FROM student_college_api_sent_status LIMIT 5")
cols = [desc[0] for desc in cur.description]
print(f'Columns: {cols}')
for r in cur.fetchall():
    print(r)

print("\n=== student_id sample ===")
cur.execute("SELECT student_id FROM student_college_api_sent_status LIMIT 5")
for r in cur.fetchall():
    print(f'type: {type(r[0]).__name__}, value: {repr(r[0])}')

print("\n=== student_lead_activities columns ===")
cur.execute("SELECT * FROM student_lead_activities LIMIT 5")
cols = [desc[0] for desc in cur.description]
print(f'Columns: {cols}')
for r in cur.fetchall():
    print(r)

conn.close()
