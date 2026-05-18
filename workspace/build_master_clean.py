import os
import json
import base64
import io
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from dotenv import load_dotenv
import warnings
import re

warnings.filterwarnings('ignore')

# --- CONFIG ---
OUTPUT_PATH = "/workspace/Degreefyd_Final_Master_White.html"

# --- THEME COLORS ---
BG_COLOR = "#ffffff"
TEXT_COLOR = "#0d1117"
TEXT2_COLOR = "#4b5563"
TEXT3_COLOR = "#9ca3af"
BORDER_COLOR = "#e4e8ef"

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

def process_hierarchy(raw_rows):
    if len(raw_rows) < 2: return {}
    hierarchy = {}
    current_platform = "Unknown"
    current_account = "Unknown"
    
    for r in raw_rows[1:]:
        if not r or len(r) < 4: continue
        if str(r[0]).strip() == "Grand Total": continue
        
        if str(r[0]).strip() and "Total" not in str(r[0]):
            current_platform = str(r[0]).strip()
        
        is_account_total = "Total" in str(r[1])
        is_platform_total = "Total" in str(r[0])
        
        if is_platform_total: continue
        
        if is_account_total:
            current_account = str(r[1]).replace("Total", "").strip()
            if current_platform not in hierarchy:
                hierarchy[current_platform] = {}
            hierarchy[current_platform][current_account] = {
                "stats": r,
                "campaigns": []
            }
        else:
            camp_name = str(r[2]).strip()
            if not camp_name: camp_name = "Generic/Unknown Campaign"
            if current_platform in hierarchy and current_account in hierarchy[current_platform]:
                hierarchy[current_platform][current_account]["campaigns"].append(r)
                
    return hierarchy

def extract_overall_total(raw_rows):
    for r in raw_rows:
        if str(r[0]).strip() == "Grand Total":
            return r
    return None

def build_summary_table(raw_rows):
    if not raw_rows or len(raw_rows) < 2: return ""
    
    rows = []
    overall_metrics = {'dup':[], 'cpl_p':[], 'cpl_l':[], 'cac_f':[], 'cac_a':[], 'l2f':[], 'l2a':[], 'f2a':[]}
    
    grand_total = None
    for r in raw_rows[1:]:
        if len(r) < 4: continue
        if str(r[0]).strip() == "Grand Total":
            grand_total = r
            continue
            
        if "Total" in str(r[0]):
            plat_name = str(r[0]).replace("Total", "").strip()
            if not plat_name: continue
            
            sp = pnum(r[3]) if len(r)>3 else 0
            if sp > 0:
                lp = pnum(r[4]) if len(r)>4 else 0
                ll = pnum(r[5]) if len(r)>5 else 0
                dup = ((lp - ll) / lp * 100) if lp > 0 else 0
                cpl_p = pnum(r[9]) if len(r)>9 else 0
                cpl_l = pnum(r[10]) if len(r)>10 else 0
                cac_f = pnum(r[11]) if len(r)>11 else 0
                cac_a = pnum(r[12]) if len(r)>12 else 0
                l2f = pnum(r[15]) if len(r)>15 else 0
                l2a = pnum(r[16]) if len(r)>16 else 0
                f2a = pnum(r[17]) if len(r)>17 else 0
                
                overall_metrics['dup'].append(dup)
                overall_metrics['cpl_p'].append(cpl_p)
                overall_metrics['cpl_l'].append(cpl_l)
                overall_metrics['cac_f'].append(cac_f)
                overall_metrics['cac_a'].append(cac_a)
                overall_metrics['l2f'].append(l2f)
                overall_metrics['l2a'].append(l2a)
                overall_metrics['f2a'].append(f2a)
                
            rows.append((plat_name, r))
            
    html = '<div class="table-wrap"><table class="overall-table"><thead><tr><th class="text-left sticky-col">Platform</th><th class="num">Spends</th><th class="num">Pannel_Leads</th><th class="num">Leads_LMS</th><th class="num">Dup %</th><th class="num">FFH</th><th class="num">ADM</th><th class="num">Inv_Var</th><th class="num">CPL_Pannel</th><th class="num">CPL_LMS</th><th class="num">CAC_FFH</th><th class="num">CAC_Adm</th><th class="num">ARPU</th><th class="num">CAC/ARPU</th><th class="num">L2F</th><th class="num">L2A</th><th class="num">F2A</th></tr></thead><tbody>'
    
    def r_tr(label, r, custom_bg=None, is_total=False):
        style = f' style="background:{custom_bg}; font-weight:bold;"' if custom_bg else ' style="background:#ffffff; font-weight:bold;"'
        
        lp = pnum(r[4]) if len(r)>4 else 0
        ll = pnum(r[5]) if len(r)>5 else 0
        dup = ((lp - ll) / lp * 100) if lp > 0 else 0
        
        def gcs(metric, val):
            if is_total: return ""
            return f' style="{get_color_style(metric, val, overall_metrics.get(metric))}"'
            
        def v(idx): return r[idx] if len(r) > idx else "-"
        
        cpl_p = pnum(v(9)); cpl_l = pnum(v(10)); cac_f = pnum(v(11)); cac_a = pnum(v(12))
        l2f = pnum(v(15)); l2a = pnum(v(16)); f2a = pnum(v(17))

        return f"""<tr{style}>
            <td class="text-left sticky-col"{style}><strong>{label}</strong></td>
            <td class="num">{format_currency_full(pnum(v(3)))}</td><td class="num">{format_num(pnum(v(4)))}</td><td class="num">{format_num(pnum(v(5)))}</td>
            <td class="num"{gcs('dup', dup)}>{format_pct(dup)}</td><td class="num">{format_num(pnum(v(6)))}</td><td class="num">{format_num(pnum(v(7)))}</td>
            <td class="num">{format_currency_full(pnum(v(8)))}</td><td class="num"{gcs('cpl_p', cpl_p)}>{format_currency_full(cpl_p)}</td>
            <td class="num"{gcs('cpl_l', cpl_l)}>{format_currency_full(cpl_l)}</td><td class="num"{gcs('cac_f', cac_f)}>{format_currency_full(cac_f)}</td>
            <td class="num"{gcs('cac_a', cac_a)}>{format_currency_full(cac_a)}</td><td class="num">{format_currency_full(pnum(v(13)))}</td><td class="num">{v(14)}</td>
            <td class="num"{gcs('l2f', l2f)}>{format_pct(l2f)}</td><td class="num"{gcs('l2a', l2a)}>{format_pct(l2a)}</td><td class="num"{gcs('f2a', f2a)}>{format_pct(f2a)}</td>
        </tr>"""

    for label, r in rows: html += r_tr(label, r)
    if grand_total: html += r_tr("OVERALL TOTAL", grand_total, custom_bg="#f8fafc", is_total=True)
    return html + '</tbody></table></div>'

def build_kpi(label, date, r, timeframe):
    def v(idx): return r[idx] if len(r) > idx else "-"
    return f"""<div class="kpi-band" style="margin-top:10px;">
    <div class="kpi-band-title">{label} \u2014 {timeframe} ({date})</div>
    <div class="kpi-scroll">
        <div class="kc ac-blue"><div class="kc-lbl">Total Spend</div><div class="kc-val">{format_currency(pnum(v(3)))}</div><div class="kc-sub">{label}</div></div>
        <div class="kc ac-blue"><div class="kc-lbl">Panel Leads</div><div class="kc-val">{format_num(pnum(v(4)))}</div><div class="kc-sub">CPL {format_currency_full(pnum(v(9)))}</div></div>
        <div class="kc ac-cyan"><div class="kc-lbl">LMS Leads</div><div class="kc-val">{format_num(pnum(v(5)))}</div><div class="kc-sub">CPL {format_currency_full(pnum(v(10)))}</div></div>
        <div class="kc ac-green"><div class="kc-lbl">FFH</div><div class="kc-val">{format_num(pnum(v(6)))}</div><div class="kc-sub">CAC {format_currency_full(pnum(v(11)))}</div></div>
        <div class="kc ac-green"><div class="kc-lbl">ADM</div><div class="kc-val">{format_num(pnum(v(7)))}</div><div class="kc-sub">CAC {format_currency_full(pnum(v(12)))}</div></div>
        <div class="kc ac-purple"><div class="kc-lbl">L2F Rate</div><div class="kc-val">{format_pct(pnum(v(15)))}</div><div class="kc-sub">Lead &#8594; FFH</div></div>
        <div class="kc ac-purple"><div class="kc-lbl">L2A Rate</div><div class="kc-val">{format_pct(pnum(v(16)))}</div><div class="kc-sub">Lead &#8594; ADM</div></div>
        <div class="kc ac-amber"><div class="kc-lbl">F2A Rate</div><div class="kc-val">{format_pct(pnum(v(17)))}</div><div class="kc-sub">FFH &#8594; ADM</div></div>
        <div class="kc ac-orange"><div class="kc-lbl">Inv Variance</div><div class="kc-val">{format_currency(pnum(v(8)))}</div><div class="kc-sub">Revenue proxy</div></div>
    </div>
</div>"""

def build_h_table(h, pref):
    ins, css, idx = "", "", 0
    html = '<div class="table-wrap" style="margin-top:20px;"><table><thead><tr><th class="text-left sticky-col">Account / Campaign</th><th class="num">Spends</th><th class="num">Pannel_Leads</th><th class="num">Leads_LMS</th><th class="num">Dup %</th><th class="num">FFH</th><th class="num">ADM</th><th class="num">Inv_Var</th><th class="num">CPL_Pannel</th><th class="num">CPL_LMS</th><th class="num">CAC_FFH</th><th class="num">CAC_Adm</th><th class="num">ARPU</th><th class="num">CAC/ARPU</th><th class="num">L2F</th><th class="num">L2A</th><th class="num">F2A</th></tr></thead>'
    for plat, accs in h.items():
        pi = "🔵" if "Google" in plat else "🟣" if "Meta" in plat else "⚪"
        for acct, data in accs.items():
            idx += 1; cid = f"cb-{pref}-{idx}"
            s = data["stats"]
            def v(i): return s[i] if len(s) > i else "-"
            lp = pnum(v(4)); ll = pnum(v(5))
            dup = ((lp - ll) / lp * 100) if lp > 0 else 0
            
            ins += f'<input type="checkbox" id="{cid}" class="h-cb" tabindex="-1">\n'
            css += f"#{cid}:checked ~ .wrap #body-{cid} {{ display: table-row-group; }}\n#{cid}:checked ~ .wrap label[for='{cid}'] .chev {{ transform: rotate(90deg); }}\n"
            
            html += f"""<tbody><tr class="account-row">
                <td class="text-left sticky-col"><label for="{cid}" class="exp-lbl"><span class="chev">\u25b6</span> {pi} <strong>{acct}</strong></label></td>
                <td class="num">{format_currency_full(pnum(v(3)))}</td><td class="num">{format_num(pnum(v(4)))}</td><td class="num">{format_num(pnum(v(5)))}</td>
                <td class="num">{format_pct(dup)}</td><td class="num">{format_num(pnum(v(6)))}</td><td class="num">{format_num(pnum(v(7)))}</td>
                <td class="num">{format_currency_full(pnum(v(8)))}</td><td class="num">{format_currency_full(pnum(v(9)))}</td><td class="num">{format_currency_full(pnum(v(10)))}</td>
                <td class="num">{format_currency_full(pnum(v(11)))}</td><td class="num">{format_currency_full(pnum(v(12)))}</td><td class="num">{format_currency_full(pnum(v(13)))}</td>
                <td class="num">{v(14)}</td><td class="num">{format_pct(pnum(v(15)))}</td><td class="num">{format_pct(pnum(v(16)))}</td><td class="num">{format_pct(pnum(v(17)))}</td>
            </tr></tbody><tbody class="camp-body" id="body-{cid}">"""
            
            for c in data['campaigns']:
                def cv(i): return c[i] if len(c) > i else "-"
                clp = pnum(cv(4)); cll = pnum(cv(5))
                cdup = ((clp - cll) / clp * 100) if clp > 0 else 0
                html += f"""<tr class="camp-row"><td class="text-left sticky-col"><span style="padding-left:25px;">\u21b3 {cv(2)}</span></td>
                    <td class="num">{format_currency_full(pnum(cv(3)))}</td><td class="num">{format_num(pnum(cv(4)))}</td><td class="num">{format_num(pnum(cv(5)))}</td>
                    <td class="num">{format_pct(cdup)}</td><td class="num">{format_num(pnum(cv(6)))}</td><td class="num">{format_num(pnum(cv(7)))}</td>
                    <td class="num">{format_currency_full(pnum(cv(8)))}</td><td class="num">{format_currency_full(pnum(cv(9)))}</td><td class="num">{format_currency_full(pnum(cv(10)))}</td>
                    <td class="num">{format_currency_full(pnum(cv(11)))}</td><td class="num">{format_currency_full(pnum(cv(12)))}</td><td class="num">{format_currency_full(pnum(cv(13)))}</td>
                    <td class="num">{cv(14)}</td><td class="num">{format_pct(pnum(cv(15)))}</td><td class="num">{format_pct(pnum(cv(16)))}</td><td class="num">{format_pct(pnum(cv(17)))}</td>
                </tr>"""
            html += '</tbody>'
    return ins, css, html + '</table></div>'

def create_line_pair(g_file, plat):
    with open(g_file, 'r') as f: data = json.load(f)
    if not data or len(data) < 2: return "",""
    d1 = pd.DataFrame(data[1:], columns=[str(c).strip() for c in data[0]])
    with open(g_file.replace('g1', 'g2'), 'r') as f: data2 = json.load(f)
    d2 = pd.DataFrame(data2[1:], columns=[str(c).strip() for c in data2[0]])
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

print("Fetching data from JSON extracts...")
with open('ytd_sheet.json', 'r') as f: ytd_raw = json.load(f)
with open('mtd_sheet.json', 'r') as f: mtd_raw = json.load(f)
with open('ftd_sheet.json', 'r') as f: ftd_raw = json.load(f)

today = datetime.now()

ytd_h = process_hierarchy(ytd_raw)
mtd_h = process_hierarchy(mtd_raw)
ftd_h = process_hierarchy(ftd_raw)

f_in, f_cs, f_ht = build_h_table(ftd_h, "ftd")
m_in, m_cs, m_ht = build_h_table(mtd_h, "mtd")
y_in, y_cs, y_ht = build_h_table(ytd_h, "ytd")

ov_f = build_summary_table(ftd_raw)
ov_m = build_summary_table(mtd_raw)
ov_y = build_summary_table(ytd_raw)

f_gt = extract_overall_total(ftd_raw)
m_gt = extract_overall_total(mtd_raw)
y_gt = extract_overall_total(ytd_raw)

f_kpi = build_kpi('FTD', today.strftime('%d %b'), f_gt, 'For The Day') if f_gt else ""
m_kpi = build_kpi('MTD', today.strftime('%b %Y'), m_gt, 'Month to Date') if m_gt else ""
y_kpi = build_kpi('YTD', today.strftime('%Y'), y_gt, 'Year to Date') if y_gt else ""

p1 = f"""
<h3 class="sec-title">Overall Summary (FTD)</h3>
{f_kpi}
{ov_f}

<h3 class="sec-title">Overall Summary (MTD)</h3>
{m_kpi}
{ov_m}

<h3 class="sec-title">Overall Summary (YTD)</h3>
{y_kpi}
{ov_y}

<h3 class="sec-title" style="margin-top: 40px;">DETAILED DRILLDOWN (FTD)</h3>
{f_ht}

<h3 class="sec-title">DETAILED DRILLDOWN (MTD)</h3>
{m_ht}

<h3 class="sec-title">DETAILED DRILLDOWN (YTD)</h3>
{y_ht}
"""

dl, dc = create_line_pair('latest_dsa_g1.json', 'DSA')
bl, bc = create_line_pair('latest_brand_g1.json', 'Brand')
ml, mc = create_line_pair('latest_meta_g1.json', 'META ADS')
def wg(l, c): return f'<div class="graph-card"><h4 class="graph-title">Leads Trend</h4><img src="data:image/png;base64,{l}" class="responsive-img"><h4 class="graph-title">CPL Trend</h4><img src="data:image/png;base64,{c}" class="responsive-img"></div>'

with open('clean_css.txt', 'r') as f: clean_css = f.read()
with open('clean_js.txt', 'r') as f: clean_js = f.read()
with open('clean_p5_html.txt', 'r') as f: p5_raw = f.read()
p5_html = p5_raw.split("/* ── Toolbar ── */")[1]
p5_html = "<!-- Toolbar -->" + p5_html

HTML = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=5,user-scalable=yes"><style>{clean_css}</style><style>
.kpi-band{{margin-bottom:20px;}}
.kpi-band-title{{font-size:12px;font-weight:800;letter-spacing:1px;text-transform:uppercase;color:#475569;margin-bottom:10px;}}
.kpi-scroll{{display:flex;gap:10px;overflow-x:auto;scrollbar-width:none;padding-bottom:10px;}}
.kpi-scroll::-webkit-scrollbar{{display:none;}}
.kc{{flex-shrink:0;background:#ffffff;border:1px solid #e4e8ef;border-radius:12px;padding:13px 14px 11px;min-width:110px;box-shadow:0 1px 3px rgba(0,0,0,0.08);position:relative;overflow:hidden;}}
.kc::before{{content:'';position:absolute;top:0;left:0;right:0;height:4px;background:var(--kc-ac,#2563eb);}}
.kc.ac-blue{{--kc-ac:#2563eb;}}
.kc.ac-green{{--kc-ac:#059669;}}
.kc.ac-purple{{--kc-ac:#7c3aed;}}
.kc.ac-amber{{--kc-ac:#d97706;}}
.kc.ac-cyan{{--kc-ac:#0284c7;}}
.kc.ac-orange{{--kc-ac:#ea580c;}}
.kc-lbl{{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;color:#64748b;margin-bottom:7px;}}
.kc-val{{font-size:22px;font-weight:900;color:var(--kc-ac,#2563eb);font-family:'JetBrains Mono',monospace;letter-spacing:-.5px;line-height:1;}}
.kc-sub{{font-size:10px;color:#9ca3af;margin-top:5px;font-weight:600;}}
.camp-row td{{background:#ffffff !important;color:#475569;font-weight:600;border-bottom:1px dashed #cbd5e1;}}
.sec-title{{font-size:20px;font-weight:800;margin:35px 0 20px 0;color:#1e293b;padding-bottom:12px;border-bottom:3px solid #2563eb;display:inline-block;}}
</style></head><body>{f_in}{m_in}{y_in}<style>{f_cs}{m_cs}{y_cs}</style><input type="radio" name="tabs" id="t1" checked><input type="radio" name="tabs" id="t2"><input type="radio" name="tabs" id="t3"><input type="radio" name="tabs" id="t4"><input type="radio" name="tabs" id="t5"><div class="wrap"><div class="hdr"><h1>Degreefyd Master Dashboard</h1><p>Intelligence • {today.strftime('%d %b %Y')}</p></div><div class="tabs"><label for="t1" class="lbl-t1">📊 SUMMARIES</label><label for="t2" class="lbl-t2">🔷 DSA</label><label for="t3" class="lbl-t3">🔶 BRAND</label><label for="t4" class="lbl-t4">🟣 META ADS</label><label for="t5" class="lbl-t5">📈 GRAPHS</label></div><div id="p1" class="panel">{p1}</div><div id="p2" class="panel">{wg(dl, dc)}</div><div id="p3" class="panel">{wg(bl, bc)}</div><div id="p4" class="panel">{wg(ml, mc)}</div><div id="p5" class="panel" style="padding:0;">{p5_html}<script>{clean_js}</script></div></div></body></html>"""

with open(OUTPUT_PATH, "w", encoding="utf-8-sig", errors="replace") as f: f.write(HTML)

load_dotenv("/workspace/.env")
WHAPI_TOKEN, WHATSAPP_GROUP = os.getenv("WHAPI_TOKEN"), os.getenv("WHATSAPP_GROUP")
with open(OUTPUT_PATH, "rb") as f: b64 = base64.b64encode(f.read()).decode('utf-8')
payload = {"to": WHATSAPP_GROUP, "media": f"data:text/html;name=Degreefyd_Final_Master_White.html;base64,{b64}", "caption": "🏆 **EXECUTIVE DASHBOARD - TRUE DATA FIX**\n\n✅ **Accurate Totals:** Now pulling directly from the 'Campaign Wise' FTD/MTD/YTD sheets to match the true Grand Total (e.g. 362 ADM instead of 305).\n✅ **Layout Adjusted:** Overall summaries are now at the VERY TOP of the Summaries tab, followed by Detailed Drilldowns at the bottom.\n✅ **Clean UI:** Removed the 'AI Intelligence' block and the redundant gradient KPI hero.\n✅ **Everything Off by Default:** All drilldowns are collapsed initially so the view is perfectly clean on open.\n✅ **Graph Fixed:** Icons render natively without '??'."}
requests.post("https://gate.whapi.cloud/messages/document", headers={"accept": "application/json", "authorization": f"Bearer {WHAPI_TOKEN}", "content-type": "application/json"}, json=payload)
print("Done.")
