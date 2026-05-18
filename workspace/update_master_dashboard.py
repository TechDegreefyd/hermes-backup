import os
import json
import base64
import io
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from dotenv import load_dotenv
import warnings
import re

warnings.filterwarnings('ignore')

# --- CONFIG ---
TEMPLATE_PATH = "/workspace/Degreefyd_Final_Master_White.html"
OUTPUT_PATH = "/workspace/Degreefyd_Final_Master_White_Latest.html"
DATA_PATH = "latest_data.json"

# --- UTILS ---
def pnum(v):
    try:
        if isinstance(v, (int, float)): return float(v)
        s = str(v).replace(',', '').strip().replace('%', '').replace('₹', '')
        if s == '-' or s == '' or s == 'N/A' or s == '\u2014': return 0.0
        return float(s)
    except: return 0.0

def format_currency(v): return f"₹{v:,.0f}"
def format_pct(v): return f"{v:.1f}%"
def format_num(v): return f"{v:,.0f}"

def rats(v):
    sp = v.get('Spends', 0)
    lp = v.get('Pannel_Lead', 0)
    ll = v.get('Lead_LMS', 0)
    ff = v.get('FFH', 0)
    ad = v.get('Adm', 0)
    iv = v.get('Invoicing_Var', 0)
    
    cpl_p = sp/lp if lp > 0 else 0
    cpl_l = sp/ll if ll > 0 else 0
    cac_f = sp/ff if ff > 0 else 0
    cac_a = sp/ad if ad > 0 else 0
    arpu = iv/ad if ad > 0 else 0
    cac_arpu = (cac_a / arpu) if arpu > 0 else 0
    l2f = (ff / ll * 100) if ll > 0 else 0
    l2a = (ad / ll * 100) if ll > 0 else 0
    f2a = (ad / ff * 100) if ff > 0 else 0
    dup = ((lp - ll) / lp * 100) if lp > 0 else 0
    return {
        'cpl_p': cpl_p, 'cpl_l': cpl_l, 'cac_f': cac_f, 'cac_a': cac_a,
        'arpu': arpu, 'cac_arpu': cac_arpu, 'l2f': l2f, 'l2a': l2a, 'f2a': f2a, 'dup': dup
    }

def get_color_style(metric, value, all_values=None):
    # Conditional coloring logic from prompt
    if metric == 'dup':
        # Absolute: <=10% Green, 10-20% Amber, >20% Red
        if value <= 10: return "background:rgba(16,185,129,.20);" # Green
        if value <= 20: return "background:rgba(245,158,11,.20);" # Amber
        return "background:rgba(239,68,68,.22);" # Red
    
    if all_values is not None and len(all_values) > 1:
        ranks = sorted(list(set(all_values)))
        if metric in ['cpl_p', 'cpl_l', 'cac_f', 'cac_a']:
            # Best-to-worst rank: Lowest Green, Highest Red
            if value == ranks[0]: return "background:rgba(16,185,129,.20);"
            if value == ranks[-1]: return "background:rgba(239,68,68,.20);"
        if metric in ['l2f', 'l2a', 'f2a']:
            # Best-to-worst rank: Highest Green, Lowest Red
            if value == ranks[-1]: return "background:rgba(16,185,129,.20);"
            if value == ranks[0]: return "background:rgba(239,68,68,.20);"
    return ""

# --- FETCH & PROCESS ---
print("Loading data...")
with open(DATA_PATH, 'r') as f:
    raw = json.load(f)

headers = [str(h).strip() for h in raw[1]]
df = pd.DataFrame(raw[2:], columns=headers)

df['Platform'] = df['Platform'].fillna('').str.strip()
df['Type'] = df['Type'].fillna('').str.strip()
df['Account'] = df['Account'].fillna('').str.strip()
df['Campaign'] = df['Campaign'].fillna('').str.strip()
df['Ad Name'] = df['Ad Name'].fillna('').str.strip()

for c in ['Spends', 'Pannel_Lead', 'Lead_LMS', 'FFH', 'Adm', 'Invoicing_Var']:
    if c in df.columns: df[c] = df[c].apply(pnum)

df['Date_Parsed'] = pd.to_datetime(df['Date'], errors='coerce')
df = df.dropna(subset=['Date_Parsed'])
today = df['Date_Parsed'].max()

ytd_start = datetime(today.year, 1, 1)
mtd_start = datetime(today.year, today.month, 1)
ftd_start = today # Single latest day

def aggregate(start, end):
    mask = (df['Date_Parsed'] >= start) & (df['Date_Parsed'] <= end)
    f = df[mask].copy()
    h = {}
    for plat in sorted(f['Platform'].unique()):
        if not plat: continue
        h[plat] = {}
        for acct in sorted(f[f['Platform']==plat]['Account'].unique()):
            if not acct: continue
            a_df = f[(f['Platform']==plat) & (f['Account']==acct)]
            h[plat][acct] = {
                'stats': {c: a_df[c].sum() for c in ['Spends', 'Pannel_Lead', 'Lead_LMS', 'FFH', 'Adm', 'Invoicing_Var']},
                'campaigns': []
            }
            for camp in sorted(a_df['Campaign'].unique()):
                c_df = a_df[a_df['Campaign']==camp]
                h[plat][acct]['campaigns'].append({
                    'Campaign': camp, 
                    'Spends': c_df['Spends'].sum(), 
                    'Pannel_Lead': c_df['Pannel_Lead'].sum(), 
                    'Lead_LMS': c_df['Lead_LMS'].sum(), 
                    'FFH': c_df['FFH'].sum(), 
                    'Adm': c_df['Adm'].sum(), 
                    'Invoicing_Var': c_df['Invoicing_Var'].sum(),
                    'rows': c_df.sort_values('Date_Parsed', ascending=False)
                })
    return h

print("Aggregating...")
ytd_h = aggregate(ytd_start, today)
mtd_h = aggregate(mtd_start, today)
ftd_h = aggregate(ftd_start, today)

# --- COMPONENT BUILDERS ---

def render_tr(label, data, is_account=False, is_camp=False, is_daily=False, cid=None, pi="", indent=0, custom_bg=None, custom_co=None, overall_data=None):
    s = data
    r = rats(s)
    
    cls = ""
    if is_account: cls = "account-row"
    elif is_camp: cls = "camp-row"
    elif is_daily: cls = "daily-row"
    
    style = f' style="background:{custom_bg}; color:{custom_co if custom_co else "inherit"}; font-weight:bold;"' if custom_bg else ""
    lbl_content = f"<strong>{label}</strong>"
    if is_account: lbl_content = f'<label for="{cid}" class="exp-lbl"><span class="chev">▶</span> {pi} <strong>{label}</strong></label>'
    elif is_camp: lbl_content = f'<label for="{cid}" class="exp-lbl" style="padding-left:{indent}px;"><span class="chev">▶</span> ↳ {label}</label>'
    elif is_daily: lbl_content = f'<span style="padding-left:{indent}px;">{label}</span>'
    
    td_style = f' style="background:{custom_bg};"' if custom_bg else ""
    
    # Conditional styling for overall tables
    def get_cell_style(metric, val):
        if overall_data is None: return ""
        return f' style="{get_color_style(metric, val, overall_data.get(metric))}"'

    return f"""<tr class="{cls}"{style}>
        <td class="text-left sticky-col"{td_style}>{lbl_content}</td>
        <td class="num">{format_currency(s['Spends'])}</td>
        <td class="num">{format_num(s['Pannel_Lead'])}</td>
        <td class="num">{format_num(s['Lead_LMS'])}</td>
        <td class="num"{get_cell_style('dup', r['dup'])}>{format_pct(r['dup'])}</td>
        <td class="num">{format_num(s['FFH'])}</td>
        <td class="num">{format_num(s['Adm'])}</td>
        <td class="num">{format_currency(s['Invoicing_Var'])}</td>
        <td class="num"{get_cell_style('cpl_p', r['cpl_p'])}>{format_currency(r['cpl_p'])}</td>
        <td class="num"{get_cell_style('cpl_l', r['cpl_l'])}>{format_currency(r['cpl_l'])}</td>
        <td class="num"{get_cell_style('cac_f', r['cac_f'])}>{format_currency(r['cac_f'])}</td>
        <td class="num"{get_cell_style('cac_a', r['cac_a'])}>{format_currency(r['cac_a'])}</td>
        <td class="num">{format_currency(r['arpu'])}</td>
        <td class="num">{format_pct(r['cac_arpu']*100)}</td>
        <td class="num"{get_cell_style('l2f', r['l2f'])}>{format_pct(r['l2f'])}</td>
        <td class="num"{get_cell_style('l2a', r['l2a'])}>{format_pct(r['l2a'])}</td>
        <td class="num"{get_cell_style('f2a', r['f2a'])}>{format_pct(r['f2a'])}</td>
    </tr>"""

def build_hierarchy_table(h, pref):
    ins, css, idx = "", "", 0
    html = '<div class="table-wrap"><table><thead><tr><th class="text-left sticky-col">Account / Campaign / Date</th><th class="num">Spends</th><th class="num">Pannel_Leads</th><th class="num">Leads_LMS</th><th class="num">Dup %</th><th class="num">FFH</th><th class="num">ADM</th><th class="num">Inv_Var</th><th class="num">CPL_Pannel</th><th class="num">CPL_LMS</th><th class="num">CAC_FFH</th><th class="num">CAC_Adm</th><th class="num">ARPU</th><th class="num">CAC/ARPU</th><th class="num">L2F</th><th class="num">L2A</th><th class="num">F2A</th></tr></thead>'
    for plat, accs in h.items():
        pi = "🔵" if "Google" in plat else "🟣" if "Meta" in plat else "⚪"
        for acct, data in accs.items():
            idx += 1
            cid = f"cb-{pref}-{idx}"
            ins += f'<input type="checkbox" id="{cid}" class="h-cb" tabindex="-1">\n'
            css += f"#{cid}:checked ~ .wrap #body-{cid} {{ display: table-row-group; }}\n#{cid}:checked ~ .wrap label[for='{cid}'] .chev {{ transform: rotate(90deg); }}\n"
            html += f'<tbody>{render_tr(acct, data["stats"], is_account=True, cid=cid, pi=pi)}</tbody>'
            html += f'<tbody class="camp-body" id="body-{cid}">'
            for ci, c in enumerate(data['campaigns']):
                iid = f"{cid}-c-{ci}"
                ins += f'<input type="checkbox" id="{iid}" class="h-cb" tabindex="-1">\n'
                css += f"#{iid}:checked ~ .wrap .daily-{iid} {{ display: table-row; }}\n#{iid}:checked ~ .wrap label[for='{iid}'] .chev {{ transform: rotate(90deg); }}\n"
                html += render_tr(c["Campaign"], c, is_camp=True, cid=iid, indent=25)
                html += f'<tr class="daily-hdr daily-{iid}"><th colspan="17" style="text-align:left; padding-left:50px; background:#f8fafc;">Daily (Last 5 Days)</th></tr>'
                for _, r_row in c['rows'].head(5).iterrows():
                    r_data = {col: r_row[col] for col in ['Spends', 'Pannel_Lead', 'Lead_LMS', 'FFH', 'Adm', 'Invoicing_Var']}
                    html += render_tr(f"{r_row['Date']} - {r_row['Ad Name']}", r_data, is_daily=True, indent=50).replace('<tr class="daily-row">', f'<tr class="daily-row daily-{iid}">')
            html += '</tbody>'
    return ins, css, html + '</table></div>'

def build_overall_cac(start, end):
    rows = []
    platform_configs = [
        ("Meta Ads", "Meta", None), 
        ("Google Brand", "Google", "Brand"), 
        ("Google DSA", "Google", "DSA"), 
        ("Google Generic", "Google", "Generic")
    ]
    
    overall_metrics = {'dup':[], 'cpl_p':[], 'cpl_l':[], 'cac_f':[], 'cac_a':[], 'l2f':[], 'l2a':[], 'f2a':[]}
    
    for l, p, t in platform_configs:
        mask = (df['Date_Parsed'] >= start) & (df['Date_Parsed'] <= end)
        f = df[mask].copy()
        if p: f = f[f['Platform'].str.contains(p, case=False, na=False)]
        if t: f = f[f['Type'].str.contains(t, case=False, na=False)]
        s = {c: f[c].sum() for c in ['Spends', 'Pannel_Lead', 'Lead_LMS', 'FFH', 'Adm', 'Invoicing_Var']}
        if s['Spends'] > 0:
            rt = rats(s)
            for k in overall_metrics: overall_metrics[k].append(rt[k])
        rows.append((l, s))
    
    mask = (df['Date_Parsed'] >= start) & (df['Date_Parsed'] <= end)
    ov = {c: df[mask][c].sum() for c in ['Spends', 'Pannel_Lead', 'Lead_LMS', 'FFH', 'Adm', 'Invoicing_Var']}
    rows.append(("OVERALL TOTAL", ov))
    
    h = '<div class="table-wrap"><table class="overall-table"><thead><tr><th class="text-left sticky-col">Platform</th><th class="num">Spends</th><th class="num">Pannel_Leads</th><th class="num">Leads_LMS</th><th class="num">Dup %</th><th class="num">FFH</th><th class="num">ADM</th><th class="num">Inv_Var</th><th class="num">CPL_Pannel</th><th class="num">CPL_LMS</th><th class="num">CAC_FFH</th><th class="num">CAC_Adm</th><th class="num">ARPU</th><th class="num">CAC/ARPU</th><th class="num">L2F</th><th class="num">L2A</th><th class="num">F2A</th></tr></thead><tbody>'
    for label, s in rows:
        bg = "#f8fafc" if label == "OVERALL TOTAL" else "#ffffff"
        h += render_tr(label, s, custom_bg=bg, overall_data=overall_metrics if label != "OVERALL TOTAL" else None)
    return h + '</tbody></table></div>'

def build_kpi_hero(period_label, date_label, stats):
    r = rats(stats)
    return f"""<div class="kpi-hero"><div class="kh-item"><div class="kh-lbl">Period</div><div class="kh-val dim">{period_label} — {date_label}</div></div><div class="kh-item"><div class="kh-lbl">Total Spend</div><div class="kh-val ">{format_currency(stats['Spends'])}</div></div><div class="kh-item"><div class="kh-lbl">Panel Leads</div><div class="kh-val amber">{format_num(stats['Pannel_Lead'])}</div></div><div class="kh-item"><div class="kh-lbl">LMS Leads</div><div class="kh-val amber">{format_num(stats['Lead_LMS'])}</div></div><div class="kh-item"><div class="kh-lbl">CPL Panel</div><div class="kh-val green">{format_currency(r['cpl_p'])}</div></div><div class="kh-item"><div class="kh-lbl">CPL LMS</div><div class="kh-val green">{format_currency(r['cpl_l'])}</div></div><div class="kh-item"><div class="kh-lbl">FFH</div><div class="kh-val purple">{format_num(stats['FFH'])}</div></div><div class="kh-item"><div class="kh-lbl">ADM</div><div class="kh-val purple">{format_num(stats['Adm'])}</div></div></div><div class="kpi-band"><div class="kpi-band-title">{period_label} — For The Day ({today.strftime('%d %b %Y')})</div><div class="kpi-scroll"><div class="kc ac-blue"><div class="kc-lbl">Total Spend</div><div class="kc-val">{format_currency(stats['Spends'])}</div><div class="kc-sub">Today</div></div><div class="kc ac-blue"><div class="kc-lbl">Panel Leads</div><div class="kc-val">{format_num(stats['Pannel_Lead'])}</div><div class="kc-sub">CPL {format_currency(r['cpl_p'])}</div></div><div class="kc ac-cyan"><div class="kc-lbl">LMS Leads</div><div class="kc-val">{format_num(stats['Lead_LMS'])}</div><div class="kc-sub">CPL {format_currency(r['cpl_l'])}</div></div><div class="kc ac-green"><div class="kc-lbl">FFH</div><div class="kc-val">{format_num(stats['FFH'])}</div><div class="kc-sub">CAC {format_currency(r['cac_f'])}</div></div><div class="kc ac-green"><div class="kc-lbl">ADM</div><div class="kc-val">{format_num(stats['Adm'])}</div><div class="kc-sub">CAC {format_currency(r['cac_a'])}</div></div><div class="kc ac-purple"><div class="kc-lbl">L2F Rate</div><div class="kc-val">{format_pct(r['l2f'])}</div><div class="kc-sub">Lead \u2192 FFH</div></div><div class="kc ac-purple"><div class="kc-lbl">L2A Rate</div><div class="kc-val">{format_pct(r['l2a'])}</div><div class="kc-sub">Lead \u2192 ADM</div></div><div class="kc ac-amber"><div class="kc-lbl">F2A Rate</div><div class="kc-val">{format_pct(r['f2a'])}</div><div class="kc-sub">FFH \u2192 ADM</div></div><div class="kc ac-orange"><div class="kc-lbl">Inv Variance</div><div class="kc-val">{format_currency(stats['Invoicing_Var'])}</div><div class="kc-sub">Revenue proxy</div></div></div></div>"""

def get_intelligence():
    last_7 = today - timedelta(days=7)
    recent_mask = (df['Date_Parsed'] >= last_7) & (df['Date_Parsed'] < today)
    today_mask = df['Date_Parsed'] == today
    
    recent_df = df[recent_mask]
    today_df = df[today_mask]
    
    if today_df.empty: return '<div class="intel-card"><h3>AI Intelligence & Insights</h3><p>No data for today yet.</p></div>'
    
    avg_cpl = (recent_df['Spends'].sum() / recent_df['Lead_LMS'].sum()) if recent_df['Lead_LMS'].sum() > 0 else 0
    today_cpl = (today_df['Spends'].sum() / today_df['Lead_LMS'].sum()) if today_df['Lead_LMS'].sum() > 0 else 0
    
    cpl_change = ((today_cpl - avg_cpl) / avg_cpl * 100) if avg_cpl > 0 else 0
    cpl_status = "increased" if cpl_change > 0 else "decreased"
    cpl_color = "#dc2626" if cpl_change > 10 else "#059669"
    
    best_camp = today_df.sort_values('Adm', ascending=False).iloc[0]
    
    return f"""
    <div class="intel-card">
        <h3>AI Intelligence & Insights</h3>
        <div class="intel-grid">
            <div class="intel-item">
                <span class="intel-label">CPL Trend (Today vs 7D Avg)</span>
                <span class="intel-value" style="color:{cpl_color};">{format_pct(abs(cpl_change))} {cpl_status}</span>
            </div>
            <div class="intel-item">
                <span class="intel-label">Daily Lead Flow</span>
                <span class="intel-value">{format_num(today_df['Lead_LMS'].sum())} LMS Leads</span>
            </div>
            <div class="intel-item">
                <span class="intel-label">Top Performer</span>
                <span class="intel-value">{best_camp['Campaign']} ({format_num(best_camp['Adm'])} Adms)</span>
            </div>
        </div>
    </div>
    """

# --- GRAPHS (FOR TABS 2,3,4) ---
# Since I don't want to break the "Graph Builder" which extracts from tables,
# but the skill says "Mandatory 6 Graphs", I'll generate them as images.

def prep_g_fuzzy(g1_rows, g2_rows):
    if not g1_rows or not g2_rows or len(g1_rows) < 2: return pd.DataFrame(), "", "", "", "", ""
    d1 = pd.DataFrame(g1_rows[1:], columns=[str(c).strip() for c in g1_rows[0]])
    d2 = pd.DataFrame(g2_rows[1:], columns=[str(c).strip() for c in g2_rows[0]])
    x1, x2 = d1.columns[0], d2.columns[0]
    def fc(df, p):
        for c in df.columns:
            if p.upper() in str(c).upper().replace(' ', '').replace('_', ''): return c
        return None
    sp_col, lp_col = fc(d1, 'SPEND'), fc(d1, 'PANNEL')
    ll_col = fc(d2, 'LMS')
    if not sp_col or not lp_col or not ll_col: return pd.DataFrame(), "", "", "", "", ""
    d1_sub = d1[[x1, sp_col, lp_col]].copy(); d1_sub.columns = ['Date_Shared', 'Spends_Internal', 'Pannel_Internal']
    d2_sub = d2[[x2, ll_col]].copy(); d2_sub.columns = ['Date_Shared', 'LMS_Internal']
    m = pd.merge(d1_sub, d2_sub, on='Date_Shared')
    for c in ['Spends_Internal', 'Pannel_Internal', 'LMS_Internal']: m[c] = m[c].apply(pnum)
    m['CPL_P'], m['CPL_L'] = m['Spends_Internal']/m['Pannel_Internal'], m['Spends_Internal']/m['LMS_Internal']
    m.replace([np.inf, -np.inf], 0, inplace=True); m.fillna(0, inplace=True)
    m['Date_Parsed'] = pd.to_datetime(m['Date_Shared'], errors='coerce')
    m = m.sort_values(by='Date_Parsed').dropna(subset=['Date_Parsed'])
    m['X'] = m['Date_Parsed'].dt.strftime('%b %d')
    return m, 'X', 'CPL_P', 'CPL_L', 'Pannel_Internal', 'LMS_Internal'

def create_line_chart(dfg, x, y1, y2, t, l1, l2, color1, color2, is_cpl=False):
    if dfg.empty: return ""
    plt.rcParams.update({"axes.facecolor": "#ffffff", "figure.facecolor": "#ffffff", "text.color": "#0f172a"})
    fig, ax = plt.subplots(figsize=(12, 5), dpi=150)
    ax.plot(dfg[x], dfg[y1], marker='o', color=color1, label=l1, linewidth=2.5, markersize=6)
    ax.plot(dfg[x], dfg[y2], marker='s', color=color2, label=l2, linewidth=2.5, markersize=6)
    for i, v in enumerate(dfg[y1]):
        lbl = f"₹{v:,.0f}" if is_cpl else f"{v:,.0f}"
        ax.text(i, v, lbl, ha='center', va='bottom', fontweight='bold', color=color1, fontsize=9, bbox=dict(facecolor='white', alpha=0.6, edgecolor='none', pad=1))
    for i, v in enumerate(dfg[y2]):
        lbl = f"₹{v:,.0f}" if is_cpl else f"{v:,.0f}"
        ax.text(i, v, lbl, ha='center', va='top', fontweight='bold', color=color2, fontsize=9, bbox=dict(facecolor='white', alpha=0.6, edgecolor='none', pad=1))
    ax.set_title(t, pad=20, fontweight='bold', fontsize=14)
    ax.set_xticks(range(len(dfg[x]))); ax.set_xticklabels(dfg[x], rotation=45, ha="right")
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=2, frameon=False)
    fig.tight_layout()
    buf = io.BytesIO(); fig.savefig(buf, format="png"); plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode('utf-8')

# Load graph data
with open('dsa_g1.json', 'r') as f: dsa_g1 = json.load(f)
with open('dsa_g2.json', 'r') as f: dsa_g2 = json.load(f)
with open('brand_g1.json', 'r') as f: brand_g1 = json.load(f)
with open('brand_g2.json', 'r') as f: brand_g2 = json.load(f)
with open('meta_g1.json', 'r') as f: meta_g1 = json.load(f)
with open('meta_g2.json', 'r') as f: meta_g2 = json.load(f)

# --- RECONSTRUCT HTML ---
print("Reconstructing HTML...")
with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
    template = f.read()

# 1. Extract Head (up to checkbox inputs)
head_match = re.search(r'<!DOCTYPE html>.*?</style></head><body>', template, re.DOTALL)
head = head_match.group(0)

# 2. Extract Foot (from Tab 5 Graph Builder)
foot_match = re.search(r'/\* ══ Tab 5 – Graph Builder.*</html>', template, re.DOTALL)
foot = foot_match.group(0)

# 3. Build Body
body_parts = []

# Checkboxes and Styles for hierarchy
y_in, y_cs, y_ht = build_hierarchy_table(ytd_h, "ytd")
m_in, m_cs, m_ht = build_hierarchy_table(mtd_h, "mtd")
f_in, f_cs, f_ht = build_hierarchy_table(ftd_h, "ftd")

body_parts.append(f"<style>{y_cs}{m_cs}{f_cs}</style>")
body_parts.append(y_in + m_in + f_in)

# Radios for tabs
body_parts.append('<input type="radio" name="tabs" id="t1" checked><input type="radio" name="tabs" id="t2"><input type="radio" name="tabs" id="t3"><input type="radio" name="tabs" id="t4"><input type="radio" name="tabs" id="t5">')

# Main Wrap
body_parts.append(f'<div class="wrap"><div class="hdr"><h1>Degreefyd Master Dashboard</h1><p>Intelligence • {today.strftime("%d %b %Y")}</p></div>')

# Tabs labels
body_parts.append('<div class="tabs"><label for="t1" class="lbl-t1">\ud83d\udcca SUMMARIES</label><label for="t2" class="lbl-t2">\ud83d\udd3a DSA</label><label for="t3" class="lbl-t3">\ud83d\udd36 BRAND</label><label for="t4" class="lbl-t4">\ud83d\udc3a META ADS</label><label for="t5" class="lbl-t5">\ud83d\udcc8 GRAPHS</label></div>')

# Panel 1: Summaries
stats_ftd = {c: df[df['Date_Parsed'] == today][c].sum() for c in ['Spends', 'Pannel_Lead', 'Lead_LMS', 'FFH', 'Adm', 'Invoicing_Var']}
stats_mtd = {c: df[df['Date_Parsed'] >= mtd_start][c].sum() for c in ['Spends', 'Pannel_Lead', 'Lead_LMS', 'FFH', 'Adm', 'Invoicing_Var']}
stats_ytd = {c: df[df['Date_Parsed'] >= ytd_start][c].sum() for c in ['Spends', 'Pannel_Lead', 'Lead_LMS', 'FFH', 'Adm', 'Invoicing_Var']}

p1 = f"""<div id="p1" class="panel">
    {get_intelligence()}
    <h3 class="sec-title">DETAILED DRILLDOWN (FTD)</h3>
    {build_kpi_hero('FTD', today.strftime('%d %b'), stats_ftd)}
    {f_ht}
    <h3 class="sec-title">Overall CAC (FTD)</h3>{build_overall_cac(ftd_start, today)}
    
    <h3 class="sec-title">DETAILED DRILLDOWN (MTD)</h3>
    {build_kpi_hero('MTD', today.strftime('%b %Y'), stats_mtd)}
    {m_ht}
    <h3 class="sec-title">Overall CAC (MTD)</h3>{build_overall_cac(mtd_start, today)}
    
    <h3 class="sec-title">DETAILED DRILLDOWN (YTD)</h3>
    {build_kpi_hero('YTD', today.strftime('%Y'), stats_ytd)}
    {y_ht}
    <h3 class="sec-title">Overall CAC (YTD)</h3>{build_overall_cac(ytd_start, today)}
</div>"""
body_parts.append(p1)

# Panels 2, 3, 4: DSA, Brand, Meta
def get_graph_card(g1, g2, plat_name):
    m, x, cpl_p, cpl_l, p_int, l_int = prep_g_fuzzy(g1, g2)
    b64_leads = create_line_chart(m, x, 'Pannel_Internal', 'LMS_Internal', f'Degreefyd Online Google ads {plat_name} campaign lead pannel and lead lms', 'Panel', 'LMS', '#059669', '#7c3aed')
    b64_cpl = create_line_chart(m, x, 'CPL_P', 'CPL_L', f'Degreefyd Online Google ads {plat_name} campaign cpl pannel and cpl lms', 'Panel', 'LMS', '#d97706', '#dc2626', True)
    return f'<div class="graph-card"><h4 class="graph-title">{plat_name} Leads</h4><img src="data:image/png;base64,{b64_leads}" class="responsive-img"><h4 class="graph-title">{plat_name} CPL</h4><img src="data:image/png;base64,{b64_cpl}" class="responsive-img"></div>'

body_parts.append(f'<div id="p2" class="panel">{get_graph_card(dsa_g1, dsa_g2, "DSA")}</div>')
body_parts.append(f'<div id="p3" class="panel">{get_graph_card(brand_g1, brand_g2, "Brand")}</div>')
body_parts.append(f'<div id="p4" class="panel">{get_graph_card(meta_g1, meta_g2, "Meta")}</div>')

# Panel 5: Placeholder for Graph Builder (it will be injected from the footer)
body_parts.append('<div id="p5" class="panel" style="padding:0;">')

# Close main wrap
# Note: the footer contains the rest of the p5 content and the closing tags.

full_html = head + "".join(body_parts) + foot

print(f"Writing to {OUTPUT_PATH}...")
with open(OUTPUT_PATH, "w", encoding="utf-8", errors="replace") as f:
    f.write(full_html)

# --- SEND TO WHATSAPP ---
load_dotenv("/workspace/.env")
WHAPI_TOKEN, WHATSAPP_GROUP = os.getenv("WHAPI_TOKEN"), os.getenv("WHATSAPP_GROUP")
if not WHATSAPP_GROUP: WHATSAPP_GROUP = "120363426619711887@g.us"

with open(OUTPUT_PATH, "rb") as f:
    b64 = base64.b64encode(f.read()).decode('utf-8')

payload = {
    "to": WHATSAPP_GROUP,
    "media": f"data:text/html;name=Degreefyd_Final_Master_White.html;base64,{b64}",
    "caption": f"🏆 **FINAL EXECUTIVE DASHBOARD - UPDATED {today.strftime('%d %b %Y')}**\n\n✅ **Latest Data:** Fetched from Google Sheets (GID: 245632068).\n✅ **Graph Builder Active:** Tab 5 now working with latest totals.\n✅ **Conditional Coloring:** Row styles applied to FTD/MTD/YTD summaries.\n✅ **KPI Hero/Band:** Visual summaries at the top of each timeframe.\n\nEverything fully automated via Python."
}

resp = requests.post("https://gate.whapi.cloud/messages/document", 
                     headers={"accept": "application/json", "authorization": f"Bearer {WHAPI_TOKEN}", "content-type": "application/json"}, 
                     json=payload)

print(f"Delivered: {resp.status_code}")
