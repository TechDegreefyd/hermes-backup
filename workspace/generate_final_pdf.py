from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import pandas as pd

try:
    df = pd.read_csv('may4_reflection_final.csv')
    pdf_df = df[['Account', 'Campaign', 'Ad Name', 'Spends', 'Pannel_Lead', 'LMS Leads']].copy()
    pdf_df['Campaign'] = pdf_df['Campaign'].astype(str).str[:30]
    pdf_df['Ad Name'] = pdf_df['Ad Name'].astype(str).str[:30]

    doc = SimpleDocTemplate("May4_Final_Reflection_Report.pdf", pagesize=landscape(A4))
    elements = []
    styles = getSampleStyleSheet()

    title = Paragraph("Meta Ads & LMS Lead Reflection: May 4, 2026", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 20))

    total_spend = df['Spends'].sum()
    total_panel = df['Pannel_Lead'].sum()
    total_lms = df['LMS Leads'].sum()

    summary_data = [
        ["Metric", "Value"],
        ["Total Spend", f"INR {total_spend:,.2f}"],
        ["Total Panel Leads", str(int(total_panel))],
        ["Total LMS Verified Leads", str(int(total_lms))],
        ["Avg Cost Per Panel Lead", f"INR {total_spend/total_panel if total_panel > 0 else 0:,.2f}"]
    ]
    summary_table = Table(summary_data, colWidths=[200, 200])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 30))

    data = [pdf_df.columns.tolist()] + pdf_df.values.tolist()
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.dodgerblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.beige])
    ]))
    elements.append(table)
    doc.build(elements)
    print("PDF generated successfully.")
except Exception as e:
    print(f"Error: {e}")
