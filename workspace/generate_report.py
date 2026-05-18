import json
import base64
import io
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# --- MATPLOTLIB STYLING (PLOTLY DARK THEME MIMIC) ---
plt.style.use('dark_background')
sns.set_theme(style="darkgrid", rc={
    "axes.facecolor": "#0F1018",
    "figure.facecolor": "#0F1018",
    "grid.color": "#22233a",
    "axes.edgecolor": "#333333",
    "text.color": "#dde0f0",
    "axes.labelcolor": "#dde0f0",
    "xtick.color": "#5a5d80",
    "ytick.color": "#5a5d80",
    "font.family": "monospace",
})

# --- FETCH DATA ---
TOKEN_PATH = "/home/hermeswebui/.hermes/google_token.json"
creds = Credentials.from_authorized_user_file(TOKEN_PATH)
service = build("sheets", "v4", credentials=creds)
spreadsheet_id = "1oOJMZqfq31_2DrdEUKsNeforXlikOodyKUJoAgTKsCw"

ranges = [
    "Dashboard!A1:N20",
    "DSA_graph1!A1:F100",
    "DSA_graph2!A1:C100",
    "Brand graph1!A1:F100",
    "Brand graph2!A1:C100",
    "graph1!A1:F100",
    "graph2!A1:C100"
]

results = service.spreadsheets().values().batchGet(
    spreadsheetId=spreadsheet_id,
    ranges=ranges
).execute()

data = {r["range"].split("!")[0]: r.get("values", []) for r in results.get("valueRanges", [])}

# --- PROCESS DATA ---
def make_df(rows):
    if not rows or len(rows) < 2: return pd.DataFrame()
    df = pd.DataFrame(rows[1:], columns=rows[0])
    return df

df_dsa_cpl = make_df(data.get("DSA_graph1", []))
df_dsa_lead = make_df(data.get("DSA_graph2", []))
df_brand_cpl = make_df(data.get("'Brand graph1'", []))
df_brand_lead = make_df(data.get("'Brand graph2'", []))
df_meta_cpl = make_df(data.get("graph1", []))
df_meta_lead = make_df(data.get("graph2", []))

def clean_numeric(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c].astype(str).str.replace(',', ''), errors='coerce')
    return df

for df in [df_dsa_cpl, df_brand_cpl, df_meta_cpl]:
    if not df.empty:
        cpl_p_col = [c for c in df.columns if 'CPL' in c.upper() and 'PANNEL' in c.upper()][0]
        cpl_l_col = [c for c in df.columns if 'CPL' in c.upper() and 'LMS' in c.upper()][0]
        df = clean_numeric(df, [cpl_p_col, cpl_l_col])

for df in [df_dsa_lead, df_brand_lead, df_meta_lead]:
    if not df.empty:
        lead_p_col = [c for c in df.columns if 'PANNEL' in c.upper()][0]
        lead_l_col = [c for c in df.columns if 'LMS' in c.upper()][0]
        df = clean_numeric(df, [lead_p_col, lead_l_col])

images_html = []

def fig_to_html(fig, title):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches='tight', dpi=150)
    buf.seek(0)
    b64_img = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return f'<div class="chart-container"><img src="data:image/png;base64,{b64_img}" alt="{title}" style="width:100%; height:auto; display:block; border-radius:6px;"/></div>'

def make_line_chart_img(df, x_col, y_cols, title, names):
    if df.empty: return ""
    fig, ax = plt.subplots(figsize=(10, 5))
    colors = ['#00E5FF', '#FF1744']
    
    for i, y in enumerate(y_cols):
        ax.plot(df[x_col], df[y], marker='o', markersize=6, linewidth=2.5, color=colors[i], label=names[i])
        
        # Add labels on points
        for x_val, y_val in zip(df[x_col], df[y]):
            if pd.notnull(y_val):
                ax.annotate(f'{y_val:g}', (x_val, y_val), textcoords="offset points", xytext=(0,10), ha='center', fontsize=9, color=colors[i])

    ax.set_title(title, color='#dde0f0', pad=20, fontweight='bold', fontsize=14)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.15), ncol=2, frameon=False)
    ax.tick_params(axis='x', rotation=45)
    
    return fig_to_html(fig, title)

def make_bar_chart_img(title, x_data, y_data_list, names):
    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ['#4f8ef7', '#22d98a', '#a78bfa']
    
    x = range(len(x_data))
    width = 0.35 if len(y_data_list) == 2 else 0.5
    
    for i, y_data in enumerate(y_data_list):
        offset = (i - len(y_data_list)/2 + 0.5) * width
        rects = ax.bar([pos + offset for pos in x], y_data, width, label=names[i], color=colors[i])
        ax.bar_label(rects, padding=3, color=colors[i], fmt='%g', fontsize=10)

    ax.set_title(title, color='#dde0f0', pad=20, fontweight='bold', fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels(x_data)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.15), ncol=len(names), frameon=False)
    
    return fig_to_html(fig, title)


# GENERATE ALL CHARTS
if not df_dsa_cpl.empty:
    cols = [c for c in df_dsa_cpl.columns if 'CPL' in c.upper()]
    images_html.append(make_line_chart_img(df_dsa_cpl, df_dsa_cpl.columns[0], cols, "Degreefyd Online Google ads DSA campaign cpl_pannel and cpl_lms", ['CPL Pannel', 'CPL LMS']))
if not df_dsa_lead.empty:
    cols = [c for c in df_dsa_lead.columns if 'PANNEL' in c.upper() or 'LMS' in c.upper()]
    images_html.append(make_line_chart_img(df_dsa_lead, df_dsa_lead.columns[0], cols, "Degreefyd Online Google ads DSA campaign lead_pannel and lead_lms", ['Lead Pannel', 'Lead LMS']))

if not df_meta_cpl.empty:
    cols = [c for c in df_meta_cpl.columns if 'CPL' in c.upper()]
    images_html.append(make_line_chart_img(df_meta_cpl, df_meta_cpl.columns[0], cols, "Degreefyd Online META ads cpl_pannel and cpl_lms", ['CPL Pannel', 'CPL LMS']))
if not df_meta_lead.empty:
    cols = [c for c in df_meta_lead.columns if 'PANNEL' in c.upper() or 'LMS' in c.upper()]
    images_html.append(make_line_chart_img(df_meta_lead, df_meta_lead.columns[0], cols, "Degreefyd Online META ads lead_pannel and lead_lms", ['Lead Pannel', 'Lead LMS']))

if not df_brand_cpl.empty:
    cols = [c for c in df_brand_cpl.columns if 'CPL' in c.upper()]
    images_html.append(make_line_chart_img(df_brand_cpl, df_brand_cpl.columns[0], cols, "Degreefyd Online Google ads Brand campaign cpl_pannel and cpl_lms", ['CPL Pannel', 'CPL LMS']))
if not df_brand_lead.empty:
    cols = [c for c in df_brand_lead.columns if 'PANNEL' in c.upper() or 'LMS' in c.upper()]
    images_html.append(make_line_chart_img(df_brand_lead, df_brand_lead.columns[0], cols, "Degreefyd Online Google ads Brand campaign lead_pannel and lead_lms", ['Lead Pannel', 'Lead LMS']))

dashboard = data.get("Dashboard", [])
meta_ytd, google_ytd = [], []
for r in dashboard:
    if len(r) > 5 and 'Meta' in r[4]: meta_ytd = r
    if len(r) > 5 and 'Google' in r[4]: google_ytd = r

def parse_num(val):
    try: return float(str(val).replace(',', ''))
    except: return 0

if meta_ytd and google_ytd:
    x_data = ['Meta Ads', 'Google Ads']
    y_spends = [parse_num(meta_ytd[5]), parse_num(google_ytd[5])]
    y_leads_p = [parse_num(meta_ytd[6]), parse_num(google_ytd[6])]
    y_leads_l = [parse_num(meta_ytd[7]), parse_num(google_ytd[7])]
    y_cpl_p = [parse_num(meta_ytd[9]), parse_num(google_ytd[9])]
    y_cpl_l = [parse_num(meta_ytd[10]), parse_num(google_ytd[10])]
    
    images_html.insert(0, make_bar_chart_img("Degreefyd Online overall CAC YTD 27-04-2026", x_data, [y_cpl_p, y_cpl_l], ["CPL Pannel", "CPL LMS"]))
    images_html.insert(0, make_bar_chart_img("Degreefyd Online overall Leads YTD 27-04-2026", x_data, [y_leads_p, y_leads_l], ["Leads Pannel", "Leads LMS"]))
    images_html.insert(0, make_bar_chart_img("Degreefyd Online overall Spends 27-04-2026", x_data, [y_spends], ["Spends"]))

# --- ASSEMBLE STRICT HTML ---
html_out = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
    <title>Degreefyd Daily Dashboard</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; -webkit-tap-highlight-color: transparent; }}
        body {{ background-color: #07080f; color: #dde0f0; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; margin: 0; padding: 15px; }}
        .wrap {{ max-width: 1000px; margin: 0 auto; }}
        h1 {{ text-align: center; color: #fff; margin-bottom: 5px; font-weight: 700; font-family: system-ui, sans-serif; font-size: 20px; }}
        p.subtitle {{ text-align: center; color: #5a5d80; font-size: 11px; margin-bottom: 30px; }}
        .chart-container {{ background: #0F1018; border: 1px solid #22233a; border-radius: 8px; padding: 10px; margin-bottom: 24px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }}
    </style>
</head>
<body>
    <div class="wrap">
        <h1>Degreefyd Performance Dashboard</h1>
        <p class="subtitle">100% Static & WhatsApp Compliant • Rendered via Matplotlib</p>
        {''.join(images_html)}
    </div>
</body>
</html>
"""

with open("/workspace/Degreefyd_Final_Report.html", "w", encoding="utf-8") as f:
    f.write(html_out)

print("Generated Final Static HTML with embedded Base64 PNGs.")
