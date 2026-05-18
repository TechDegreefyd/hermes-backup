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
DATA_PATH = "latest_cac.json"
OUTPUT_PATH = "/workspace/Degreefyd_Final_Master_White.html"

# --- DATA LOADING ---
def load_json(path):
    with open(path, 'r') as f: return json.load(f)

latest_cac = load_json(DATA_PATH)
dsa_g1 = load_json('latest_dsa_g1.json')
dsa_g2 = load_json('latest_dsa_g2.json')
brand_g1 = load_json('latest_brand_g1.json')
brand_g2 = load_json('latest_brand_g2.json')
meta_g1 = load_json('latest_meta_g1.json')
meta_g2 = load_json('latest_meta_g2.json')

# --- PROCESSING ---
def pnum(v):
    try:
        if isinstance(v, (int, float)): return float(v)
        s = str(v).replace(',', '').strip().replace('%', '').replace('₹', '')
        if s == '-' or s == '' or s == 'N/A' or s == '\u2014': return 0.0
        return float(s)
    except: return 0.0

df = pd.DataFrame(latest_cac[2:], columns=[c.strip() for c in latest_cac[1]])
for c in ['Spends', 'Pannel_Lead', 'Lead_LMS', 'FFH', 'Adm', 'Invoicing_Var']:
    if c in df.columns: df[c] = df[c].apply(pnum)
df['Date_Parsed'] = pd.to_datetime(df['Date'], errors='coerce')
df = df.dropna(subset=['Date_Parsed'])
today = df['Date_Parsed'].max()

def aggregate(start, end):
    mask = (df['Date_Parsed'] >= start) & (df['Date_Parsed'] <= end)
    f = df[mask].copy(); h = {}
    for plat in sorted(f['Platform'].unique()):
        if not plat: continue
        h[plat] = {}
        for acct in sorted(f[f['Platform']==plat]['Account'].unique()):
            if not acct: continue
            a_df = f[(f['Platform']==plat) & (f['Account']==acct)]
            h[plat][acct] = {'stats': {c: a_df[c].sum() for c in ['Spends', 'Pannel_Lead', 'Lead_LMS', 'FFH', 'Adm', 'Invoicing_Var']}, 'campaigns': []}
            for camp in sorted(a_df['Campaign'].unique()):
                c_df = a_df[a_df['Campaign']==camp]
                h[plat][acct]['campaigns'].append({'Campaign': camp, 'Spends': c_df['Spends'].sum(), 'Pannel_Lead': c_df['Pannel_Lead'].sum(), 'Lead_LMS': c_df['Lead_LMS'].sum(), 'FFH': c_df['FFH'].sum(), 'Adm': c_df['Adm'].sum(), 'Invoicing_Var': c_df['Invoicing_Var'].sum(), 'rows': c_df.sort_values('Date_Parsed', ascending=False)})
    return h

ytd_h = aggregate(datetime(today.year, 1, 1), today)
mtd_h = aggregate(datetime(today.year, today.month, 1), today)
ftd_h = aggregate(today, today)

# --- UTILS FOR HTML ---
def format_currency(v): return f"₹{v:,.0f}"
def format_num(v): return f"{v:,.0f}"
def format_pct(v): return f"{v:.1f}%"

def rats(v):
    sp, lp, ll, ff, ad, iv = v['Spends'], v['Pannel_Lead'], v['Lead_LMS'], v['FFH'], v['Adm'], v['Invoicing_Var']
    cp, cl, cf, ca = sp/lp if lp>0 else 0, sp/ll if ll>0 else 0, sp/ff if ff>0 else 0, sp/ad if ad>0 else 0
    ar = iv/ad if ad>0 else 0; ca_ar = ca/ar if ar>0 else 0
    l2f, l2a, f2a = ff/ll*100 if ll>0 else 0, ad/ll*100 if ll>0 else 0, ad/ff*100 if ff>0 else 0
    dp = (lp-ll)/lp*100 if lp>0 else 0
    return {'cpl_p':cp,'cpl_l':cl,'cac_f':cf,'cac_a':ca,'arpu':ar,'cac_arpu':ca_ar,'l2f':l2f,'l2a':l2a,'f2a':f2a,'dup':dp}

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

def render_tr(label, data, is_account=False, is_camp=False, is_daily=False, cid=None, pi="", indent=0, custom_bg=None, overall_data=None):
    s = data; r = rats(s)
    cls = "account-row" if is_account else "camp-row" if is_camp else "daily-row" if is_daily else ""
    style = f' style="background:{custom_bg}; font-weight:bold;"' if custom_bg else ""
    lbl = f"<strong>{label}</strong>"
    if is_account: lbl = f'<label for="{cid}" class="exp-lbl"><span class="chev">\u25b6</span> {pi} <strong>{label}</strong></label>'
    elif is_camp: lbl = f'<label for="{cid}" class="exp-lbl" style="padding-left:{indent}px;"><span class="chev">\u25b6</span> ↳ {label}</label>'
    elif is_daily: lbl = f'<span style="padding-left:{indent}px;">{label}</span>'
    td_style = f' style="background:{custom_bg};"' if custom_bg else ""
    def gcs(metric, val):
        if overall_data is None: return ""
        return f' style="{get_color_style(metric, val, overall_data.get(metric))}"'
    return f"""<tr class="{cls}"{style}><td class="text-left sticky-col"{td_style}>{lbl}</td><td class="num">{format_currency(s['Spends'])}</td><td class="num">{format_num(s['Pannel_Lead'])}</td><td class="num">{format_num(s['Lead_LMS'])}</td><td class="num"{gcs('dup', r['dup'])}>{format_pct(r['dup'])}</td><td class="num">{format_num(s['FFH'])}</td><td class="num">{format_num(s['Adm'])}</td><td class="num">{format_currency(s['Invoicing_Var'])}</td><td class="num"{gcs('cpl_p', r['cpl_p'])}>{format_currency(r['cpl_p'])}</td><td class="num"{gcs('cpl_l', r['cpl_l'])}>{format_currency(r['cpl_l'])}</td><td class="num"{gcs('cac_f', r['cac_f'])}>{format_currency(r['cac_f'])}</td><td class="num"{gcs('cac_a', r['cac_a'])}>{format_currency(r['cac_a'])}</td><td class="num">{format_currency(r['arpu'])}</td><td class="num">{format_pct(r['cac_arpu']*100)}</td><td class="num"{gcs('l2f', r['l2f'])}>{format_pct(r['l2f'])}</td><td class="num"{gcs('l2a', r['l2a'])}>{format_pct(r['l2a'])}</td><td class="num"{gcs('f2a', r['f2a'])}>{format_pct(r['f2a'])}</td></tr>"""

def build_h_table(h, pref):
    ins, css, idx = "", "", 0
    html = '<div class="table-wrap"><table><thead><tr><th class="text-left sticky-col">Account / Campaign / Date</th><th class="num">Spends</th><th class="num">Pannel_Leads</th><th class="num">Leads_LMS</th><th class="num">Dup %</th><th class="num">FFH</th><th class="num">ADM</th><th class="num">Inv_Var</th><th class="num">CPL_Pannel</th><th class="num">CPL_LMS</th><th class="num">CAC_FFH</th><th class="num">CAC_Adm</th><th class="num">ARPU</th><th class="num">CAC/ARPU</th><th class="num">L2F</th><th class="num">L2A</th><th class="num">F2A</th></tr></thead>'
    for plat, accs in h.items():
        pi = "🔵" if "Google" in plat else "🟣" if "Meta" in plat else "⚪"
        for acct, data in accs.items():
            idx += 1; cid = f"cb-{pref}-{idx}"
            ins += f'<input type="checkbox" id="{cid}" class="h-cb" tabindex="-1">\n'
            css += f"#{cid}:checked ~ .wrap #body-{cid} {{ display: table-row-group; }}\n#{cid}:checked ~ .wrap label[for='{cid}'] .chev {{ transform: rotate(90deg); }}\n"
            html += f'<tbody>{render_tr(acct, data["stats"], is_account=True, cid=cid, pi=pi)}</tbody><tbody class="camp-body" id="body-{cid}">'
            for ci, c in enumerate(data['campaigns']):
                iid = f"{cid}-c-{ci}"; ins += f'<input type="checkbox" id="{iid}" class="h-cb" tabindex="-1">\n'
                css += f"#{iid}:checked ~ .wrap .daily-{iid} {{ display: table-row; }}\n#{iid}:checked ~ .wrap label[for='{iid}'] .chev {{ transform: rotate(90deg); }}\n"
                html += render_tr(c["Campaign"], c, is_camp=True, cid=iid, indent=25)
                html += f'<tr class="daily-hdr daily-{iid}"><th colspan="17" style="text-align:left; padding-left:50px; background:#f8fafc;">Daily (Last 5 Days)</th></tr>'
                for _, r in c['rows'].head(5).iterrows():
                    r_d = {col: r[col] for col in ['Spends', 'Pannel_Lead', 'Lead_LMS', 'FFH', 'Adm', 'Invoicing_Var']}
                    html += render_tr(f"{r['Date']} - {r['Ad Name']}", r_d, is_daily=True, indent=50).replace('<tr class="daily-row">', f'<tr class="daily-row daily-{iid}">')
            html += '</tbody>'
    return ins, css, html + '</table></div>'

def build_ov_cac(start, end):
    configs = [("META ADS", "Meta", None), ("Google Ads - Brand", "Google", "Brand"), ("Google Ads - DSA", "Google", "DSA"), ("Google Ads - Generic", "Google", "Generic")]
    metrics = {'dup':[], 'cpl_p':[], 'cpl_l':[], 'cac_f':[], 'cac_a':[], 'l2f':[], 'l2a':[], 'f2a':[]}
    mask = (df['Date_Parsed'] >= start) & (df['Date_Parsed'] <= end)
    p_df = df[mask].copy(); rows = []
    for l, p, t in configs:
        f = p_df.copy()
        if p: f = f[f['Platform'].str.contains(p, case=False, na=False)]
        if t: f = f[f['Type'].str.contains(t, case=False, na=False)]
        s = {c: f[c].sum() for c in ['Spends', 'Pannel_Lead', 'Lead_LMS', 'FFH', 'Adm', 'Invoicing_Var']}
        if s['Spends'] > 0:
            rt = rats(s)
            for k in metrics: metrics[k].append(rt[k])
        rows.append((l, s))
    ov = {c: p_df[c].sum() for c in ['Spends', 'Pannel_Lead', 'Lead_LMS', 'FFH', 'Adm', 'Invoicing_Var']}
    rows.append(("OVERALL TOTAL", ov))
    html = '<div class="table-wrap"><table class="overall-table"><thead><tr><th class="text-left sticky-col">Platform</th><th class="num">Spends</th><th class="num">Pannel_Leads</th><th class="num">Leads_LMS</th><th class="num">Dup %</th><th class="num">FFH</th><th class="num">ADM</th><th class="num">Inv_Var</th><th class="num">CPL_Pannel</th><th class="num">CPL_LMS</th><th class="num">CAC_FFH</th><th class="num">CAC_Adm</th><th class="num">ARPU</th><th class="num">CAC/ARPU</th><th class="num">L2F</th><th class="num">L2A</th><th class="num">F2A</th></tr></thead><tbody>'
    for label, s in rows:
        bg = "#f8fafc" if label == "OVERALL TOTAL" else "#ffffff"
        html += render_tr(label, s, custom_bg=bg, overall_data=metrics if label != "OVERALL TOTAL" else None)
    return html + '</tbody></table></div>'

def build_kpi(label, date, stats, timeframe):
    r = rats(stats)
    return f"""<div class="kpi-hero"><div class="kh-item"><div class="kh-lbl">Period</div><div class="kh-val dim">{label} \u2014 {date}</div></div><div class="kh-item"><div class="kh-lbl">Total Spend</div><div class="kh-val ">{format_currency(stats['Spends'])}</div></div><div class="kh-item"><div class="kh-lbl">Panel Leads</div><div class="kh-val amber">{format_num(stats['Pannel_Lead'])}</div></div><div class="kh-item"><div class="kh-lbl">LMS Leads</div><div class="kh-val amber">{format_num(stats['Lead_LMS'])}</div></div><div class="kh-item"><div class="kh-lbl">CPL Panel</div><div class="kh-val green">{format_currency(r['cpl_p'])}</div></div><div class="kh-item"><div class="kh-lbl">CPL LMS</div><div class="kh-val green">{format_currency(r['cpl_l'])}</div></div><div class="kh-item"><div class="kh-lbl">FFH</div><div class="kh-val purple">{format_num(stats['FFH'])}</div></div><div class="kh-item"><div class="kh-lbl">ADM</div><div class="kh-val purple">{format_num(stats['Adm'])}</div></div></div><div class="kpi-band"><div class="kpi-band-title">{label} \u2014 {timeframe} ({date})</div><div class="kpi-scroll"><div class="kc ac-blue"><div class="kc-lbl">Total Spend</div><div class="kc-val">{format_currency(stats['Spends'])}</div><div class="kc-sub">{label}</div></div><div class="kc ac-blue"><div class="kc-lbl">Panel Leads</div><div class="kc-val">{format_num(stats['Pannel_Lead'])}</div><div class="kc-sub">CPL {format_currency(r['cpl_p'])}</div></div><div class="kc ac-cyan"><div class="kc-lbl">LMS Leads</div><div class="kc-val">{format_num(stats['Lead_LMS'])}</div><div class="kc-sub">CPL {format_currency(r['cpl_l'])}</div></div><div class="kc ac-green"><div class="kc-lbl">FFH</div><div class="kc-val">{format_num(stats['FFH'])}</div><div class="kc-sub">CAC {format_currency(r['cac_f'])}</div></div><div class="kc ac-green"><div class="kc-lbl">ADM</div><div class="kc-val">{format_num(stats['Adm'])}</div><div class="kc-sub">CAC {format_currency(r['cac_a'])}</div></div><div class="kc ac-purple"><div class="kc-lbl">L2F Rate</div><div class="kc-val">{format_pct(r['l2f'])}</div><div class="kc-sub">Lead &#8594; FFH</div></div><div class="kc ac-purple"><div class="kc-lbl">L2A Rate</div><div class="kc-val">{format_pct(r['l2a'])}</div><div class="kc-sub">Lead &#8594; ADM</div></div><div class="kc ac-amber"><div class="kc-lbl">F2A Rate</div><div class="kc-val">{format_pct(r['f2a'])}</div><div class="kc-sub">FFH &#8594; ADM</div></div><div class="kc ac-orange"><div class="kc-lbl">Inv Variance</div><div class="kc-val">{format_currency(stats['Invoicing_Var'])}</div><div class="kc-sub">Revenue proxy</div></div></div></div>"""

# --- GRAPHS ---
def create_line_pair(g1_v, g2_v, plat):
    if not g1_v or len(g1_v)<2: return "",""
    d1, d2 = pd.DataFrame(g1_v[1:], columns=[c.strip() for c in g1_v[0]]), pd.DataFrame(g2_v[1:], columns=[c.strip() for c in g2_v[0]])
    x1, x2 = d1.columns[0], d2.columns[0]
    def fc(df, p):
        for c in df.columns:
            if p.upper() in str(c).upper().replace(' ','').replace('_',''): return c
        return None
    sp, lp, ll = fc(d1, 'SPEND'), fc(d1, 'PANNEL'), fc(d2, 'LMS')
    m = pd.merge(d1[[x1, sp, lp]], d2[[x2, ll]], left_on=x1, right_on=x2)
    for c in [sp, lp, ll]: m[c] = m[c].apply(pnum)
    m['CPL_P'], m['CPL_L'] = m[sp]/m[lp], m[sp]/m[ll]; m.replace([np.inf, -np.inf], 0, inplace=True); m.fillna(0, inplace=True)
    m['Date_P'] = pd.to_datetime(m[x1], errors='coerce'); m = m.sort_values('Date_P').dropna(subset=['Date_P'])
    m['X'] = m['Date_P'].dt.strftime('%b %d')
    def chart(y1, y2, l1, l2, t, is_cpl):
        plt.rcParams.update({"axes.facecolor":"#ffffff","figure.facecolor":"#ffffff","text.color":"#0f172a","font.family":"sans-serif"})
        fig, ax = plt.subplots(figsize=(12, 5), dpi=150)
        ax.plot(m['X'], m[y1], marker='o', color='#059669' if not is_cpl else '#d97706', label=l1, linewidth=2.5, markersize=6)
        ax.plot(m['X'], m[y2], marker='s', color='#7c3aed' if not is_cpl else '#dc2626', label=l2, linewidth=2.5, markersize=6)
        for i,v in enumerate(m[y1]): ax.text(i,v,(f"₹{v:,.0f}" if is_cpl else f"{v:,.0f}"),ha='center',va='bottom',fontweight='bold',fontsize=9,bbox=dict(facecolor='white',alpha=0.6,edgecolor='none',pad=1))
        for i,v in enumerate(m[y2]): ax.text(i,v,(f"₹{v:,.0f}" if is_cpl else f"{v:,.0f}"),ha='center',va='top',fontweight='bold',fontsize=9,bbox=dict(facecolor='white',alpha=0.6,edgecolor='none',pad=1))
        ax.set_title(t, pad=20, fontweight='bold', fontsize=14); ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=2, frameon=False); fig.tight_layout(); buf = io.BytesIO(); fig.savefig(buf, format="png"); plt.close(fig)
        return base64.b64encode(buf.getvalue()).decode('utf-8')
    return chart(lp, ll, 'Panel', 'LMS', f'Degreefyd Online Google ads {plat} campaign lead pannel and lead lms', False), chart('CPL_P', 'CPL_L', 'Panel', 'LMS', f'Degreefyd Online Google ads {plat} campaign cpl pannel and cpl lms', True)

# --- ASSEMBLE ---
print("Building final dashboard...")
with open('clean_css.txt', 'r') as f: clean_css = f.read()
with open('clean_js.txt', 'r') as f: clean_js = f.read()
with open('clean_p5_html.txt', 'r') as f: p5_raw = f.read()
p5_html = p5_raw.split("/* ── Toolbar ── */")[1]
p5_html = "<!-- Toolbar -->" + p5_html

f_in, f_cs, f_ht = build_h_table(ftd_h, "ftd"); m_in, m_cs, m_ht = build_h_table(mtd_h, "mtd"); y_in, y_cs, y_ht = build_h_table(ytd_h, "ytd")

l7 = today - timedelta(days=7); r_df = df[(df['Date_Parsed'] >= l7) & (df['Date_Parsed'] < today)]
avg_c = (r_df['Spends'].sum() / r_df['Lead_LMS'].sum()) if r_df['Lead_LMS'].sum() > 0 else 0
tod_s = {c: df[df['Date_Parsed'] == today][c].sum() for c in ['Spends', 'Pannel_Lead', 'Lead_LMS', 'FFH', 'Adm', 'Invoicing_Var']}
tod_c = (tod_s['Spends'] / tod_s['Lead_LMS']) if tod_s['Lead_LMS'] > 0 else 0
c_chg = ((tod_c - avg_c) / avg_c * 100) if avg_c > 0 else 0
best = df[df['Date_Parsed'] == today].sort_values('Adm', ascending=False).iloc[0] if not df[df['Date_Parsed'] == today].empty else {'Campaign': 'N/A', 'Adm': 0}
intel = f"""<div class="intel-card"><h3>AI Intelligence & Insights</h3><div class="intel-grid"><div class="intel-item"><span class="intel-label">CPL Trend (Today vs 7D Avg)</span><span class="intel-value" style="color:{'#dc2626' if c_chg > 10 else '#059669'};">{format_pct(abs(c_chg))} {'increased' if c_chg > 0 else 'decreased'}</span></div><div class="intel-item"><span class="intel-label">Daily Lead Flow</span><span class="intel-value">{format_num(tod_s['Lead_LMS'])} LMS Leads</span></div><div class="intel-item"><span class="intel-label">Top Performer</span><span class="intel-value">{best['Campaign']} ({format_num(best['Adm'])} Adms)</span></div></div></div>"""

ms = datetime(today.year, today.month, 1); ys = datetime(today.year, 1, 1)
m_s = {c: df[df['Date_Parsed'] >= ms][c].sum() for c in ['Spends', 'Pannel_Lead', 'Lead_LMS', 'FFH', 'Adm', 'Invoicing_Var']}
y_s = {c: df[df['Date_Parsed'] >= ys][c].sum() for c in ['Spends', 'Pannel_Lead', 'Lead_LMS', 'FFH', 'Adm', 'Invoicing_Var']}

p1 = f"""{intel}<h3 class="sec-title">DETAILED DRILLDOWN (FTD)</h3>{build_kpi('FTD', today.strftime('%d %b'), tod_s, 'For The Day')}{f_ht}<h3 class="sec-title">Overall CAC (FTD)</h3>{build_ov_cac(today, today)}<h3 class="sec-title">DETAILED DRILLDOWN (MTD)</h3>{build_kpi('MTD', today.strftime('%b %Y'), m_s, 'Month to Date')}{m_ht}<h3 class="sec-title">Overall CAC (MTD)</h3>{build_ov_cac(ms, today)}<h3 class="sec-title">DETAILED DRILLDOWN (YTD)</h3>{build_kpi('YTD', today.strftime('%Y'), y_s, 'Year to Date')}{y_ht}<h3 class="sec-title">Overall CAC (YTD)</h3>{build_ov_cac(ys, today)}"""

dl, dc = create_line_pair(dsa_g1, dsa_g2, 'DSA'); bl, bc = create_line_pair(brand_g1, brand_g2, 'Brand'); ml, mc = create_line_pair(meta_g1, meta_g2, 'META ADS')
def wg(l, c): return f'<div class="graph-card"><h4 class="graph-title">Leads Trend</h4><img src="data:image/png;base64,{l}" class="responsive-img"><h4 class="graph-title">CPL Trend</h4><img src="data:image/png;base64,{c}" class="responsive-img"></div>'

p5_toolbar = """
<div class="gb-desk">
<div class="gb-bar">
  <div class="gb-grp">
    <em>Period</em>
    <div class="gb-seg">
      <button class="gbtn on" data-gb="period" data-val="0" title="For The Day">FTD</button>
      <button class="gbtn" data-gb="period" data-val="1" title="Month to Date">MTD</button>
      <button class="gbtn" data-gb="period" data-val="2" title="Year to Date">YTD</button>
    </div>
  </div>
  <div class="gb-grp" id="gb-cmp-grp">
    <em>\u21c4 vs Period</em>
    <div class="gb-seg">
      <button class="gbtn on" data-gb="cmp" data-val="" title="No comparison \u2014 single period">Off</button>
      <button class="gbtn" data-gb="cmp" data-val="0" title="Compare current period vs FTD">FTD</button>
      <button class="gbtn" data-gb="cmp" data-val="1" title="Compare current period vs MTD">MTD</button>
      <button class="gbtn" data-gb="cmp" data-val="2" title="Compare current period vs YTD">YTD</button>
    </div>
  </div>
  <div class="gb-grp">
    <em>Compare By</em>
    <div class="gb-seg">
      <button class="gbtn on" data-gb="compare" data-val="platform" title="Compare ad platforms (Google vs Meta)">Platforms</button>
      <button class="gbtn" data-gb="compare" data-val="account" title="Compare ad accounts">Accounts</button>
      <button class="gbtn" data-gb="compare" data-val="campaign" title="Compare individual campaigns">Campaigns</button>
    </div>
  </div>
  <div class="gb-grp">
    <em>Metric</em>
    <select id="gbmet" class="gb-sel" title="Select the metric to visualise">
      <option value="1">Ad Spend (\u20b9)</option>
      <option value="2">Panel Leads</option>
      <option value="3">LMS Leads</option>
      <option value="4">Dup %</option>
      <option value="5">FFH</option>
      <option value="6">ADM</option>
      <option value="7">Inv Var (\u20b9)</option>
      <option value="8">CPL Panel (\u20b9)</option>
      <option value="9">CPL LMS (\u20b9)</option>
      <option value="10">CAC FFH (\u20b9)</option>
      <option value="11">CAC ADM (\u20b9)</option>
      <option value="12">ARPU (\u20b9)</option>
      <option value="13">CAC / ARPU</option>
      <option value="14">L2F %</option>
      <option value="15">L2A %</option>
      <option value="16">F2A %</option>
    </select>
  </div>
  <div class="gb-grp">
    <em>Chart Type</em>
    <div class="gb-seg">
      <button class="gbtn on" data-gb="chart" data-val="vbar">Bar</button>
      <button class="gbtn" data-gb="chart" data-val="hbar">H-Bar</button>
      <button class="gbtn" data-gb="chart" data-val="pie">Pie</button>
      <button class="gbtn" data-gb="chart" data-val="donut">Donut</button>
    </div>
  </div>
  <div class="gb-grp" id="gb-topn-grp">
    <em>Top N</em>
    <select id="gbtopn" class="gb-sel" title="Show only top N items by value">
      <option value="0">All</option>
      <option value="10">Top 10</option>
      <option value="20" selected>Top 20</option>
      <option value="30">Top 30</option>
    </select>
  </div>
  <div class="gb-grp" style="margin-left:auto;">
    <em>&nbsp;</em>
    <div style="display:flex;gap:8px;align-items:center;">
      <button class="gb-go" onclick="gbRun()">\u25b6&nbsp; Build Chart</button>
      <button class="gb-save" onclick="gbDL()" title="Download chart as PNG">\u2193&nbsp;PNG</button>
      <button class="gb-copy" onclick="gbCopy()" title="Copy chart image to clipboard">\ud83d\udccb&nbsp;Copy</button>
    </div>
  </div>
</div>
<div class="gb-area" id="gbarea">
  <p class="gb-ph" id="gbph"><span>\ud83d\udcc2</span>Select options above and click <strong>Build Chart</strong></p>
  <canvas id="gbcv" style="display:none;"></canvas>
</div>
<div class="gb-st" id="gbst"></div>
</div>
<div class="gb-mob">
  <div style="font-size:44px;margin-bottom:14px;">\ud83d\udcc2</div>
  <div style="font-size:15px;font-weight:600;color:var(--txt);margin-bottom:6px;">Desktop Only Feature</div>
  <div>Graph Builder is available on desktop browsers only.</div>
</div>
"""

HTML = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=5,user-scalable=yes"><style>{clean_css}</style></head><body>{f_in}{m_in}{y_in}<style>{f_cs}{m_cs}{y_cs}</style><input type="radio" name="tabs" id="t1" checked><input type="radio" name="tabs" id="t2"><input type="radio" name="tabs" id="t3"><input type="radio" name="tabs" id="t4"><input type="radio" name="tabs" id="t5"><div class="wrap"><div class="hdr"><h1>Degreefyd Master Dashboard</h1><p>Intelligence • {today.strftime('%d %b %Y')}</p></div><div class="tabs"><label for="t1" class="lbl-t1">📊 SUMMARIES</label><label for="t2" class="lbl-t2">🔷 DSA</label><label for="t3" class="lbl-t3">🔶 BRAND</label><label for="t4" class="lbl-t4">🟣 META ADS</label><label for="t5" class="lbl-t5">📈 GRAPHS</label></div><div id="p1" class="panel">{p1}</div><div id="p2" class="panel">{wg(dl, dc)}</div><div id="p3" class="panel">{wg(bl, bc)}</div><div id="p4" class="panel">{wg(ml, mc)}</div><div id="p5" class="panel" style="padding:0;">{p5_toolbar}</div></div><script>{clean_js}</script></body></html>"""

with open(OUTPUT_PATH, "w", encoding="utf-8-sig", errors="replace") as f: f.write(HTML)

load_dotenv("/workspace/.env")
WHAPI_TOKEN, WHATSAPP_GROUP = os.getenv("WHAPI_TOKEN"), os.getenv("WHATSAPP_GROUP")
with open(OUTPUT_PATH, "rb") as f: b64 = base64.b64encode(f.read()).decode('utf-8')
payload = {"to": WHATSAPP_GROUP, "media": f"data:text/html;name=Degreefyd_Final_Master_White.html;base64,{b64}", "caption": "🏆 **EXECUTIVE DASHBOARD - CLEAN REBUILD**\n\n✅ **Zero Duplication:** Skeleton re-architected to prevent header cloning.\n✅ **Native Icons:** Fixed UTF-8 tab emojis for all platforms.\n✅ **Latest Data:** Performance updated with data from today.\n✅ **Tab 5 Active:** Fully interactive JS chart builder preserved."}
requests.post("https://gate.whapi.cloud/messages/document", headers={"accept": "application/json", "authorization": f"Bearer {WHAPI_TOKEN}", "content-type": "application/json"}, json=payload)
print("Done.")
