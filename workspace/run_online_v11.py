"""
Degreefyd Master Dashboard — v11 (ULTIMATE FIX)
==============================================
Improved Platform Attribution + Strict Same-Day FTD Logic.
"""

import os, sys, json, base64, io, subprocess, warnings, re
import requests
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime
from dotenv import load_dotenv

warnings.filterwarnings('ignore')

# ── CONFIG (TEMPLATE) ────────────────────────────────────────────────────────
# This script is a template. setup_v11.py overwrites SHEET_ID / OUTPUT_PATH / LABEL per run.
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
WORKSPACE   = "/workspace" if os.path.isdir("/workspace") else SCRIPT_DIR
SHEET_ID    = "1jzgnRxmmLIe_DAZ7nwHSRXeO6sI4CRxlTatc0T88ukY"
OUTPUT_PATH = os.path.join(WORKSPACE, "Degreefyd_Online_v11.html")
LABEL       = "ONLINE"
GAPI_SCRIPT = "/home/hermeswebui/.hermes/skills/productivity/google-workspace/scripts/google_api.py"
if not os.path.exists(GAPI_SCRIPT):
    GAPI_SCRIPT = "/home/mohit/.hermes/skills/productivity/google-workspace/scripts/google_api.py"
GAPI        = f"{sys.executable} {GAPI_SCRIPT}"
GRAPH_DAYS  = 10

# ── UTILS ────────────────────────────────────────────────────────────────────
def pnum(v):
    try:
        if isinstance(v, (int, float)): return float(v)
        s = str(v).replace(',', '').strip().replace('%','').replace('₹','')
        if s in ('-','','N/A','—','\u2014'): return 0.0
        return float(s)
    except: return 0.0

def fc(v):   return f"₹{v/100000:.1f}L" if abs(v) >= 100000 else f"₹{v:,.0f}"
def fcf(v):
    try: return f"₹{float(v):,.0f}"
    except: return "₹0"
def fp(v):   return f"{float(v):.1f}%"
def fn(v):
    try: return f"{int(float(v)):,}"
    except: return "0"

def gcs(metric, value, bucket):
    if not bucket or len(bucket) < 2: return ""
    ranks = sorted(set(bucket))
    if metric in ('cpl_p','cpl_l','cac_f','cac_a'):
        if value == ranks[0]:  return "background:rgba(16,185,129,.18);"
        if value == ranks[-1]: return "background:rgba(239,68,68,.18);"
    if metric in ('l2f','l2a','f2a'):
        if value == ranks[-1]: return "background:rgba(16,185,129,.18);"
        if value == ranks[0]:  return "background:rgba(239,68,68,.18);"
    return ""

# ── AGGREGATE ────────────────────────────────────────────────────────────────
def agg(df):
    if df.empty: return ["-"]*20
    s  = df['Spends'].sum()
    lp = df['Pannel_Lead'].sum()
    ll = df['Lead_LMS'].sum()
    ff = df['FFH'].sum()
    ad = df['Adm'].sum()
    iv = df['Invoicing_Var'].sum()
    dup = (lp - ll) / lp * 100 if lp > 0 else 0
    cp  = s / lp  if lp > 0 else 0
    cl  = s / ll  if ll > 0 else 0
    cf  = s / ff  if ff > 0 else 0
    ca  = s / ad  if ad > 0 else 0
    ar  = iv / ad if ad > 0 else 0
    cru = ca / ar if (ca > 0 and ar > 0) else 0
    l2f = ff / ll * 100 if ll > 0 else 0
    l2a = ad / ll * 100 if ll > 0 else 0
    f2a = ad / ff * 100 if ff > 0 else 0
    return ["Total","","", s, lp, ll, ff, ad, iv, cp, cl, cf, ca, ar, f"{cru:.2f}", l2f, l2a, f2a]

# ── SUMMARY TABLE ────────────────────────────────────────────────────────────
def build_summary(df_src):
    g_df  = df_src[df_src['Platform'].str.contains('Google', case=False, na=False)]
    m_df  = df_src[df_src['Platform'].str.contains('Meta',   case=False, na=False)]
    gs, ms, ov = agg(g_df), agg(m_df), agg(df_src)

    bkt = {}
    for s in [gs, ms]:
        lp, ll = pnum(s[4]), pnum(s[5])
        bkt.setdefault('dup',  []).append((lp-ll)/lp*100 if lp>0 else 0)
        for k, i in zip(('cpl_p','cpl_l','cac_f','cac_a','l2f','l2a','f2a'), (9,10,11,12,15,16,17)):
            bkt.setdefault(k, []).append(pnum(s[i]))

    TH = '<th class="num" style="font-weight:900!important;">'
    hdr = (f'<div class="table-wrap"><table class="overall-table"><thead><tr>'
           f'<th class="text-left sticky-col" style="font-weight:900!important;"><strong>Platform</th>'
           f'{TH}Spends</th>{TH}Panel Leads</th>{TH}LMS Leads</th>{TH}Dup%</th>'
           f'{TH}FFH</th>{TH}ADM</th>{TH}Inv_Var</th>'
           f'{TH}CPL Panel</th>{TH}CPL LMS</th>{TH}CAC FFH</th>{TH}CAC Adm</th>'
           f'{TH}ARPU</th>{TH}CAC/ARPU</th>{TH}L2F</th>{TH}L2A</th>{TH}F2A</th>'
           f'</tr></thead><tbody>')

    def row(lbl, r, bg=None, is_total=False):
        lp, ll = pnum(r[4]), pnum(r[5])
        dup = (lp-ll)/lp*100 if lp>0 else 0
        def cs(m, v): return f' style="{gcs(m,v,bkt.get(m))}"' if not is_total else ""
        sty = f' style="background:{bg};font-weight:bold;"' if bg else ' style="font-weight:bold;"'
        return (f'<tr{sty}>'
                f'<td class="text-left sticky-col"{sty}><strong>{lbl}</strong></td>'
                f'<td class="num">{fcf(pnum(r[3]))}</td>'
                f'<td class="num">{fn(lp)}</td><td class="num">{fn(ll)}</td>'
                f'<td class="num"{cs("dup",dup)}>{fp(dup)}</td>'
                f'<td class="num">{fn(pnum(r[6]))}</td><td class="num">{fn(pnum(r[7]))}</td>'
                f'<td class="num">{fcf(pnum(r[8]))}</td>'
                f'<td class="num"{cs("cpl_p",pnum(r[9]))}>{fcf(pnum(r[9]))}</td>'
                f'<td class="num"{cs("cpl_l",pnum(r[10]))}>{fcf(pnum(r[10]))}</td>'
                f'<td class="num"{cs("cac_f",pnum(r[11]))}>{fcf(pnum(r[11]))}</td>'
                f'<td class="num"{cs("cac_a",pnum(r[12]))}>{fcf(pnum(r[12]))}</td>'
                f'<td class="num">{fcf(pnum(r[13]))}</td>'
                f'<td class="num">{r[14]}</td>'
                f'<td class="num"{cs("l2f",pnum(r[15]))}>{fp(pnum(r[15]))}</td>'
                f'<td class="num"{cs("l2a",pnum(r[16]))}>{fp(pnum(r[16]))}</td>'
                f'<td class="num"{cs("f2a",pnum(r[17]))}>{fp(pnum(r[17]))}</td>'
                f'</tr>')

    body = row("Google Ads", gs) + row("Meta Ads", ms) + row("OVERALL TOTAL", ov, "#f8fafc", True)
    return hdr + body + '</tbody></table></div>', ov

# ── KPI CARDS ─────────────────────────────────────────────────────────────────
def build_kpi(lbl, date_str, r, sub):
    def card(cls, title, val, s): return f'<div class="kc {cls}"><div class="kc-lbl">{title}</div><div class="kc-val">{val}</div><div class="kc-sub">{s}</div></div>'
    sp, pl, ll = fc(pnum(r[3])), fn(pnum(r[4])), fn(pnum(r[5]))
    ff, ad, iv = fn(pnum(r[6])), fn(pnum(r[7])), fc(pnum(r[8]))
    cpl_p, cpl_l = fcf(pnum(r[9])), fcf(pnum(r[10]))
    cac_f, cac_a = fcf(pnum(r[11])), fcf(pnum(r[12]))
    l2f, l2a, f2a = fp(pnum(r[15])), fp(pnum(r[16])), fp(pnum(r[17]))
    return (f'<div class="kpi-band"><div class="kpi-band-title">{lbl} — {sub} ({date_str})</div>'
            f'<div class="kpi-scroll">'
            f'{card("ac-blue","Total Spend",sp,lbl)}'
            f'{card("ac-blue","Panel Leads",pl,f"CPL {cpl_p}")}'
            f'{card("ac-cyan","LMS Leads",ll,f"CPL {cpl_l}")}'
            f'{card("ac-green","FFH",ff,f"CAC {cac_f}")}'
            f'{card("ac-green","ADM",ad,f"CAC {cac_a}")}'
            f'{card("ac-purple","L2F",l2f,"Lead→FFH")}'
            f'{card("ac-purple","L2A",l2a,"Lead→ADM")}'
            f'{card("ac-amber","F2A",f2a,"FFH→ADM")}'
            f'{card("ac-orange","Inv Variance",iv,"Revenue proxy")}'
            f'</div></div>')

# ── DRILLDOWN TABLE ──────────────────────────────────────────────────────────
def build_drilldown(df_src, pref):
    ins = ""; css = ""; idx = 0
    TH = '<th class="num" style="font-weight:900!important;">'
    html = (f'<div class="table-wrap" style="margin-top:20px;"><table>'
            f'<thead><tr><th class="text-left sticky-col" style="font-weight:900!important;"><strong>Account / Campaign</th>'
            f'{TH}Spends</th>{TH}Panel Leads</th>{TH}LMS Leads</th>{TH}Dup%</th>'
            f'{TH}FFH</th>{TH}ADM</th>{TH}Inv_Var</th>'
            f'{TH}CPL Panel</th>{TH}CPL LMS</th>{TH}CAC FFH</th>{TH}CAC Adm</th>'
            f'{TH}ARPU</th>{TH}CAC/ARPU</th>{TH}L2F</th>{TH}L2A</th>{TH}F2A</th>'
            f'</tr></thead>')

    for plat in sorted(df_src['Platform'].dropna().unique()):
        icon = "🔵" if "Google" in plat else "🟣" if "Meta" in plat else "⚪"
        plat_df = df_src[df_src['Platform'] == plat]
        for acct in sorted(plat_df['Account'].dropna().unique()):
            idx += 1
            cid = f"cb-{pref}-{idx}"
            acct_df = plat_df[plat_df['Account'] == acct]
            s = agg(acct_df)
            ins += f'<input type="checkbox" id="{cid}" class="h-cb" tabindex="-1">\n'
            css += (f'#{cid}:checked ~ .wrap #body-{cid} {{ display:table-row-group !important; }}\n'
                    f'#{cid}:checked ~ .wrap label[for="{cid}"] .chev {{ transform:rotate(90deg); }}\n')
            lp, ll = pnum(s[4]), pnum(s[5]); dup = (lp-ll)/lp*100 if lp>0 else 0
            html += (f'<tbody><tr class="account-row">'
                     f'<td class="text-left sticky-col"><label for="{cid}" class="exp-lbl">'
                     f'<span class="chev">▶</span> {icon} <strong>{acct}</strong></label></td>'
                     f'<td class="num">{fcf(pnum(s[3]))}</td><td class="num">{fn(lp)}</td>'
                     f'<td class="num">{fn(ll)}</td><td class="num">{fp(dup)}</td>'
                     f'<td class="num">{fn(pnum(s[6]))}</td><td class="num">{fn(pnum(s[7]))}</td>'
                     f'<td class="num">{fcf(pnum(s[8]))}</td><td class="num">{fcf(pnum(s[9]))}</td>'
                     f'<td class="num">{fcf(pnum(s[10]))}</td><td class="num">{fcf(pnum(s[11]))}</td>'
                     f'<td class="num">{fcf(pnum(s[12]))}</td><td class="num">{fcf(pnum(s[13]))}</td>'
                     f'<td class="num">{s[14]}</td>'
                     f'<td class="num">{fp(pnum(s[15]))}</td><td class="num">{fp(pnum(s[16]))}</td>'
                     f'<td class="num">{fp(pnum(s[17]))}</td>'
                     f'</tr></tbody>'
                     f'<tbody class="camp-body" id="body-{cid}">')

            for ci, camp in enumerate(sorted(acct_df['Campaign'].dropna().unique())):
                iid = f"{cid}-c-{ci}"
                ins += f'<input type="checkbox" id="{iid}" class="h-cb" tabindex="-1">\n'
                css += (f'#{iid}:checked ~ .wrap .daily-{iid} {{ display:table-row !important; }}\n'
                        f'#{iid}:checked ~ .wrap label[for="{iid}"] .chev {{ transform:rotate(90deg); }}\n')
                c_df = acct_df[acct_df['Campaign'] == camp]
                cs = agg(c_df)
                clp, cll = pnum(cs[4]), pnum(cs[5]); cdup = (clp-cll)/clp*100 if clp>0 else 0
                html += (f'<tr class="camp-row">'
                         f'<td class="text-left sticky-col"><label for="{iid}" class="exp-lbl" style="padding-left:25px;">'
                         f'<span class="chev">▶</span> ↳ {camp}</label></td>'
                         f'<td class="num">{fcf(cs[3])}</td><td class="num">{fn(cs[4])}</td>'
                         f'<td class="num">{fn(cs[5])}</td><td class="num">{fp(cdup)}</td>'
                         f'<td class="num">{fn(cs[6])}</td><td class="num">{fn(cs[7])}</td>'
                         f'<td class="num">{fcf(cs[8])}</td><td class="num">{fcf(cs[9])}</td>'
                         f'<td class="num">{fcf(cs[10])}</td><td class="num">{fcf(cs[11])}</td>'
                         f'<td class="num">{fcf(cs[12])}</td><td class="num">{fcf(cs[13])}</td>'
                         f'<td class="num">{cs[14]}</td>'
                         f'<td class="num">{fp(cs[15])}</td><td class="num">{fp(cs[16])}</td>'
                         f'<td class="num">{fp(cs[17])}</td>'
                         f'</tr>'
                         f'<tr class="daily-hdr daily-{iid}">'
                         f'<th colspan="17" style="text-align:left;padding-left:50px;background:#f8fafc;">Daily Raw (Latest 5)</th></tr>')
                for _, d in c_df.sort_values('Date_Parsed', ascending=False).head(5).iterrows():
                    ds,dp,dl,df_v,da,di = d['Spends'],d['Pannel_Lead'],d['Lead_LMS'],d['FFH'],d['Adm'],d['Invoicing_Var']
                    dar = di/da if da>0 else 0; drup = (ds/da/dar*100) if da>0 and dar>0 else 0
                    ddp = (dp-dl)/dp*100 if dp>0 else 0
                    html += (f'<tr class="daily-row daily-{iid}">'
                             f'<td class="text-left sticky-col"><span style="padding-left:50px;font-size:11px;color:#64748b;">'
                             f'{d["Date"]} — {d["Ad Name"]}</span></td>'
                             f'<td class="num">{fcf(ds)}</td><td class="num">{fn(dp)}</td>'
                             f'<td class="num">{fn(dl)}</td><td class="num">{fp(ddp)}</td>'
                             f'<td class="num">{fn(df_v)}</td><td class="num">{fn(da)}</td>'
                             f'<td class="num">{fcf(di)}</td>'
                             f'<td class="num">{fcf(ds/dp if dp>0 else 0)}</td>'
                             f'<td class="num">{fcf(ds/dl if dl>0 else 0)}</td>'
                             f'<td class="num">{fcf(ds/df_v if df_v>0 else 0)}</td>'
                             f'<td class="num">{fcf(ds/da if da>0 else 0)}</td>'
                             f'<td class="num">{fcf(dar)}</td><td class="num">{fp(drup)}</td>'
                             f'<td class="num">{fp(df_v/dl*100 if dl>0 else 0)}</td>'
                             f'<td class="num">{fp(da/dl*100 if dl>0 else 0)}</td>'
                             f'<td class="num">{fp(da/df_v*100 if df_v>0 else 0)}</td>'
                             f'</tr>')
            html += '</tbody>'
    return ins, css, html + '</table></div>'

# ── TREND CHARTS (last N days) ────────────────────────────────────────────────
def make_charts(df_full, pattern, label, n_days=GRAPH_DAYS):
    try:
        # Search graph designators across every naming column. Regular has no literal
        # "Brand" tag, so Brand is derived as Google rows excluding Generic/DSA.
        search_cols = [c for c in ['Platform','Type','Account','Campaign','Ad Name'] if c in df_full.columns]
        masks = [df_full[c].astype(str).str.contains(pattern, case=False, na=False, regex=True) for c in search_cols]
        mask = masks[0]
        for m in masks[1:]: mask = mask | m
        sub = df_full[mask].copy()
        if sub.empty and str(pattern).lower() == 'brand' and LABEL == 'REGULAR':
            google = df_full['Platform'].astype(str).str.contains('Google', case=False, na=False)
            non_brand_terms = 'Generic|DSA'
            non_brand = pd.Series(False, index=df_full.index)
            for c in search_cols:
                non_brand = non_brand | df_full[c].astype(str).str.contains(non_brand_terms, case=False, na=False, regex=True)
            sub = df_full[google & (~non_brand)].copy()
        if sub.empty: return "", ""
        daily = (sub.groupby('Date_Parsed')
                    .agg(Spends=('Spends','sum'), PL=('Pannel_Lead','sum'), LL=('Lead_LMS','sum'))
                    .reset_index().sort_values('Date_Parsed'))
        daily = daily[(daily['PL']>0) | (daily['Spends']>0)].tail(n_days).reset_index(drop=True)
        if daily.empty: return "", ""
        daily['CPL_P'] = (daily['Spends'] / daily['PL']).replace([np.inf,-np.inf],0).fillna(0)
        daily['CPL_L'] = (daily['Spends'] / daily['LL']).replace([np.inf,-np.inf],0).fillna(0)
        daily['X'] = daily['Date_Parsed'].dt.strftime('%d %b')

        def one_chart(y1, y2, l1, l2, title, is_currency):
            plt.rcParams.update({"axes.facecolor":"#ffffff","figure.facecolor":"#ffffff",
                                  "text.color":"#0f172a","font.family":"sans-serif"})
            fig, ax = plt.subplots(figsize=(11, 4.5), dpi=150)
            c1 = '#059669' if not is_currency else '#d97706'
            c2 = '#7c3aed' if not is_currency else '#dc2626'
            ax.plot(daily['X'], daily[y1], marker='o', color=c1, label=l1, linewidth=2.2)
            ax.plot(daily['X'], daily[y2], marker='s', color=c2, label=l2, linewidth=2.2)
            y_max = max(daily[y1].max(), daily[y2].max())
            pad = y_max * 0.04 if y_max > 0 else 1
            for i, v in enumerate(daily[y1]):
                if v > 0:
                    lbl = f"₹{v:,.0f}" if is_currency else f"{v:,.0f}"
                    ax.text(i, v + pad, lbl, ha='center', va='bottom', fontsize=8, fontweight='bold', color=c1)
            for i, v in enumerate(daily[y2]):
                if v > 0:
                    lbl = f"₹{v:,.0f}" if is_currency else f"{v:,.0f}"
                    ax.text(i, v - pad, lbl, ha='center', va='top', fontsize=8, fontweight='bold', color=c2)
            ax.set_ylim(bottom=0, top=y_max * 1.25 if y_max > 0 else 10)
            ax.legend(loc='upper left', bbox_to_anchor=(0,1.15), ncol=2, frameon=False, fontsize=9)
            ax.grid(axis='y', linestyle='--', alpha=0.35)
            ax.set_title(f"{label} — {title} (Last {n_days} Days)", fontweight='bold', fontsize=11, pad=18)
            plt.xticks(rotation=45, ha='right', fontsize=9)
            fig.tight_layout()
            buf = io.BytesIO(); fig.savefig(buf, format='png'); plt.close(fig)
            return base64.b64encode(buf.getvalue()).decode('utf-8')

        leads_b64 = one_chart('PL',    'LL',    'Panel Leads', 'LMS Leads', 'Leads Trend',  False)
        cpl_b64   = one_chart('CPL_P', 'CPL_L', 'CPL Panel',  'CPL LMS',   'CPL Trend',    True)
        return leads_b64, cpl_b64
    except: return "", ""

def graph_wrap(l_b64, c_b64):
    if not l_b64: return '<div class="graph-card"><p style="padding:20px;color:#94a3b8;">No data available.</p></div>'
    return (f'<div class="graph-card">'
            f'<h4 class="graph-title">Leads Trend</h4>'
            f'<img src="data:image/png;base64,{l_b64}" class="responsive-img">'
            f'<h4 class="graph-title" style="margin-top:24px;">CPL Trend</h4>'
            f'<img src="data:image/png;base64,{c_b64}" class="responsive-img">'
            f'</div>')

# ── RUN ───────────────────────────────────────────────────────────────────────
print(f"[{LABEL}] Fetching CAC...")
r = subprocess.run(f"{GAPI} sheets get {SHEET_ID} \"'Day Wise CAC Report'!A1:S20000\"", shell=True, capture_output=True, text=True)
cac_raw = json.loads(r.stdout)
# Online sheet has merged headers in row 1 (duplicate "Campaign", lowercase "lead_LMS").
# Row 2 has proper sub-headers (Ad Name, Lead_LMS). Detect by checking col[5].
if len(cac_raw) > 2 and str(cac_raw[2][5]).strip() == 'Ad Name':
    columns = [str(c).strip() for c in cac_raw[2]]
    data_start = 3
else:
    columns = [str(c).strip() for c in cac_raw[1]]
    data_start = 2
df = pd.DataFrame(cac_raw[data_start:], columns=columns)
for c in ('Spends','Pannel_Lead','Lead_LMS'): df[c] = df[c].apply(pnum)
df['Date_Parsed'] = pd.to_datetime(df['Date'], errors='coerce')
df = df.dropna(subset=['Date_Parsed'])
df = df[df['Platform'].str.strip() != '']
today = df['Date_Parsed'].max()
print(f"  Anchor: {today.date()}")

df['FFH'] = 0.0; df['Adm'] = 0.0; df['Invoicing_Var'] = 0.0
df['pipeline_only'] = False; df['same_day_pipe'] = False  # FTD Adm/Inv allowed only for Form Date == Admission Date

print(f"[{LABEL}] Fetching CRM...")
r2 = subprocess.run(f"{GAPI} sheets get {SHEET_ID} \"'FFH & Above'!A1:Z5000\"", shell=True, capture_output=True, text=True)
crm_raw = json.loads(r2.stdout)
df_crm = pd.DataFrame(crm_raw[1:], columns=[str(c).strip() for c in crm_raw[0]])
df_crm.columns = [c.strip() for c in df_crm.columns]
df_crm['Inv_Val'] = df_crm['Invoicing Variable'].astype(str).str.replace(',','').apply(pnum)
df_crm['F_Date'] = pd.to_datetime(df_crm['Form Date'], format='%d/%b/%Y', errors='coerce')
df_crm['A_Date'] = pd.to_datetime(df_crm['Admission Date'], format='%d/%b/%Y', errors='coerce')
df_crm['Src'] = df_crm['Source Name'].astype(str).str.strip().str.lower()

# Campaign Lookup
camp_lookup = {}
for _, row in df.iterrows():
    for key in (str(row.get('Ad Name','')).strip(), str(row.get('Campaign','')).strip()):
        if key: camp_lookup[key] = {'Platform': row.get('Platform','Unknown'), 'Account': row.get('Account','Unknown'), 'Campaign': str(row.get('Campaign','')).strip(), 'Ad Name': str(row.get('Ad Name','')).strip()}

new_rows = []
def inject(date, camp, ffh, adm, inv, p_only=False, s_pipe=False):
    # If it's old-pipeline data, ALWAYS create a new row so it can be filtered out of FTD.
    # This prevents historical admissions from inflating current day's CAC metrics.
    if not p_only:
        mask_d = df['Date_Parsed'] == date
        mask_c = (df['Ad Name'].str.strip() == camp) | (df['Campaign'].str.strip() == camp)
        hits = df.index[mask_d & mask_c]
        if len(hits) > 0:
            idx = hits[0]
            df.at[idx, 'FFH'] += ffh; df.at[idx, 'Adm'] += adm; df.at[idx, 'Invoicing_Var'] += inv
            if s_pipe: df.at[idx, 'same_day_pipe'] = True
            return

    # If no hit found OR it is pipeline_only, append new row
    m = camp_lookup.get(camp)
    if m: plat, acct, cname, aname = m['Platform'], m['Account'], m['Campaign'], m['Ad Name']
    else:
        plat = 'Unknown'
        crm_matches = df_crm[df_crm['Campaign Name'].str.strip() == camp]
        if not crm_matches.empty:
            src = str(crm_matches.iloc[0]['Src'])
            if 'google' in src: plat = 'Google Ads'
            elif 'meta' in src or 'facebook' in src: plat = 'Meta Ads'
        acct, cname, aname = 'Unknown', camp, camp
    
    new_rows.append({'Platform': plat, 'Account': acct, 'Campaign': cname, 'Ad Name': aname, 'Date': date.strftime('%Y-%m-%d'), 'Date_Parsed': date, 'Spends': 0.0, 'Pannel_Lead': 0.0, 'Lead_LMS': 0.0, 'FFH': ffh, 'Adm': adm, 'Invoicing_Var': inv, 'pipeline_only': p_only, 'same_day_pipe': s_pipe})

# 1. FFH by Form Date
ffh_grp = df_crm.dropna(subset=['F_Date']).groupby(['F_Date','Campaign Name']).size().reset_index(name='count')
for _, r in ffh_grp.iterrows(): inject(r['F_Date'], r['Campaign Name'].strip(), float(r['count']), 0.0, 0.0)

# 2. Admissions + Invoicing Variable
# FTD admission and invoicing variable are counted only when Form Date == Admission Date == today.
# ONLINE: MTD/YTD Inv follows Admission Date.
# REGULAR: MTD/YTD Inv follows Form Date, because the Regular raw May view is Form-Date based.
same = df_crm[(df_crm['F_Date'].notna()) & (df_crm['A_Date'].notna()) & (df_crm['F_Date'] == df_crm['A_Date'])]
old = df_crm[(df_crm['A_Date'].notna()) & (df_crm['F_Date'] != df_crm['A_Date'])]

if LABEL == 'REGULAR':
    # Admissions are still counted by Admission Date, but old-pipeline admissions stay excluded from FTD.
    same_adm_grp = same.groupby(['F_Date','Campaign Name']).agg(A_Count=('A_Date','count')).reset_index()
    for _, r in same_adm_grp.iterrows():
        inject(r['F_Date'], r['Campaign Name'].strip(), 0.0, float(r['A_Count']), 0.0, s_pipe=True)
    old_adm_grp = old.groupby(['A_Date','Campaign Name']).agg(A_Count=('A_Date','count')).reset_index()
    for _, r in old_adm_grp.iterrows():
        inject(r['A_Date'], r['Campaign Name'].strip(), 0.0, float(r['A_Count']), 0.0, p_only=True)

    # Invoicing Variable is counted by Form Date for Regular MTD/YTD.
    inv_src = df_crm[(df_crm['F_Date'].notna()) & (df_crm['A_Date'].notna())]
    # Same_Day marks rows eligible for FTD; non-same-day inv rows are MTD/YTD only.
    inv_grp = inv_src.assign(Same_Day_Row=inv_src['F_Date'] == inv_src['A_Date']).groupby(['F_Date','Campaign Name']).agg(Inv_Sum=('Inv_Val','sum'), Same_Day=('Same_Day_Row','all')).reset_index()
    for _, r in inv_grp.iterrows():
        inject(r['F_Date'], r['Campaign Name'].strip(), 0.0, 0.0, float(r['Inv_Sum']), p_only=not bool(r['Same_Day']), s_pipe=bool(r['Same_Day']))
else:
    same_grp = same.groupby(['F_Date','Campaign Name']).agg(A_Count=('A_Date','count'), Inv_Sum=('Inv_Val','sum')).reset_index()
    for _, r in same_grp.iterrows(): inject(r['F_Date'], r['Campaign Name'].strip(), 0.0, float(r['A_Count']), float(r['Inv_Sum']), s_pipe=True)

    old_grp = old.groupby(['A_Date','Campaign Name']).agg(A_Count=('A_Date','count'), Inv_Sum=('Inv_Val','sum')).reset_index()
    for _, r in old_grp.iterrows(): inject(r['A_Date'], r['Campaign Name'].strip(), 0.0, float(r['A_Count']), float(r['Inv_Sum']), p_only=True)

if new_rows: df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
df = df[df['Date_Parsed'] <= today]

# Verification
# FTD = today's CAC/leads + today's FFH by Form Date + Adm/Inv only from same-day Form Date == Admission Date rows.
ftd_df = df[(df['Date_Parsed'].dt.date == today.date()) & (~df['pipeline_only'])]
mtd_df = df[df['Date_Parsed'] >= datetime(today.year, today.month, 1)]
print(f"  FTD: FFH={ftd_df['FFH'].sum():.0f} Adm={ftd_df['Adm'].sum():.0f} Inv={ftd_df['Invoicing_Var'].sum():.0f}")
print(f"  MTD: Adm={mtd_df['Adm'].sum():.0f} Inv={mtd_df['Invoicing_Var'].sum():.0f}")

ov_f, f_gt = build_summary(ftd_df); ov_m, m_gt = build_summary(mtd_df); ov_y, y_gt = build_summary(df[df['Date_Parsed'] >= datetime(today.year, 1, 1)])
f_kpi = build_kpi('FTD', today.strftime('%d %b'), f_gt, 'For The Day'); m_kpi = build_kpi('MTD', today.strftime('%b %Y'), m_gt, 'Month to Date'); y_kpi = build_kpi('YTD', str(today.year), y_gt, 'Year to Date')
f_ins, f_css, f_ht = build_drilldown(ftd_df, 'ftd'); m_ins, m_css, m_ht = build_drilldown(mtd_df, 'mtd'); y_ins, y_css, y_ht = build_drilldown(df[df['Date_Parsed'] >= datetime(today.year, 1, 1)], 'ytd')
p1 = f'<h3 class="sec-title">Overall Summary (FTD)</h3>{f_kpi}{ov_f}<h3 class="sec-title">Overall Summary (MTD)</h3>{m_kpi}{ov_m}<h3 class="sec-title">Overall Summary (YTD)</h3>{y_kpi}{ov_y}<h3 class="sec-title" style="margin-top:40px;">DETAILED DRILLDOWN (FTD)</h3>{f_ht}<h3 class="sec-title">DETAILED DRILLDOWN (MTD)</h3>{m_ht}<h3 class="sec-title">DETAILED DRILLDOWN (YTD)</h3>{y_ht}'
d_l, d_c = make_charts(df, 'DSA', 'DSA'); b_l, b_c = make_charts(df, 'Brand', 'Brand'); m_l, m_c = make_charts(df, 'Meta', 'Meta Ads')
p2, p3, p4 = graph_wrap(d_l, d_c), graph_wrap(b_l, b_c), graph_wrap(m_l, m_c)

with open(os.path.join(WORKSPACE, 'clean_css.txt'),'r',errors='ignore') as f: bcss = f.read()
bcss = re.sub(r'#cb-[^}]+\{[^}]+\}', '', bcss)
with open(os.path.join(WORKSPACE, 'clean_js.txt'),'r',errors='ignore') as f: cjs = f.read()

extra_css = ".table-wrap{overflow:auto;-webkit-overflow-scrolling:touch;}thead th{position:sticky;top:0;background:#f1f5f9;z-index:10;font-weight:800!important;color:#0f172a;}.sticky-col{position:sticky;left:0;z-index:20;background:inherit;}.kpi-band{margin-bottom:20px;}.kpi-band-title{font-size:12px;font-weight:800;letter-spacing:1px;text-transform:uppercase;color:#475569;margin-bottom:10px;}.kpi-scroll{display:flex;gap:10px;overflow-x:auto;scrollbar-width:none;padding-bottom:10px;}.kc{flex-shrink:0;background:#ffffff;border:1px solid #e4e8ef;border-radius:12px;padding:13px 14px 11px;min-width:112px;box-shadow:0 1px 3px rgba(0,0,0,.08);position:relative;overflow:hidden;}.kc::before{content:'';position:absolute;top:0;left:0;right:0;height:4px;background:#2563eb;}.ac-blue::before{background:#2563eb;} .ac-cyan::before{background:#0891b2;} .ac-green::before{background:#059669;}.ac-purple::before{background:#7c3aed;} .ac-amber::before{background:#d97706;} .ac-orange::before{background:#ea580c;}.kc-lbl{font-size:10px;font-weight:700;text-transform:uppercase;color:#64748b;margin-bottom:7px;}.kc-val{font-size:21px;font-weight:900;color:#1e293b;font-family:monospace;line-height:1;}.kc-sub{font-size:10px;color:#9ca3af;margin-top:5px;font-weight:600;}.camp-row td{background:#ffffff!important;color:#475569;font-weight:600;border-bottom:1px dashed #cbd5e1;}.sec-title{font-size:20px;font-weight:800;margin:35px 0 20px;color:#1e293b;padding-bottom:12px;border-bottom:3px solid #2563eb;display:inline-block;}.graph-card{padding:20px 10px;}.graph-title{font-size:14px;font-weight:700;color:#1e293b;margin:0 0 10px 10px;}.responsive-img{width:100%;max-width:100%;height:auto;border-radius:8px;border:1px solid #e4e8ef;}"
p5_toolbar = """<div class="gb-desk"><div class="gb-bar"><div class="gb-grp"><em>Period</em><div class="gb-seg"><button class="gbtn on" data-gb="period" data-val="0">FTD</button><button class="gbtn" data-gb="period" data-val="1">MTD</button><button class="gbtn" data-gb="period" data-val="2">YTD</button></div></div><div class="gb-grp" id="gb-cmp-grp"><em>\u21c4 vs Period</em><div class="gb-seg"><button class="gbtn on" data-gb="cmp" data-val="">Off</button><button class="gbtn" data-gb="cmp" data-val="0">FTD</button><button class="gbtn" data-gb="cmp" data-val="1">MTD</button><button class="gbtn" data-gb="cmp" data-val="2">YTD</button></div></div><div class="gb-grp"><em>Compare By</em><div class="gb-seg"><button class="gbtn on" data-gb="compare" data-val="platform">Platforms</button><button class="gbtn" data-gb="compare" data-val="account">Accounts</button><button class="gbtn" data-gb="compare" data-val="campaign">Campaigns</button></div></div><div class="gb-grp"><em>Metric</em><select id="gbmet" class="gb-sel"><option value="1">Spend (\u20b9)</option><option value="2">Panel Leads</option><option value="3">LMS Leads</option><option value="4">Dup %</option><option value="5">FFH</option><option value="6">ADM</option><option value="7">Inv Var (\u20b9)</option><option value="8">CPL Panel (\u20b9)</option><option value="9">CPL LMS (\u20b9)</option><option value="10">CAC FFH (\u20b9)</option><option value="11">CAC ADM (\u20b9)</option><option value="12">ARPU (\u20b9)</option><option value="13">CAC / ARPU</option><option value="14">L2F %</option><option value="15">L2A %</option><option value="16">F2A %</option></select></div><div class="gb-grp"><em>Chart Type</em><div class="gb-seg"><button class="gbtn on" data-gb="chart" data-val="vbar">Bar</button><button class="gbtn" data-gb="chart" data-val="hbar">H-Bar</button><button class="gbtn" data-gb="chart" data-val="pie">Pie</button><button class="gbtn" data-gb="chart" data-val="donut">Donut</button></div></div><div class="gb-grp" id="gb-topn-grp"><em>Top N</em><select id="gbtopn" class="gb-sel"><option value="0">All</option><option value="10">Top 10</option><option value="20" selected>Top 20</option><option value="30">Top 30</option></select></div><div class="gb-grp" style="margin-left:auto;"><em>&nbsp;</em><div style="display:flex;gap:8px;align-items:center;"><button class="gb-go" onclick="gbRun()">Build Chart</button></div></div></div><div class="gb-area" id="gbarea"><p class="gb-ph" id="gbph"><span>\U0001f4c2</span>Select options above and click <strong>Build Chart</strong></p><canvas id="gbcv" style="display:none;"></canvas></div><div class="gb-st" id="gbst"></div></div>"""

HTML = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=5"><title>Degreefyd {LABEL} Dashboard — {today.strftime('%d %b %Y')}</title><style>{bcss}{f_css}{m_css}{y_css}{extra_css}</style></head><body>{f_ins}{m_ins}{y_ins}<input type="radio" name="tabs" id="t1" checked><input type="radio" name="tabs" id="t2"><input type="radio" name="tabs" id="t3"><input type="radio" name="tabs" id="t4"><input type="radio" name="tabs" id="t5"><div class="wrap"><div class="hdr"><h1>Degreefyd {LABEL} Dashboard</h1><p>Intelligence &bull; {today.strftime('%d %b %Y')} &bull; v11 (Golden)</p></div><div class="tabs"><label for="t1" class="lbl-t1">📊 SUMMARIES</label><label for="t2" class="lbl-t2">🔷 DSA</label><label for="t3" class="lbl-t3">🔶 BRAND</label><label for="t4" class="lbl-t4">🟣 META ADS</label><label for="t5" class="lbl-t5">📈 GRAPH BUILDER</label></div><div id="p1" class="panel">{p1}</div><div id="p2" class="panel">{p2}</div><div id="p3" class="panel">{p3}</div><div id="p4" class="panel">{p4}</div><div id="p5" class="panel" style="padding:0;">{p5_toolbar}<script>{cjs}</script></div></div></body></html>"""

with open(OUTPUT_PATH, 'w', encoding='utf-8-sig', errors='ignore') as f: f.write(HTML)
load_dotenv(os.path.join(WORKSPACE, '.env'))
W_TOK, W_GRP = os.getenv('WHAPI_TOKEN'), os.getenv('WHATSAPP_GROUP')
with open(OUTPUT_PATH, 'rb') as f: b64 = base64.b64encode(f.read()).decode('utf-8')
caption = f"📊 *DEGREEFYD {LABEL} DASHBOARD — {today.strftime('%d %b %Y').upper()}*\n\n✅ FTD (Same-Day): FFH={ftd_df['FFH'].sum():.0f} | ADM={ftd_df['Adm'].sum():.0f} | Inv={fcf(ftd_df['Invoicing_Var'].sum())}\n✅ MTD Total: ADM={mtd_df['Adm'].sum():.0f} | Inv={fcf(mtd_df['Invoicing_Var'].sum())}\n✅ Improved Platform Attribution Applied\n✅ Bold Headers & 10-Day Graphs"
resp = requests.post("https://gate.whapi.cloud/messages/document", headers={"authorization": f"Bearer {W_TOK}"}, json={"to": W_GRP, "media": f"data:text/html;name=Degreefyd_{LABEL}_v11.html;base64,{b64}", "caption": caption}, timeout=60)
print(f"WHAPI status: {resp.status_code}")
try:
    print("WHAPI response:", resp.json())
except Exception:
    print("WHAPI response:", resp.text[:500])
resp.raise_for_status()
print("Done.")
