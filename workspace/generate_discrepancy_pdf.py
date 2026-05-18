import pandas as pd
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
import os
import base64
import requests
from datetime import datetime

# Load the discrepancy data
df = pd.read_csv('final_discrepancy_report.csv')
df['Date'] = pd.to_datetime(df['Date']).dt.date

def generate_pdf(filename):
    doc = SimpleDocTemplate(filename, pagesize=landscape(A4), 
                            rightMargin=1*cm, leftMargin=1*cm, 
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        'TitleStyle', parent=styles['Heading1'], fontSize=18, 
        alignment=1, spaceAfter=20, textColor=colors.HexColor("#1877F2")
    )
    subtitle_style = ParagraphStyle(
        'SubtitleStyle', parent=styles['Normal'], fontSize=12, 
        alignment=1, spaceAfter=15, textColor=colors.grey
    )
    header_style = ParagraphStyle('HeaderStyle', parent=styles['Normal'], fontSize=8, textColor=colors.whitesmoke, fontName='Helvetica-Bold')
    body_style = ParagraphStyle('BodyStyle', parent=styles['Normal'], fontSize=7)
    
    elements = []
    
    # Title Page
    elements.append(Paragraph("Meta Ads Data Reconciliation Report", title_style))
    elements.append(Paragraph(f"Analysis Period: 2026-04-28 to 2026-05-06", subtitle_style))
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", subtitle_style))
    elements.append(Spacer(1, 2*cm))
    
    # Summary Table
    summary = df.groupby(['Date', 'Status']).size().unstack(fill_value=0)
    summary_data = [["Date", "Matches", "Discrepancies", "Missing Rows"]]
    for d, row in summary.iterrows():
        summary_data.append([str(d), str(row.get('MATCH', 0)), str(row.get('DISCREPANCY', 0)), str(row.get('MISSING', 0))])
    
    summary_table = Table(summary_data, colWidths=[4*cm, 3*cm, 4*cm, 4*cm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1877F2")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
    ]))
    
    elements.append(Paragraph("<b>Daily Sync Status Summary</b>", styles['Heading2']))
    elements.append(Spacer(1, 10))
    elements.append(summary_table)
    elements.append(PageBreak())
    
    # Detailed Discrepancy Tables (Split by Date)
    dates = sorted(df['Date'].unique(), reverse=True)
    
    for d in dates:
        day_df = df[df['Date'] == d].copy()
        # Filter for rows that actually have a problem
        issues = day_df[day_df['Status'] != 'MATCH'].copy()
        
        if issues.empty:
            continue
            
        elements.append(Paragraph(f"<b>Detailed Discrepancies - {d}</b>", styles['Heading2']))
        elements.append(Spacer(1, 10))
        
        # Prepare Data Table
        # Columns: Account, Ad Name, Meta Spend, Sheet Spend, Meta Panel, Sheet Panel, Status
        table_data = [[
            Paragraph("<b>Account</b>", header_style),
            Paragraph("<b>Ad Name</b>", header_style),
            Paragraph("<b>Meta Spend</b>", header_style),
            Paragraph("<b>Sheet Spend</b>", header_style),
            Paragraph("<b>Meta Panel</b>", header_style),
            Paragraph("<b>Sheet Panel</b>", header_style),
            Paragraph("<b>Status</b>", header_style)
        ]]
        
        for _, r in issues.iterrows():
            table_data.append([
                Paragraph(str(r['Account']), body_style),
                Paragraph(str(r['Ad Name']), body_style),
                f"₹{r['Meta Spend']:,.2f}",
                f"₹{r['Sheet Spend']:,.2f}",
                str(int(r['Meta Panel'])),
                str(int(r['Sheet Panel'])),
                Paragraph(f"<font color='red'><b>{r['Status']}</b></font>" if r['Status']=='MISSING' else r['Status'], body_style)
            ])
            
        t = Table(table_data, colWidths=[3.5*cm, 8*cm, 2.5*cm, 2.5*cm, 2*cm, 2*cm, 2.5*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1877F2")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 1*cm))
        
    doc.build(elements)
    print(f"PDF generated: {filename}")

def send_to_whatsapp(file_path):
    # Retrieve WHAPI token and Group ID from env or fallback to user provided values
    # For now, using the group ID from memory
    group_id = "120363426619711887@g.us"
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    # I will attempt to read the .env file if it exists
    whapi_token = os.getenv("WHAPI_TOKEN") 
    
    if not whapi_token:
        # Check report_config.json which often contains tokens
        print("Warning: WHAPI_TOKEN not found in env.")
        
    with open(file_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode('utf-8')
    
    payload = {
        "to": group_id,
        "media": f"data:application/pdf;name={os.path.basename(file_path)};base64,{b64}",
        "caption": "📊 *Meta Ads vs CAC Sheet Discrepancy Report*\nPeriod: Apr 28 - May 6, 2026\n\n*Critical Note:* May 6 data is completely missing from the sheets."
    }
    
    # Note: Using the WHAPI bridge tool is preferred if available, but here I'll try the manual request first
    # headers = {"Authorization": f"Bearer {whapi_token}"}
    # r = requests.post("https://gate.whapi.cloud/messages/document", json=payload, headers=headers)
    # return r.json()
    print("PDF ready for delivery.")

generate_pdf("Meta_Ads_Discrepancy_Report.pdf")
