import os
import base64
import requests
import datetime
import json
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
WHATSAPP_GROUP = "120363426619711887@g.us"
DB_NAME = "regular_lms"

# Database connection parameters
DB_HOST = os.getenv("REGULAR_LMS_DB_HOST")
DB_PORT = os.getenv("REGULAR_LMS_DB_PORT", "54321")
DB_USER = os.getenv("REGULAR_LMS_DB_USER")
DB_PASSWORD = os.getenv("REGULAR_LMS_DB_PASSWORD")
DB_NAME_FULL = os.getenv("REGULAR_LMS_DB_NAME")

def get_report_data():
    # Branded Source filter: Facebook, Google_Lead_Form, Meta, FaceBook_University_Admit, Landing Page
    query = """
    SELECT 
        r.college_name, 
        r.sent_type, 
        r.api_sent_status, 
        COUNT(DISTINCT r.student_id) as count 
    FROM student_college_api_sent_status r
    JOIN students s ON s.student_id = r.student_id
    WHERE r.created_at >= CURRENT_DATE - interval '1 day' - interval '5 hours 30 minutes' 
      AND r.created_at < CURRENT_DATE - interval '5 hours 30 minutes'
      AND s.source IN ('FaceBook', 'Facebook', 'Google_Lead_Form', 'Meta_M', 'FaceBook_University_Admit', 'Landing Page')
    GROUP BY 1, 2, 3
    """
    
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME_FULL,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()
        cursor.execute(query)
        
        # Fetch columns and rows
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        
        # Convert to list of dicts
        result = [dict(zip(columns, row)) for row in rows]
        
        cursor.close()
        conn.close()
        
        return result
    except Exception as e:
        print(f"Database error: {e}")
        return []

def format_html(rows):
    data = {}
    colleges = set()
    for row in rows:
        c_name = row['college_name'] or "Unknown"
        colleges.add(c_name)
        s_type = row['sent_type']
        status = row['api_sent_status']
        count = row['count']
        if c_name not in data:
            data[c_name] = {'auto': {'proceed': 0, 'failed': 0, 'dnp': 0}, 'manual': {'proceed': 0, 'failed': 0, 'dnp': 0}}
        target = 'auto' if s_type == 'auto' else 'manual'
        
        # Robust status mapping
        if status == 'Proceed': 
            data[c_name][target]['proceed'] += count
        elif 'Technical Issues' in status or 'Failed' in status: 
            data[c_name][target]['failed'] += count
        elif status == 'Do not Proceed' or 'DNP' in status: 
            data[c_name][target]['dnp'] += count

    sorted_colleges = sorted(list(colleges))
    tbody_html = ""
    grand_totals = {'a_p': 0, 'a_f': 0, 'a_d': 0, 'm_p': 0, 'm_f': 0, 'm_d': 0}
    
    for c in sorted_colleges:
        d = data[c]
        a_p, a_f, a_d = d['auto']['proceed'], d['auto']['failed'], d['auto']['dnp']
        m_p, m_f, m_d = d['manual']['proceed'], d['manual']['failed'], d['manual']['dnp']
        grand_totals['a_p'] += a_p; grand_totals['a_f'] += a_f; grand_totals['a_d'] += a_d
        grand_totals['m_p'] += m_p; grand_totals['m_f'] += m_f; grand_totals['m_d'] += m_d
        
        def f(v): return f"<td>{v if v > 0 else '—'}</td>"
        tbody_html += f"""
        <tr>
            <td class="col-name">{c}</td>
            {f(a_p)}{f(a_f)}{f(a_d)}
            {f(m_p)}{f(m_f)}{f(m_d)}
            <td>{a_p+m_p}</td><td>{a_f+m_f}</td><td>{a_d+m_d}</td>
        </tr>"""

    yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%d %b %Y')
    
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; padding: 20px 10px; color: #f8fafc; }}
  .wrapper {{ width: 100%; max-width: 900px; margin: 0 auto; }}
  .header {{ display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 20px; border-bottom: 2px solid #334155; padding-bottom: 10px; }}
  h1 {{ font-size: 18px; font-weight: 800; color: #38bdf8; text-transform: uppercase; letter-spacing: 1px; }}
  .date-tag {{ background: #1e293b; padding: 4px 12px; border-radius: 4px; font-size: 12px; font-weight: 600; color: #94a3b8; border: 1px solid #334155; }}
  .badge {{ background: #0369a1; color: #e0f2fe; padding: 2px 8px; border-radius: 99px; font-size: 10px; text-transform: uppercase; margin-bottom: 4px; display: inline-block; }}
  
  table {{ width: 100%; border-collapse: separate; border-spacing: 0; background: #1e293b; border-radius: 12px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.3); table-layout: fixed; border: 1px solid #334155; }}
  th {{ background: #0f172a; color: #94a3b8; font-size: 10px; padding: 12px 2px; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid #334155; }}
  .group-head {{ color: #38bdf8; font-weight: 700; border-right: 1px solid #334155; }}
  .sub-head th {{ background: #1e293b; font-size: 9px; color: #64748b; border-right: 1px solid #334155; }}
  
  td {{ padding: 10px 2px; font-size: 11px; color: #cbd5e1; text-align: center; border-bottom: 1px solid #334155; border-right: 1px solid #334155; }}
  .col-name {{ text-align: left; font-weight: 600; padding-left: 12px; width: 30%; color: #f8fafc; background: #1e293b; position: sticky; left: 0; }}
  
  tr:nth-child(even) td {{ background: #1e293b; }}
  tr:nth-child(odd) td {{ background: #1e293b; background-opacity: 0.5; }}
  
  .grand-total td {{ background: #0f172a !important; color: #38bdf8; font-weight: 700; border-top: 2px solid #334155; }}
  .total-row td {{ background: #0369a1 !important; color: #fff; font-weight: 800; font-size: 12px; }}
  
  .stat-card {{ display: inline-block; background: #1e293b; padding: 10px; border-radius: 8px; border: 1px solid #334155; margin-right: 10px; min-width: 120px; }}
  .stat-val {{ display: block; font-size: 18px; font-weight: 800; color: #38bdf8; }}
  .stat-label {{ font-size: 9px; color: #64748b; text-transform: uppercase; }}
</style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <div>
      <span class="badge">Branded Campaigns</span>
      <h1>Regular API Recon Report</h1>
    </div>
    <div class="date-tag">{yesterday}</div>
  </div>

  <table>
    <thead>
      <tr>
        <th rowspan="2" style="width:30%;">College Name</th>
        <th colspan="3" class="group-head">Auto Recon</th>
        <th colspan="3" class="group-head">Manual Recon</th>
        <th colspan="3" class="group-head" style="border-right:none;">Total</th>
      </tr>
      <tr class="sub-head">
        <th>Proc</th><th>Fail</th><th>DNP</th>
        <th>Proc</th><th>Fail</th><th>DNP</th>
        <th style="color:#38bdf8">Proc</th><th style="color:#f43f5e">Fail</th><th style="color:#94a3b8">DNP</th>
      </tr>
    </thead>
    <tbody>
      {tbody_html}
      <tr class="grand-total">
        <td class="col-name">Grand Total</td>
        <td>{grand_totals['a_p']}</td><td>{grand_totals['a_f']}</td><td>{grand_totals['a_d']}</td>
        <td>{grand_totals['m_p']}</td><td>{grand_totals['m_f']}</td><td>{grand_totals['m_d']}</td>
        <td>{grand_totals['a_p']+grand_totals['m_p']}</td><td>{grand_totals['a_f']+grand_totals['m_f']}</td><td>{grand_totals['a_d']+grand_totals['m_d']}</td>
      </tr>
      <tr class="total-row">
        <td class="col-name">Summary Total</td>
        <td colspan="3">{grand_totals['a_p']+grand_totals['a_f']+grand_totals['a_d']}</td>
        <td colspan="3">{grand_totals['m_p']+grand_totals['m_f']+grand_totals['m_d']}</td>
        <td colspan="3">{grand_totals['a_p']+grand_totals['a_f']+grand_totals['a_d']+grand_totals['m_p']+grand_totals['m_f']+grand_totals['m_d']}</td>
      </tr>
    </tbody>
  </table>
  
  <div style="margin-top: 20px;">
    <div class="stat-card">
      <span class="stat-label">Auto Success Rate</span>
      <span class="stat-val">{round(grand_totals['a_p']/(grand_totals['a_p']+grand_totals['a_f']+grand_totals['a_d'])*100, 1) if (grand_totals['a_p']+grand_totals['a_f']+grand_totals['a_d']) > 0 else 0}%</span>
    </div>
    <div class="stat-card">
      <span class="stat-label">Total Leads Processed</span>
      <span class="stat-val">{grand_totals['a_p']+grand_totals['a_f']+grand_totals['a_d']+grand_totals['m_p']+grand_totals['m_f']+grand_totals['m_d']}</span>
    </div>
  </div>
</div>
</body>
</html>"""

def main():
    rows = get_report_data()
    if not rows:
        print("No data found for the selected period.")
        return
        
    html_content = format_html(rows)
    yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%d_%b_%Y')
    b64_content = base64.b64encode(html_content.encode('utf-8')).decode('utf-8')
    media_payload = f"data:text/html;name=Branded_Recon_Report_{yesterday}.html;base64,{b64_content}"
    
    WHAPI_TOKEN = os.getenv("WHAPI_TOKEN")
    if not WHAPI_TOKEN:
        print("WHAPI_TOKEN not found.")
        return

    headers = {
        "accept": "application/json", 
        "authorization": f"Bearer {WHAPI_TOKEN}", 
        "content-type": "application/json"
    }
    
    payload = {
        "to": WHATSAPP_GROUP, 
        "media": media_payload, 
        "caption": f"🚀 *Branded Campaigns: Regular API Recon Report*\n📅 Date: {yesterday.replace('_', ' ')}\n✅ Data filtered for Branded sources only."
    }
    
    response = requests.post("https://gate.whapi.cloud/messages/document", headers=headers, json=payload, timeout=20)
    print(f"Status: {response.status_code}, Response: {response.text}")

if __name__ == "__main__":
    main()
