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

# --- DATA SOURCE ---
DATA_PATH = "latest_cac.json"
OUTPUT_PATH = "/workspace/Degreefyd_Final_Master_White.html"

# --- UTILS ---
def pnum(v):
    try:
        if isinstance(v, (int, float)): return float(v)
        s = str(v).replace(',', '').strip().replace('%', '').replace('₹', '')
        if s == '-' or s == '' or s == 'N/A' or s == '\u2014': return 0.0
        return float(s)
    except: return 0.0

def format_currency(v): 
    if abs(v) >= 100000: return f"₹{v/100000:.1f}L"
    return f"₹{v:,.0f}"

def format_currency_full(v): return f"₹{v:,.0f}"
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
    if metric == 'dup':
        if value <= 10: return "background:rgba(16,185,129,.20);" 
        if value <= 20: return "background:rgba(245,158,11,.20);" 
        return "background:rgba(239,68,68,.22);" 
    if all_values is not None and len(all_values) > 1:
        ranks = sorted(list(set(all_values)))
        if metric in ['cpl_p', 'cpl_l', 'cac_f', 'cac_a']:
            if value == ranks[0]: return "background:rgba(16,185,129,.20);"
            if value == ranks[-1]: return "background:rgba(239,68,68,.20);"
        if metric in ['l2f', 'l2a', 'f2a']:
            if value == ranks[-1]: return "background:rgba(16,185,129,.20);"
            if value == ranks[0]: return "background:rgba(239,68,68,.20);"
    return ""

# --- DATA PROCESSING ---
print("Loading latest data...")
with open(DATA_PATH, 'r') as f: raw_data = json.load(f)
df = pd.DataFrame(raw_data[2:], columns=[c.strip() for c in raw_data[1]])
for c in ['Spends', 'Pannel_Lead', 'Lead_LMS', 'FFH', 'Adm', 'Invoicing_Var']:
    if c in df.columns: df[c] = df[c].apply(pnum)
df['Date_Parsed'] = pd.to_datetime(df['Date'], errors='coerce')
df = df.dropna(subset=['Date_Parsed'])
today = df['Date_Parsed'].max()

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

ytd_h = aggregate(datetime(today.year, 1, 1), today)
mtd_h = aggregate(datetime(today.year, today.month, 1), today)
ftd_h = aggregate(today, today)

# --- COMPONENT BUILDERS ---
def render_tr(label, data, is_account=False, is_camp=False, is_daily=False, cid=None, pi="", indent=0, custom_bg=None, custom_co=None, overall_data=None):
    s = data
    r = rats(s)
    cls = "account-row" if is_account else "camp-row" if is_camp else "daily-row" if is_daily else ""
    style = f' style="background:{custom_bg}; color:{custom_co if custom_co else "inherit"}; font-weight:bold;"' if custom_bg else ""
    lbl_content = f"<strong>{label}</strong>"
    if is_account: lbl_content = f'<label for="{cid}" class="exp-lbl"><span class="chev">\u25b6</span> {pi} <strong>{label}</strong></label>'
    elif is_camp: lbl_content = f'<label for="{cid}" class="exp-lbl" style="padding-left:{indent}px;"><span class="chev">\u25b6</span> ↳ {label}</label>'
    elif is_daily: lbl_content = f'<span style="padding-left:{indent}px;">{label}</span>'
    td_style = f' style="background:{custom_bg};"' if custom_bg else ""
    def gcs(metric, val):
        if overall_data is None: return ""
        return f' style="{get_color_style(metric, val, overall_data.get(metric))}"'
    return f"""<tr class="{cls}"{style}>
    <td class="text-left sticky-col"{td_style}>{lbl_content}</td>
    <td class="num">{format_currency_full(s['Spends'])}</td><td class="num">{format_num(s['Pannel_Lead'])}</td><td class="num">{format_num(s['Lead_LMS'])}</td>
    <td class="num"{gcs('dup', r['dup'])}>{format_pct(r['dup'])}</td><td class="num">{format_num(s['FFH'])}</td><td class="num">{format_num(s['Adm'])}</td>
    <td class="num">{format_currency_full(s['Invoicing_Var'])}</td><td class="num"{gcs('cpl_p', r['cpl_p'])}>{format_currency_full(r['cpl_p'])}</td>
    <td class="num"{gcs('cpl_l', r['cpl_l'])}>{format_currency_full(r['cpl_l'])}</td><td class="num"{gcs('cac_f', r['cac_f'])}>{format_currency_full(r['cac_f'])}</td>
    <td class="num"{gcs('cac_a', r['cac_a'])}>{format_currency_full(r['cac_a'])}</td><td class="num">{format_currency_full(r['arpu'])}</td>
    <td class="num">{format_pct(r['cac_arpu']*100)}</td><td class="num"{gcs('l2f', r['l2f'])}>{format_pct(r['l2f'])}</td>
    <td class="num"{gcs('l2a', r['l2a'])}>{format_pct(r['l2a'])}</td><td class="num"{gcs('f2a', r['f2a'])}>{format_pct(r['f2a'])}</td>
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
                for _, r in c['rows'].head(5).iterrows():
                    r_data = {col: r[col] for col in ['Spends', 'Pannel_Lead', 'Lead_LMS', 'FFH', 'Adm', 'Invoicing_Var']}
                    html += render_tr(f"{r['Date']} - {r['Ad Name']}", r_data, is_daily=True, indent=50).replace('<tr class="daily-row">', f'<tr class="daily-row daily-{iid}">')
            html += '</tbody>'
    return ins, css, html + '</table></div>'

def build_overall_cac(start, end):
    platform_configs = [("META ADS", "Meta", None), ("Google Ads - Brand", "Google", "Brand"), ("Google Ads - DSA", "Google", "DSA"), ("Google Ads - Generic", "Google", "Generic")]
    overall_metrics = {'dup':[], 'cpl_p':[], 'cpl_l':[], 'cac_f':[], 'cac_a':[], 'l2f':[], 'l2a':[], 'f2a':[]}
    mask = (df['Date_Parsed'] >= start) & (df['Date_Parsed'] <= end)
    p_df = df[mask].copy(); rows = []
    for l, p, t in platform_configs:
        f = p_df.copy()
        if p: f = f[f['Platform'].str.contains(p, case=False, na=False)]
        if t: f = f[f['Type'].str.contains(t, case=False, na=False)]
        s = {c: f[c].sum() for c in ['Spends', 'Pannel_Lead', 'Lead_LMS', 'FFH', 'Adm', 'Invoicing_Var']}
        if s['Spends'] > 0:
            rt = rats(s)
            for k in overall_metrics: overall_metrics[k].append(rt[k])
        rows.append((l, s))
    ov = {c: p_df[c].sum() for c in ['Spends', 'Pannel_Lead', 'Lead_LMS', 'FFH', 'Adm', 'Invoicing_Var']}
    rows.append(("OVERALL TOTAL", ov))
    html = '<div class="table-wrap"><table class="overall-table"><thead><tr><th class="text-left sticky-col">Platform</th><th class="num">Spends</th><th class="num">Pannel_Leads</th><th class="num">Leads_LMS</th><th class="num">Dup %</th><th class="num">FFH</th><th class="num">ADM</th><th class="num">Inv_Var</th><th class="num">CPL_Pannel</th><th class="num">CPL_LMS</th><th class="num">CAC_FFH</th><th class="num">CAC_Adm</th><th class="num">ARPU</th><th class="num">CAC/ARPU</th><th class="num">L2F</th><th class="num">L2A</th><th class="num">F2A</th></tr></thead><tbody>'
    for label, s in rows:
        bg = "#f8fafc" if label == "OVERALL TOTAL" else "#ffffff"
        html += render_tr(label, s, custom_bg=bg, overall_data=overall_metrics if label != "OVERALL TOTAL" else None)
    return html + '</tbody></table></div>'

def build_kpi_hero(period_label, date_label, stats, timeframe_label):
    r = rats(stats)
    return f"""<div class="kpi-hero"><div class="kh-item"><div class="kh-lbl">Period</div><div class="kh-val dim">{period_label} \u2014 {date_label}</div></div><div class="kh-item"><div class="kh-lbl">Total Spend</div><div class="kh-val ">{format_currency(stats['Spends'])}</div></div><div class="kh-item"><div class="kh-lbl">Panel Leads</div><div class="kh-val amber">{format_num(stats['Pannel_Lead'])}</div></div><div class="kh-item"><div class="kh-lbl">LMS Leads</div><div class="kh-val amber">{format_num(stats['Lead_LMS'])}</div></div><div class="kh-item"><div class="kh-lbl">CPL Panel</div><div class="kh-val green">{format_currency_full(r['cpl_p'])}</div></div><div class="kh-item"><div class="kh-lbl">CPL LMS</div><div class="kh-val green">{format_currency_full(r['cpl_l'])}</div></div><div class="kh-item"><div class="kh-lbl">FFH</div><div class="kh-val purple">{format_num(stats['FFH'])}</div></div><div class="kh-item"><div class="kh-lbl">ADM</div><div class="kh-val purple">{format_num(stats['Adm'])}</div></div></div><div class="kpi-band"><div class="kpi-band-title">{period_label} \u2014 {timeframe_label} ({date_label})</div><div class="kpi-scroll"><div class="kc ac-blue"><div class="kc-lbl">Total Spend</div><div class="kc-val">{format_currency(stats['Spends'])}</div><div class="kc-sub">{period_label}</div></div><div class="kc ac-blue"><div class="kc-lbl">Panel Leads</div><div class="kc-val">{format_num(stats['Pannel_Lead'])}</div><div class="kc-sub">CPL {format_currency_full(r['cpl_p'])}</div></div><div class="kc ac-cyan"><div class="kc-lbl">LMS Leads</div><div class="kc-val">{format_num(stats['Lead_LMS'])}</div><div class="kc-sub">CPL {format_currency_full(r['cpl_l'])}</div></div><div class="kc ac-green"><div class="kc-lbl">FFH</div><div class="kc-val">{format_num(stats['FFH'])}</div><div class="kc-sub">CAC {format_currency_full(r['cac_f'])}</div></div><div class="kc ac-green"><div class="kc-lbl">ADM</div><div class="kc-val">{format_num(stats['Adm'])}</div><div class="kc-sub">CAC {format_currency_full(r['cac_a'])}</div></div><div class="kc ac-purple"><div class="kc-lbl">L2F Rate</div><div class="kc-val">{format_pct(r['l2f'])}</div><div class="kc-sub">Lead &#8594; FFH</div></div><div class="kc ac-purple"><div class="kc-lbl">L2A Rate</div><div class="kc-val">{format_pct(r['l2a'])}</div><div class="kc-sub">Lead &#8594; ADM</div></div><div class="kc ac-amber"><div class="kc-lbl">F2A Rate</div><div class="kc-val">{format_pct(r['f2a'])}</div><div class="kc-sub">FFH &#8594; ADM</div></div><div class="kc ac-orange"><div class="kc-lbl">Inv Variance</div><div class="kc-val">{format_currency(stats['Invoicing_Var'])}</div><div class="kc-sub">Revenue proxy</div></div></div></div>"""

# --- GRAPH BUILDERS ---
def prep_g_fuzzy(g_file):
    with open(g_file, 'r') as f: data = json.load(f)
    if not data or len(data) < 2: return pd.DataFrame(), "", "", "", ""
    df_g = pd.DataFrame(data[1:], columns=[c.strip() for c in data[0]])
    x = df_g.columns[0]
    def fc(d, p):
        for c in d.columns:
            if p.upper() in str(c).upper().replace(' ', '').replace('_', ''): return c
        return None
    sp, lp, ll = fc(df_g, 'SPEND'), fc(df_g, 'PANNEL'), fc(df_g, 'LMS')
    for c in [sp, lp, ll]: 
        if c: df_g[c] = df_g[c].apply(pnum)
    df_g['Date_Parsed'] = pd.to_datetime(df_g[x], errors='coerce')
    df_g = df_g.sort_values('Date_Parsed').dropna(subset=['Date_Parsed'])
    df_g['X'] = df_g['Date_Parsed'].dt.strftime('%b %d')
    return df_g, 'X', sp, lp, ll

def create_line_pair(g_file, plat):
    dfg, x, sp, lp, ll = prep_g_fuzzy(g_file)
    if dfg.empty: return "", ""
    dfg['CPL_P'] = dfg[sp]/dfg[lp]; dfg['CPL_L'] = dfg[sp]/dfg[ll]
    dfg.replace([np.inf, -np.inf], 0, inplace=True)
    def chart(y1, y2, l1, l2, t, is_cpl):
        plt.rcParams.update({"axes.facecolor": "#ffffff", "figure.facecolor": "#ffffff", "text.color": "#0f172a", "font.family": "sans-serif"})
        fig, ax = plt.subplots(figsize=(12, 5), dpi=150)
        ax.plot(dfg[x], dfg[y1], marker='o', color='#059669' if not is_cpl else '#d97706', label=l1, linewidth=2.5, markersize=6)
        ax.plot(dfg[x], dfg[y2], marker='s', color='#7c3aed' if not is_cpl else '#dc2626', label=l2, linewidth=2.5, markersize=6)
        for i, v in enumerate(dfg[y1]): ax.text(i, v, (f"₹{v:,.0f}" if is_cpl else f"{v:,.0f}"), ha='center', va='bottom', fontweight='bold', fontsize=9, bbox=dict(facecolor='white', alpha=0.6, edgecolor='none', pad=1))
        for i, v in enumerate(dfg[y2]): ax.text(i, v, (f"₹{v:,.0f}" if is_cpl else f"{v:,.0f}"), ha='center', va='top', fontweight='bold', fontsize=9, bbox=dict(facecolor='white', alpha=0.6, edgecolor='none', pad=1))
        ax.set_title(t, pad=20, fontweight='bold', fontsize=14); ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=2, frameon=False)
        fig.tight_layout(); buf = io.BytesIO(); fig.savefig(buf, format="png"); plt.close(fig)
        return base64.b64encode(buf.getvalue()).decode('utf-8')
    return chart(lp, ll, 'Panel', 'LMS', f'Degreefyd Online Google ads {plat} campaign lead pannel and lead lms', False), chart('CPL_P', 'CPL_L', 'Panel', 'LMS', f'Degreefyd Online Google ads {plat} campaign cpl pannel and cpl lms', True)

# --- ASSEMBLE ---
print("Reconstructing dashboard...")
with open('/workspace/Degreefyd_Final_Master_White.html', 'r', encoding='utf-8') as f: tmpl = f.read()
head = re.search(r'<!DOCTYPE html>.*?</style>', tmpl, re.DOTALL).group(0)
foot = re.search(r'<div id="p5" class="panel".*</html>', tmpl, re.DOTALL).group(0)

f_in, f_cs, f_ht = build_hierarchy_table(ftd_h, "ftd")
m_in, m_cs, m_ht = build_hierarchy_table(mtd_h, "mtd")
y_in, y_cs, y_ht = build_hierarchy_table(ytd_h, "ytd")

last_7 = today - timedelta(days=7); recent_df = df[(df['Date_Parsed'] >= last_7) & (df['Date_Parsed'] < today)]
avg_c = (recent_df['Spends'].sum() / recent_df['Lead_LMS'].sum()) if recent_df['Lead_LMS'].sum() > 0 else 0
tod_s = {c: df[df['Date_Parsed'] == today][c].sum() for c in ['Spends', 'Pannel_Lead', 'Lead_LMS', 'FFH', 'Adm', 'Invoicing_Var']}
tod_c = (tod_s['Spends'] / tod_s['Lead_LMS']) if tod_s['Lead_LMS'] > 0 else 0
c_chg = ((tod_c - avg_c) / avg_c * 100) if avg_c > 0 else 0
best = df[df['Date_Parsed'] == today].sort_values('Adm', ascending=False).iloc[0] if not df[df['Date_Parsed'] == today].empty else {'Campaign': 'N/A', 'Adm': 0}

intel = f"""<div class="intel-card"><h3>AI Intelligence & Insights</h3><div class="intel-grid"><div class="intel-item"><span class="intel-label">CPL Trend (Today vs 7D Avg)</span><span class="intel-value" style="color:{'#dc2626' if c_chg > 10 else '#059669'};">{format_pct(abs(c_chg))} {'increased' if c_chg > 0 else 'decreased'}</span></div><div class="intel-item"><span class="intel-label">Daily Lead Flow</span><span class="intel-value">{format_num(tod_s['Lead_LMS'])} LMS Leads</span></div><div class="intel-item"><span class="intel-label">Top Performer</span><span class="intel-value">{best['Campaign']} ({format_num(best['Adm'])} Adms)</span></div></div></div>"""

m_start = datetime(today.year, today.month, 1); y_start = datetime(today.year, 1, 1)
m_s = {c: df[df['Date_Parsed'] >= m_start][c].sum() for c in ['Spends', 'Pannel_Lead', 'Lead_LMS', 'FFH', 'Adm', 'Invoicing_Var']}
y_s = {c: df[df['Date_Parsed'] >= y_start][c].sum() for c in ['Spends', 'Pannel_Lead', 'Lead_LMS', 'FFH', 'Adm', 'Invoicing_Var']}

p1 = f"""<div id="p1" class="panel">{intel}<h3 class="sec-title">DETAILED DRILLDOWN (FTD)</h3>{build_kpi_hero('FTD', today.strftime('%d %b'), tod_s, 'For The Day')}{f_ht}<h3 class="sec-title">Overall CAC (FTD)</h3>{build_overall_cac(today, today)}<h3 class="sec-title">DETAILED DRILLDOWN (MTD)</h3>{build_kpi_hero('MTD', today.strftime('%b %Y'), m_s, 'Month to Date')}{m_ht}<h3 class="sec-title">Overall CAC (MTD)</h3>{build_overall_cac(m_start, today)}<h3 class="sec-title">DETAILED DRILLDOWN (YTD)</h3>{build_kpi_hero('YTD', today.strftime('%Y'), y_s, 'Year to Date')}{y_ht}<h3 class="sec-title">Overall CAC (YTD)</h3>{build_overall_cac(y_start, today)}</div>"""

d_l, d_c = create_line_pair('latest_dsa_g1.json', 'DSA')
b_l, b_c = create_line_pair('latest_brand_g1.json', 'Brand')
m_l, m_c = create_line_pair('latest_meta_g1.json', 'META ADS')
def wg(l, c): return f'<div class="graph-card"><h4 class="graph-title">Leads Trend</h4><img src="data:image/png;base64,{l}" class="responsive-img"><h4 class="graph-title">CPL Trend</h4><img src="data:image/png;base64,{c}" class="responsive-img"></div>'

body = f"""</head><body>{f_in}{m_in}{y_in}<style>{f_cs}{m_cs}{y_cs}</style><input type="radio" name="tabs" id="t1" checked><input type="radio" name="tabs" id="t2"><input type="radio" name="tabs" id="t3"><input type="radio" name="tabs" id="t4"><input type="radio" name="tabs" id="t5"><div class="wrap"><div class="hdr"><h1>Degreefyd Master Dashboard</h1><p>Intelligence • {today.strftime('%d %b %Y')}</p></div><div class="tabs"><label for="t1" class="lbl-t1">📊 SUMMARIES</label><label for="t2" class="lbl-t2">🔷 DSA</label><label for="t3" class="lbl-t3">🔶 BRAND</label><label for="t4" class="lbl-t4">🟣 META ADS</label><label for="t5" class="lbl-t5">📈 GRAPHS</label></div>{p1}<div id="p2" class="panel">{wg(d_l, d_c)}</div><div id="p3" class="panel">{wg(b_l, b_c)}</div><div id="p4" class="panel">{wg(m_l, m_c)}</div>"""

with open(OUTPUT_PATH, "w", encoding="utf-8-sig") as f: f.write(head + body + foot)
print(f"Final file updated at {OUTPUT_PATH}")

load_dotenv("/workspace/.env")
WHAPI_TOKEN, WHATSAPP_GROUP = os.getenv("WHAPI_TOKEN"), os.getenv("WHATSAPP_GROUP")
with open(OUTPUT_PATH, "rb") as f: b64 = base64.b64encode(f.read()).decode('utf-8')
payload = {"to": WHATSAPP_GROUP, "media": f"data:text/html;name=Degreefyd_Final_Master_White.html;base64,{b64}", "caption": "🏆 **EXECUTIVE DASHBOARD - FIXED & UPDATED**\n\n✅ **Fixed Emojis:** Used raw characters + UTF-8-SIG for correct rendering.\n✅ **Latest Data:** Updated with data up to today.\n✅ **Format preserved:** Kept exact structure of provided HTML."}
requests.post("https://gate.whapi.cloud/messages/document", headers={"accept": "application/json", "authorization": f"Bearer {WHAPI_TOKEN}", "content-type": "application/json"}, json=payload)
print("Delivered to WhatsApp.")
