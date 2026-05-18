import asyncio
import os
import json
import math
import pandas as pd
import asyncpg
import base64
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Use absolute paths for reliability in cron/WSL
WORKSPACE_DIR = "/home/mohit/workspace"
ENV_PATH = os.path.join(WORKSPACE_DIR, ".env")
CONFIG_FILE = os.path.join(WORKSPACE_DIR, "regular_report_config.json")
OUTPUT_XLSX = os.path.join(WORKSPACE_DIR, "Daily_Regular_LMS_Reports.xlsx")
OUTPUT_HTML = os.path.join(WORKSPACE_DIR, "Regular_LMS_Dashboard.html")

load_dotenv(ENV_PATH)

DB_CONFIGS = [
    {"name": "REGULAR", "host": os.getenv("REGULAR_LMS_DB_HOST"), "port": int(os.getenv("REGULAR_LMS_DB_PORT", "54321")), "database": os.getenv("REGULAR_LMS_DB_NAME"), "user": os.getenv("REGULAR_LMS_DB_USER"), "password": os.getenv("REGULAR_LMS_DB_PASSWORD")},
    {"name": "CGC", "host": os.getenv("REGULAR_CGC_LMS_DB_HOST"), "port": int(os.getenv("REGULAR_CGC_LMS_DB_PORT", "54321")), "database": os.getenv("REGULAR_CGC_LMS_DB_NAME"), "user": os.getenv("REGULAR_CGC_LMS_DB_USER"), "password": os.getenv("REGULAR_CGC_LMS_DB_PASSWORD")},
    {"name": "AMITY", "host": os.getenv("REGULAR_AMITY_LMS_DB_HOST"), "port": int(os.getenv("REGULAR_AMITY_LMS_DB_PORT", "54321")), "database": os.getenv("REGULAR_AMITY_LMS_DB_NAME"), "user": os.getenv("REGULAR_AMITY_LMS_DB_USER"), "password": os.getenv("REGULAR_AMITY_LMS_DB_PASSWORD")}
]

# SQL Queries with IST conversion
ADM_SQL = "SELECT DISTINCT ON (s.student_id, uc.course_id) s.student_id, uc.university_name AS college_name, (csj.created_at + interval '5 hours 30 minutes') AS created_at FROM students s JOIN course_status_journeys csj ON s.student_id = csj.student_id JOIN university_courses uc ON csj.course_id = uc.course_id WHERE csj.course_status = 'Admission' AND COALESCE(csj.fee_type, '') NOT ILIKE '%partial%' ORDER BY s.student_id, uc.course_id, csj.created_at ASC;"
FORM_SQL = "SELECT DISTINCT ON (s.student_id, csj.course_id) s.student_id, uc.university_name AS college_name, (csj.created_at + interval '5 hours 30 minutes') AS created_at FROM students s JOIN course_status_journeys csj ON s.student_id = csj.student_id JOIN university_courses uc ON csj.course_id = uc.course_id WHERE csj.course_status in ('Form Submitted – Portal Pending', 'Form Submitted – Completed', 'Walkin Completed', 'Exam/Interview Scheduled', 'Offer Letter/Results Pending', 'Offer Letter/Results Released', 'Ready For Admission') ORDER BY s.student_id, csj.course_id, csj.created_at ASC;"

async def fetch_db_data(db, sql):
    try:
        conn = await asyncpg.connect(host=db['host'], port=db['port'], database=db['database'], user=db['user'], password=db['password'], timeout=30)
        rows = await conn.fetch(sql)
        await conn.close()
        return pd.DataFrame([dict(r) for r in rows])
    except Exception as e:
        print(f"Error fetching from {db['name']}: {e}")
        return pd.DataFrame()

def norm_college(name):
    if not name: return "Unknown"
    name_str = str(name)
    if "Amity" in name_str: return "Amity University (All Campuses)"
    if "Chandigarh University" in name_str and "Lucknow" in name_str: return "Chandigarh University, Lucknow"
    if "Chandigarh University" in name_str: return "Chandigarh University, Mohali"
    if "CGC" in name_str or "Landran" in name_str: return "Chandigarh Group of Colleges, Landran (CGC)"
    if "Lovely" in name_str or "LPU" in name_str: return "Lovely Professional University"
    return name_str

def get_html_template(data_summary, report_date_str):
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Regular LMS Performance Dashboard</title>
        <style>
            :root {{
                --bg: #0f172a;
                --card-bg: #1e293b;
                --text: #f8fafc;
                --accent: #38bdf8;
                --success: #22c55e;
                --warning: #f59e0b;
                --danger: #ef4444;
            }}
            body {{ font-family: 'Inter', system-ui, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 20px; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .header h1 {{ margin: 0; color: var(--accent); font-size: 24px; }}
            .header p {{ opacity: 0.7; font-size: 14px; }}
            
            .kpi-container {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 30px; }}
            .kpi-card {{ background: var(--card-bg); padding: 20px; border-radius: 12px; border-left: 4px solid var(--accent); text-align: center; }}
            .kpi-title {{ font-size: 12px; text-transform: uppercase; opacity: 0.7; margin-bottom: 8px; }}
            .kpi-value {{ font-size: 28px; font-weight: 800; margin-bottom: 4px; }}
            .kpi-sub {{ font-size: 14px; opacity: 0.9; }}
            
            .table-container {{ background: var(--card-bg); border-radius: 12px; overflow: hidden; margin-bottom: 30px; border: 1px solid #334155; }}
            .table-header {{ padding: 15px 20px; background: #334155; font-weight: 700; border-bottom: 1px solid #475569; }}
            table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
            th {{ text-align: left; padding: 12px 15px; background: #1e293b; color: var(--accent); }}
            td {{ padding: 12px 15px; border-bottom: 1px solid #334155; }}
            tr:last-child {{ background: #0f172a; font-weight: bold; color: var(--accent); }}
            .pct-pill {{ padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 11px; }}
            .pct-high {{ background: #14532d; color: #4ade80; }}
            .pct-mid {{ background: #78350f; color: #fbbf24; }}
            .pct-low {{ background: #7f1d1d; color: #f87171; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Regular LMS Daily Performance</h1>
            <p>Data Snapshot for {report_date_str} (Generated via Hermes)</p>
        </div>
        
        <div class="kpi-container">
            <div class="kpi-card" style="border-color: var(--success)">
                <div class="kpi-title">MTD Admissions</div>
                <div class="kpi-value">{data_summary['adm_mtd_pct']}</div>
                <div class="kpi-sub">{data_summary['adm_mtd_ach']} / {data_summary['adm_mtd_tgt']}</div>
            </div>
            <div class="kpi-card" style="border-color: var(--accent)">
                <div class="kpi-title">FTD Admissions</div>
                <div class="kpi-value">{data_summary['adm_ftd_pct']}</div>
                <div class="kpi-sub">{data_summary['adm_ftd_ach']} / {data_summary['adm_ftd_tgt']}</div>
            </div>
            <div class="kpi-card" style="border-color: var(--warning)">
                <div class="kpi-title">MTD Forms</div>
                <div class="kpi-value">{data_summary['form_mtd_pct']}</div>
                <div class="kpi-sub">{data_summary['form_mtd_ach']} / {data_summary['form_mtd_tgt']}</div>
            </div>
            <div class="kpi-card" style="border-color: var(--danger)">
                <div class="kpi-title">FTD Forms</div>
                <div class="kpi-value">{data_summary['form_ftd_pct']}</div>
                <div class="kpi-sub">{data_summary['form_ftd_ach']} / {data_summary['form_ftd_tgt']}</div>
            </div>
        </div>

        <div class="table-container">
            <div class="table-header">Admissions Tracking</div>
            <table>
                <thead>
                    <tr>
                        <th>College</th>
                        <th>YTD Ach</th>
                        <th>MTD Target</th>
                        <th>MTD Ach</th>
                        <th>MTD %</th>
                        <th>FTD Target</th>
                        <th>FTD Ach</th>
                        <th>FTD %</th>
                    </tr>
                </thead>
                <tbody>
                    {data_summary['adm_rows_html']}
                </tbody>
            </table>
        </div>

        <div class="table-container">
            <div class="table-header">Forms Tracking</div>
            <table>
                <thead>
                    <tr>
                        <th>College</th>
                        <th>YTD Ach</th>
                        <th>MTD Target</th>
                        <th>MTD Ach</th>
                        <th>MTD %</th>
                        <th>FTD Target</th>
                        <th>FTD Ach</th>
                        <th>FTD %</th>
                    </tr>
                </thead>
                <tbody>
                    {data_summary['form_rows_html']}
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
    return html

def get_pct_class(val):
    try:
        v = float(val.strip('%'))
        if v >= 80: return "pct-high"
        if v >= 40: return "pct-mid"
        return "pct-low"
    except: return "pct-low"

async def run_report():
    if not os.path.exists(CONFIG_FILE):
        print("Config file not found")
        return

    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)

    now_ist = datetime.utcnow() + timedelta(hours=5, minutes=30)
    report_date = now_ist - timedelta(days=1) if now_ist.hour < 6 else now_ist
    
    ftd_str = report_date.strftime('%Y-%m-%d')
    mtd_start = report_date.replace(day=1).strftime('%Y-%m-%d')
    
    # Fetch Data
    adm_dfs = await asyncio.gather(*[fetch_db_data(db, ADM_SQL) for db in DB_CONFIGS])
    form_dfs = await asyncio.gather(*[fetch_db_data(db, FORM_SQL) for db in DB_CONFIGS])
    
    df_adm = pd.concat(adm_dfs).assign(college_name=lambda x: x['college_name'].apply(norm_college))
    df_form = pd.concat(form_dfs).assign(college_name=lambda x: x['college_name'].apply(norm_college))
    
    # Process Results
    targets = config.get("college_targets", {})
    summary = {
        'adm_mtd_ach': 0, 'adm_mtd_tgt': 0, 'adm_ftd_ach': 0, 'adm_ftd_tgt': 0,
        'form_mtd_ach': 0, 'form_mtd_tgt': 0, 'form_ftd_ach': 0, 'form_ftd_tgt': 0,
        'adm_rows_html': "", 'form_rows_html': ""
    }
    
    # Excel Sheets
    adm_data_xlsx = []
    form_data_xlsx = []
    
    for college, t in targets.items():
        # Admissions
        adm_ytd = len(df_adm[df_adm['college_name'] == college])
        adm_mtd = len(df_adm[(df_adm['college_name'] == college) & (df_adm['created_at'].dt.strftime('%Y-%m-%d').between(mtd_start, ftd_str))])
        adm_ftd = len(df_adm[(df_adm['college_name'] == college) & (df_adm['created_at'].dt.strftime('%Y-%m-%d') == ftd_str)])
        
        adm_mtd_t = t.get('admission_apr', 0)
        adm_week_t = t.get('admission_week', 0)
        adm_ftd_t = math.ceil(adm_week_t / 7)
        
        summary['adm_mtd_ach'] += adm_mtd
        summary['adm_mtd_tgt'] += adm_mtd_t
        summary['adm_ftd_ach'] += adm_ftd
        summary['adm_ftd_tgt'] += adm_ftd_t
        
        adm_mtd_p = f"{(adm_mtd/adm_mtd_t*100):.1f}%" if adm_mtd_t else "0.0%"
        adm_ftd_p = f"{(adm_ftd/adm_ftd_t*100):.1f}%" if adm_ftd_t else "0.0%"
        
        summary['adm_rows_html'] += f"""
        <tr>
            <td>{college}</td>
            <td>{adm_ytd}</td>
            <td>{adm_mtd_t}</td>
            <td>{adm_mtd}</td>
            <td><span class="pct-pill {get_pct_class(adm_mtd_p)}">{adm_mtd_p}</span></td>
            <td>{adm_ftd_t}</td>
            <td>{adm_ftd}</td>
            <td><span class="pct-pill {get_pct_class(adm_ftd_p)}">{adm_ftd_p}</span></td>
        </tr>
        """
        adm_data_xlsx.append([college, adm_ytd, adm_mtd_t, adm_mtd, adm_mtd_p, adm_week_t, "N/A", "N/A", adm_ftd_t, adm_ftd, adm_ftd_p])

        # Forms
        form_ytd = len(df_form[df_form['college_name'] == college])
        form_mtd = len(df_form[(df_form['college_name'] == college) & (df_form['created_at'].dt.strftime('%Y-%m-%d').between(mtd_start, ftd_str))])
        form_ftd = len(df_form[(df_form['college_name'] == college) & (df_form['created_at'].dt.strftime('%Y-%m-%d') == ftd_str)])
        
        form_mtd_t = t.get('forms_apr', 0)
        form_week_t = t.get('forms_week', 0)
        form_ftd_t = math.ceil(form_week_t / 7)
        
        summary['form_mtd_ach'] += form_mtd
        summary['form_mtd_tgt'] += form_mtd_t
        summary['form_ftd_ach'] += form_ftd
        summary['form_ftd_tgt'] += form_ftd_t
        
        form_mtd_p = f"{(form_mtd/form_mtd_t*100):.1f}%" if form_mtd_t else "0.0%"
        form_ftd_p = f"{(form_ftd/form_ftd_t*100):.1f}%" if form_ftd_t else "0.0%"
        
        summary['form_rows_html'] += f"""
        <tr>
            <td>{college}</td>
            <td>{form_ytd}</td>
            <td>{form_mtd_t}</td>
            <td>{form_mtd}</td>
            <td><span class="pct-pill {get_pct_class(form_mtd_p)}">{form_mtd_p}</span></td>
            <td>{form_ftd_t}</td>
            <td>{form_ftd}</td>
            <td><span class="pct-pill {get_pct_class(form_ftd_p)}">{form_ftd_p}</span></td>
        </tr>
        """
        form_data_xlsx.append([college, form_ytd, form_mtd_t, form_mtd, form_mtd_p, form_week_t, "N/A", "N/A", form_ftd_t, form_ftd, form_ftd_p])

    # Final Summary Logic
    summary['adm_mtd_pct'] = f"{(summary['adm_mtd_ach']/summary['adm_mtd_tgt']*100):.1f}%" if summary['adm_mtd_tgt'] else "0.0%"
    summary['adm_ftd_pct'] = f"{(summary['adm_ftd_ach']/summary['adm_ftd_tgt']*100):.1f}%" if summary['adm_ftd_tgt'] else "0.0%"
    summary['form_mtd_pct'] = f"{(summary['form_mtd_ach']/summary['form_mtd_tgt']*100):.1f}%" if summary['form_mtd_tgt'] else "0.0%"
    summary['form_ftd_pct'] = f"{(summary['form_ftd_ach']/summary['form_ftd_tgt']*100):.1f}%" if summary['form_ftd_tgt'] else "0.0%"
    
    # Add Total Rows to HTML
    summary['adm_rows_html'] += f"<tr><td>Total</td><td>-</td><td>{summary['adm_mtd_tgt']}</td><td>{summary['adm_mtd_ach']}</td><td>{summary['adm_mtd_pct']}</td><td>{summary['adm_ftd_tgt']}</td><td>{summary['adm_ftd_ach']}</td><td>{summary['adm_ftd_pct']}</td></tr>"
    summary['form_rows_html'] += f"<tr><td>Total</td><td>-</td><td>{summary['form_mtd_tgt']}</td><td>{summary['form_mtd_ach']}</td><td>{summary['form_mtd_pct']}</td><td>{summary['form_ftd_tgt']}</td><td>{summary['form_ftd_ach']}</td><td>{summary['form_ftd_pct']}</td></tr>"
    
    # Save Files
    html_content = get_html_template(summary, ftd_str)
    with open(OUTPUT_HTML, 'w') as f: f.write(html_content)
    
    with pd.ExcelWriter(OUTPUT_XLSX) as writer:
        cols = ["College", "YTD Ach", "MTD Target", "MTD Ach", "MTD Ach %", "Weekly Target", "Weekly Ach", "Weekly Ach %", "FTD Target", "FTD Ach", "FTD Ach %"]
        pd.DataFrame(adm_data_xlsx, columns=cols).to_excel(writer, sheet_name='Admissions Data', index=False)
        pd.DataFrame(form_data_xlsx, columns=cols).to_excel(writer, sheet_name='Forms Data', index=False)

    # Send to WhatsApp
    WHAPI_TOKEN = os.getenv("WHAPI_TOKEN")
    WHATSAPP_GROUP = os.getenv("WHATSAPP_GROUP")
    
    def send_whapi(file_path, mime_type, caption):
        with open(file_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode('utf-8')
        payload = {
            "to": WHATSAPP_GROUP,
            "media": f"data:{mime_type};name={os.path.basename(file_path)};base64,{b64}",
            "caption": caption
        }
        headers = {"accept": "application/json", "authorization": f"Bearer {WHAPI_TOKEN}", "content-type": "application/json"}
        r = requests.post("https://gate.whapi.cloud/messages/document", headers=headers, json=payload)
        return r.status_code == 200

    print(f"Sending HTML Dashboard...")
    send_whapi(OUTPUT_HTML, "text/html", f"🚀 *Regular LMS Dashboard - {ftd_str}*\n\nAdmissions MTD: {summary['adm_mtd_pct']}\nForms MTD: {summary['form_mtd_pct']}")
    print(f"Sending Excel Report...")
    send_whapi(OUTPUT_XLSX, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", f"📊 *Regular LMS Detailed Excel - {ftd_str}*")

if __name__ == "__main__":
    asyncio.run(run_report())
