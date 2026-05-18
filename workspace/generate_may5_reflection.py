import pandas as pd
from fpdf import FPDF

df = pd.read_csv('may5_reflection_final.csv')
total_spends = df['Spends'].sum()
total_panel = df['Pannel_Lead'].sum()
total_lms = df['LMS Leads'].sum()

pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", 'B', 16)
pdf.cell(200, 10, txt="May 5th Reflection Report", ln=True, align='C')
pdf.set_font("Arial", size=12)
pdf.ln(10)
pdf.cell(200, 10, txt=f"Total Spends: INR {total_spends:,.2f}", ln=True)
pdf.cell(200, 10, txt=f"Total Panel Leads: {total_panel}", ln=True)
pdf.cell(200, 10, txt=f"Total LMS Leads: {total_lms}", ln=True)
pdf.ln(10)

# Table Header
pdf.set_font("Arial", 'B', 10)
cols = ['Account', 'Campaign', 'Spends', 'Panel', 'LMS']
for col in cols:
    pdf.cell(38, 10, col, 1)
pdf.ln()

# Table Data
pdf.set_font("Arial", size=9)
for _, r in df.iterrows():
    pdf.cell(38, 10, str(r['Account'])[:15], 1)
    pdf.cell(38, 10, str(r['Campaign'])[:15], 1)
    pdf.cell(38, 10, f"{r['Spends']:.2f}", 1)
    pdf.cell(38, 10, str(r['Pannel_Lead']), 1)
    pdf.cell(38, 10, str(r['LMS Leads']), 1)
    pdf.ln()

pdf.output("May5_Reflection_Report.pdf")
print("Generated May 5 PDF.")
