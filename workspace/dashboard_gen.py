import pandas as pd
import os

excel_path = "/home/mohit/workspace/Daily_Online_LMS_Reports_V2.xlsx"
html_path = "/home/mohit/workspace/LMS_Report_Dashboard.html"

def generate_dashboard():
    with pd.ExcelFile(excel_path) as xls:
        df_coll = pd.read_excel(xls, "College_Performance")
        df_coun_adm = pd.read_excel(xls, "Counsellor_Admission")
        df_sup_adm = pd.read_excel(xls, "Supervisor_Admission")
        df_sup_fee = pd.read_excel(xls, "Supervisor_Fee_Collected")

    # Extract High-level KPIs from Supervisor Fee Collected (Grand Total)
    grand_total_row = df_sup_fee[df_sup_fee['Supervisor'] == 'Grand Total'].iloc[0]
    total_fee_ftd = grand_total_row['FTD']
    mtd_fee = grand_total_row['Fee Collected']
    target = grand_total_row['Target']
    ach_pct = str(grand_total_row['Ach %']).strip('%')

    # HTML Template with CSS-only Tabs and Accordions
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #121212; color: #e0e0e0; margin: 0; padding: 10px; }}
        .header {{ text-align: center; padding: 20px 0; border-bottom: 1px solid #333; }}
        .kpi-container {{ display: flex; flex-wrap: wrap; gap: 10px; margin: 20px 0; justify-content: space-around; }}
        .kpi-card {{ background: #1e1e1e; border: 1px solid #333; border-radius: 8px; padding: 15px; width: 42%; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }}
        .kpi-label {{ font-size: 11px; color: #888; text-transform: uppercase; margin-bottom: 5px; }}
        .kpi-value {{ font-size: 24px; font-weight: bold; color: #4CAF50; }}
        .kpi-subtext {{ font-size: 12px; color: #bbb; margin-top: 5px; }}
        
        .tabs {{ display: flex; flex-wrap: wrap; margin-top: 20px; }}
        .tabs label {{ order: 1; display: block; padding: 10px 15px; cursor: pointer; background: #333; border-radius: 5px 5px 0 0; margin-right: 2px; font-weight: bold; font-size: 13px; }}
        .tabs .tab {{ order: 99; flex-grow: 1; width: 100%; display: none; padding: 15px; background: #1e1e1e; border: 1px solid #333; border-radius: 0 5px 5px 5px; box-sizing: border-box; }}
        .tabs input[type="radio"] {{ display: none; }}
        .tabs input[type="radio"]:checked + label {{ background: #4CAF50; color: white; }}
        .tabs input[type="radio"]:checked + label + .tab {{ display: block; }}

        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 11px; }}
        th {{ background: #333; color: #fff; text-align: left; padding: 6px; }}
        td {{ border-bottom: 1px solid #333; padding: 6px; }}
        .ach-pct {{ font-weight: bold; color: #4CAF50; }}
        
        details {{ margin-bottom: 10px; background: #252525; border-radius: 5px; overflow: hidden; border: 1px solid #333; }}
        summary {{ padding: 10px; cursor: pointer; font-weight: bold; outline: none; background: #333; }}
        details[open] summary {{ border-bottom: 1px solid #444; background: #444; }}
        .detail-content {{ padding: 10px; overflow-x: auto; }}
    </style>
    </head>
    <body>
        <div class="header">
            <h2 style="margin:0;">LMS Performance</h2>
            <div style="font-size: 13px; color: #888;">FTD: {pd.to_datetime('today').strftime('%d %b %Y')}</div>
        </div>

        <div class="kpi-container">
            <div class="kpi-card">
                <div class="kpi-label">Month Achievement</div>
                <div class="kpi-value">{ach_pct}%</div>
                <div class="kpi-subtext">{mtd_fee/100000:,.1f}L / {target/100000:,.0f}L</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Today Fee</div>
                <div class="kpi-value">₹{total_fee_ftd:,.0f}</div>
                <div class="kpi-subtext">FTD Collected</div>
            </div>
        </div>

        <div class="tabs">
            <input type="radio" name="tabs" id="tab1" checked="checked">
            <label for="tab1">Teams</label>
            <div class="tab">
                <div style="overflow-x: auto;">
                    {df_sup_fee.to_html(index=False, classes='table')}
                </div>
            </div>

            <input type="radio" name="tabs" id="tab2">
            <label for="tab2">Colleges</label>
            <div class="tab">
                <div style="overflow-x: auto;">
                    {df_coll[['Colleges', 'MTD Admissions', 'MTD F2A %', 'FTD Admissions']].head(15).to_html(index=False, classes='table')}
                </div>
            </div>

            <input type="radio" name="tabs" id="tab3">
            <label for="tab3">Top 10</label>
            <div class="tab">
                <div style="overflow-x: auto;">
                    {df_coun_adm.sort_values('Achieve', ascending=False).head(10).to_html(index=False, classes='table')}
                </div>
            </div>
        </div>

        <div style="margin-top: 20px;">
            <details>
                <summary>Supervisor Admissions</summary>
                <div class="detail-content">
                    {df_sup_adm.to_html(index=False, classes='table')}
                </div>
            </details>
        </div>

        <div style="text-align: center; color: #666; font-size: 10px; margin-top: 30px; padding-bottom: 20px;">
            Generated by Hermes LMS Automation
        </div>
    </body>
    </html>
    """
    with open(html_path, "w") as f:
        f.write(html_content)
    print(f"Dashboard generated: {html_path}")

if __name__ == "__main__":
    generate_dashboard()
