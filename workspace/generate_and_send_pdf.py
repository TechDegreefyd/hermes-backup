import asyncio
import os
import pandas as pd
import asyncpg
import base64
import requests
from dotenv import load_dotenv

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

load_dotenv('/home/hermeswebui/workspace/.env')

DB_HOST = os.getenv("ONLINE_LMS_DB_HOST")
DB_PORT = int(os.getenv("ONLINE_LMS_DB_PORT", "54321"))
DB_NAME = os.getenv("ONLINE_LMS_DB_NAME")
DB_USER = os.getenv("ONLINE_LMS_DB_USER")
DB_PASSWORD = os.getenv("ONLINE_LMS_DB_PASSWORD")
WHAPI_TOKEN = os.getenv("WHAPI_TOKEN")
WHATSAPP_GROUP = os.getenv("WHATSAPP_GROUP")

QUERY = """
SELECT DISTINCT ON (s.student_id, uc.course_id)
    s.student_id,
    csj.deposit_amount AS fee_deposit,
    c.counsellor_name
FROM students s
JOIN course_status_journeys csj ON s.student_id = csj.student_id
JOIN university_courses uc ON csj.course_id = uc.course_id
LEFT JOIN counsellors c ON s.assigned_counsellor_id = c.counsellor_id
WHERE csj.course_status = 'Admission'
  AND csj.fee_type NOT IN ('partial paid', 'Partially Paid', 'Partial Done','Partial Paid')
  AND s.student_id IN (SELECT student_id FROM students)
  AND (csj.created_at AT TIME ZONE 'Asia/Kolkata') >= '2026-04-21 00:00:00'
  AND (csj.created_at AT TIME ZONE 'Asia/Kolkata') <= '2026-04-30 23:59:59'
"""

# Hardcoded supervisors mappings to mimic the report layout
SUPERVISORS = {
    'Varun': ['Abhishek Kamat', 'Abhishek Swami', 'Amandeep', 'Amit Kumar', 'Anishika Prashar', 'Ankita Singh Chauhan', 'Arnav Upadhyay', 'Avneet'],
    'Sunil': ['Awantika Singh', 'Chandni Kumari', 'Divya Goyal', 'Himanshi', 'Himanshi Baliyan', 'Kumud Kumar', 'Laxminaryan', 'Mayank Jain'],
    'Vishal': ['Mousumi Khatun', 'Om  Sharma', 'Prashant', 'Prateek Chauhan', 'Preeti Lohiya', 'Purushottam Kumar', 'Raja Ram', 'Rupal Tiwari'],
    'Siddhartha': ['Siddarth Kumar', 'Suhani Raj Gupta', 'Sumit Yadav', 'Tanisha Kulshrestha', 'Tanya Singh', 'Tanya sharma', 'Vijay Kumar', 'Vikas', 'Vishwajeet']
}

def get_supervisor(counselor_name):
    for sup, counselors in SUPERVISORS.items():
        if counselor_name in counselors:
            return sup
    return 'Other'

async def main():
    conn = await asyncpg.connect(
        user=DB_USER, password=DB_PASSWORD, database=DB_NAME,
        host=DB_HOST, port=DB_PORT
    )
    records = await conn.fetch(QUERY)
    await conn.close()
    
    df = pd.DataFrame([dict(r) for r in records])
    if df.empty:
        print("No records found for the given date range.")
        df = pd.DataFrame(columns=['counsellor_name', 'is_ftd', 'achieve', 'ftd', 'supervisor', 'sup_order'])
    else:
        df['is_ftd'] = pd.to_numeric(df['fee_deposit'], errors='coerce').fillna(0) > 0
        df['counsellor_name'] = df['counsellor_name'].fillna('Unassigned')
        
        # Calculate stats
        counselor_stats = df.groupby('counsellor_name').agg(
            achieve=('student_id', 'count'),
            ftd=('is_ftd', 'sum')
        ).reset_index()
        
        # Add supervisor
        counselor_stats['supervisor'] = counselor_stats['counsellor_name'].apply(get_supervisor)
        
        # Sort by supervisor order and counselor name
        sup_order = {s: i for i, s in enumerate(['Varun', 'Sunil', 'Vishal', 'Siddhartha', 'Other'])}
        counselor_stats['sup_order'] = counselor_stats['supervisor'].map(sup_order)
        counselor_stats = counselor_stats.sort_values(['sup_order', 'counsellor_name'])
        df = counselor_stats
    
    pdf_path = "/home/hermeswebui/workspace/Admission_Target_Vs_Achievement_21_30_Apr.pdf"
    
    doc = SimpleDocTemplate(pdf_path, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2.5*cm, bottomMargin=2.5*cm)
    styles = getSampleStyleSheet()
    
    S_TITLE = ParagraphStyle('T', parent=styles['Title'], fontSize=16, textColor=HexColor('#16213e'), spaceAfter=10, fontName='Helvetica-Bold')
    
    story = []
    
    # Title
    story.append(Paragraph("Admission Target Vs Achievement (21-30 Apr)", S_TITLE))
    story.append(Spacer(1, 0.5*cm))
    
    # Table Data and Styles
    data = [["Supervisor", "Counselor", "Achieve", "FTD Achievement"]]
    
    t_styles = [
        ('BACKGROUND', (0,0), (-1,0), HexColor('#16213e')),
        ('TEXTCOLOR', (0,0), (-1,0), white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('ALIGN', (0,0), (1,0), 'LEFT'),
        ('ALIGN', (2,0), (3,0), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, black),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
    ]
    
    current_row = 1
    grand_achieve = 0
    grand_ftd = 0
    
    if not df.empty:
        for sup in ['Varun', 'Sunil', 'Vishal', 'Siddhartha', 'Other']:
            sup_data = df[df['supervisor'] == sup]
            if sup_data.empty:
                continue
                
            start_row = current_row
            sup_achieve = 0
            sup_ftd = 0
            
            for _, row in sup_data.iterrows():
                achieve = row['achieve']
                ftd = row['ftd']
                
                sup_achieve += achieve
                sup_ftd += ftd
                grand_achieve += achieve
                grand_ftd += ftd
                
                data.append([sup, row['counsellor_name'], str(achieve), str(ftd)])
                t_styles.append(('ALIGN', (2, current_row), (3, current_row), 'CENTER'))
                current_row += 1
                
            # Span supervisor cell
            if current_row > start_row:
                t_styles.append(('SPAN', (0, start_row), (0, current_row - 1)))
                
            # Total Row for Supervisor
            data.append([f"{sup} Total", "", str(sup_achieve), str(sup_ftd)])
            t_styles.append(('SPAN', (0, current_row), (1, current_row)))
            t_styles.append(('BACKGROUND', (0, current_row), (-1, current_row), HexColor('#dcdcdc')))
            t_styles.append(('FONTNAME', (0, current_row), (-1, current_row), 'Helvetica-Bold'))
            t_styles.append(('ALIGN', (0, current_row), (1, current_row), 'LEFT'))
            t_styles.append(('ALIGN', (2, current_row), (3, current_row), 'CENTER'))
            current_row += 1
            
    # Grand Total
    data.append(["Grand Total", "", str(grand_achieve), str(grand_ftd)])
    t_styles.append(('SPAN', (0, current_row), (1, current_row)))
    t_styles.append(('BACKGROUND', (0, current_row), (-1, current_row), HexColor('#c0c0c0')))
    t_styles.append(('FONTNAME', (0, current_row), (-1, current_row), 'Helvetica-Bold'))
    t_styles.append(('ALIGN', (0, current_row), (1, current_row), 'LEFT'))
    t_styles.append(('ALIGN', (2, current_row), (3, current_row), 'CENTER'))
    
    col_widths = [4*cm, 7*cm, 3*cm, 3*cm]
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle(t_styles))
    story.append(t)
    
    doc.build(story)
    print(f"PDF created at {pdf_path}")
    
    # Send via WHAPI
    print("Sending via WHAPI...")
    with open(pdf_path, "rb") as f:
        b64_content = base64.b64encode(f.read()).decode('utf-8')
        
    mime_type = "application/pdf"
    media_payload = f"data:{mime_type};name=Admission_Target_Vs_Achievement_21_30_Apr.pdf;base64,{b64_content}"
    
    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {WHAPI_TOKEN}",
        "content-type": "application/json"
    }
    
    payload = {
        "to": WHATSAPP_GROUP,
        "media": media_payload,
        "caption": "📊 *Admission Target Vs Achievement (21-30 Apr)*\n\nFiltered for April 21 to April 30 timeframe."
    }
    
    resp = requests.post("https://gate.whapi.cloud/messages/document", headers=headers, json=payload)
    print("Status:", resp.status_code)
    try:
        print("Response:", resp.json())
    except:
        print("Response:", resp.text)

if __name__ == "__main__":
    asyncio.run(main())