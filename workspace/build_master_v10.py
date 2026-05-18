"""
Degreefyd Master Dashboard — v10 (FIXED)
=========================================
Fixes vs previous versions:
  1. FFH, Adm, Invoicing_Var — pulled from 'FFH & Above' sheet, NOT CAC sheet
  2. Activity-Based Attribution — FFH keyed on Form Date, Adm/Inv keyed on Admission Date
  3. Rogue future-date guard — today anchored from CAC BEFORE merging CRM rows
  4. Revenue leakage — unmatched CRM entries appended as Platform='Unknown' rows
  5. Graphs — last 10 days only, zero-value labels skipped, 45° rotated x-axis
  6. Graph mask — DSA/Brand searched across Platform + Type + Account columns
  7. All file paths absolute (/workspace/)
  8. pandas float assignment uses 0.0 not 0 to avoid LossySetitemError
  9. CAC/ARPU stored as ratio (not %) to match column index expectations
"""

import os, json, base64, io, subprocess, warnings, re
import requests
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime
from dotenv import load_dotenv

warnings.filterwarnings('ignore')

# ── CONFIG ──────────────────────────────────────────────────────────────────
SHEET_ID    = "1jzgnRxmmLIe_DAZ7nwHSRXeO6sI4CRxlTatc0T88ukY"
OUTPUT_PATH = "/workspace/Degreefyd_Final_Master_White.html"
GAPI        = "python3 /home/hermeswebui/.hermes/skills/productivity/google-workspace/scripts/google_api.py"
GRAPH_DAYS  = 10   # ← show last N days on trend charts

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
    """Return inline style for green/red heatmap on a metric."""
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
    cru = ca / ar if (ca > 0 and ar > 0) else 0   # ratio, not %
    l2f = ff / ll * 100 if ll > 0 else 0
    l2a = ad / ll * 100 if ll > 0 else 0
    f2a = ad / ff * 100 if ff > 0 else 0
    return ["Total","","", s, lp, ll, ff, ad, iv, cp, cl, cf, ca, ar, f"{cru:.2f}", l2f, l2a, f2a]

# ── SUMMARY TABLE ────────────────────────────────────────────────────────────
def build_summary(df_src):
    g_df  = df_src[df_src['Platform'].str.contains('Google', case=False, na=False)]
    m_df  = df_src[df_src['Platform'].str.contains('Meta',   case=False, na=False)]
    gs, ms, ov = agg(g_df), agg(m_df), agg(df_src)

    # buckets for heatmap colouring (Google vs Meta only)
    bkt = {}
    for s in [gs, ms]:
        lp, ll = pnum(s[4]), pnum(s[5])
        bkt.setdefault('dup',  []).append((lp-ll)/lp*100 if lp>0 else 0)
        for k, i in zip(('cpl_p','cpl_l','cac_f','cac_a','l2f','l2a','f2a'), (9,10,11,12,15,16,17)):
            bkt.setdefault(k, []).append(pnum(s[i]))

    TH = '<th class="num">'
    hdr = (f'<div class="table-wrap"><table class="overall-table"><thead><tr>'
           f'<th class="text-left sticky-col">Platform</th>'
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
    TH = '<th class="num">'
    html = (f'<div class="table-wrap" style="margin-top:20px;"><table>'
            f'<thead><tr><th class="text-left sticky-col">Account / Campaign</th>'
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
        # Search across Platform, Type, AND Account — DSA/Brand can appear in any
        m1 = df_full['Platform'].str.contains(pattern, case=False, na=False)
        m2 = df_full.get('Type', pd.Series(dtype=str)).str.contains(pattern, case=False, na=False)
        m3 = df_full['Account'].str.contains(pattern, case=False, na=False)
        sub = df_full[m1 | m2 | m3].copy()
        if sub.empty:
            print(f"  [WARN] No data for pattern '{pattern}'")
            return "", ""
        daily = (sub.groupby('Date_Parsed')
                    .agg(Spends=('Spends','sum'), PL=('Pannel_Lead','sum'), LL=('Lead_LMS','sum'))
                    .reset_index().sort_values('Date_Parsed'))
        # Keep last n_days with actual spend or leads
        daily = daily[(daily['PL']>0) | (daily['Spends']>0)].tail(n_days).reset_index(drop=True)
        if daily.empty:
            print(f"  [WARN] All zeros for pattern '{pattern}'")
            return "", ""
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
            # labels — stagger above/below, skip zeros
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
    except Exception as e:
        print(f"  [ERROR] Chart for '{pattern}': {e}")
        return "", ""

def graph_wrap(l_b64, c_b64):
    if not l_b64: return '<div class="graph-card"><p style="padding:20px;color:#94a3b8;">No data available.</p></div>'
    return (f'<div class="graph-card">'
            f'<h4 class="graph-title">Leads Trend</h4>'
            f'<img src="data:image/png;base64,{l_b64}" class="responsive-img">'
            f'<h4 class="graph-title" style="margin-top:24px;">CPL Trend</h4>'
            f'<img src="data:image/png;base64,{c_b64}" class="responsive-img">'
            f'</div>')

# ── FETCH DATA ────────────────────────────────────────────────────────────────
print("Fetching Day Wise CAC Report...")
r = subprocess.run(
    ["python3",
     "/home/hermeswebui/.hermes/skills/productivity/google-workspace/scripts/google_api.py",
     "sheets", "get", SHEET_ID, "'Day Wise CAC Report'!A1:S20000"],
    capture_output=True, text=True
)
cac_raw = json.loads(r.stdout)

print("Fetching FFH & Above...")
r2 = subprocess.run(
    ["python3",
     "/home/hermeswebui/.hermes/skills/productivity/google-workspace/scripts/google_api.py",
     "sheets", "get", SHEET_ID, "'FFH & Above'!A1:Z2000"],
    capture_output=True, text=True
)
ffh_raw = json.loads(r2.stdout)

# ── BUILD CAC DATAFRAME ───────────────────────────────────────────────────────
# Row 0 = source labels (Meta/LMS/etc), Row 1 = column headers, Row 2+ = data
df = pd.DataFrame(cac_raw[2:], columns=[str(c).strip() for c in cac_raw[1]])
for c in ('Spends','Pannel_Lead','Lead_LMS','FFH','Adm','Invoicing_Var'):
    df[c] = df[c].apply(pnum)
df['Date_Parsed'] = pd.to_datetime(df['Date'], errors='coerce')
df = df.dropna(subset=['Date_Parsed'])
df = df[df['Platform'].str.strip() != '']   # drop empty spacer rows

# Anchor TODAY strictly from CAC sheet before any CRM merging
today = df['Date_Parsed'].max()
print(f"  CAC today anchor: {today.date()}")

# ── ZERO OUT CAC FFH/ADM/INV — will be repopulated from FFH sheet ─────────────
df['FFH']           = 0.0
df['Adm']           = 0.0
df['Invoicing_Var'] = 0.0
df['pipeline_only'] = False   # marks rows that are old-pipeline closures (not same-day)

# ── BUILD FFH DATAFRAME ───────────────────────────────────────────────────────
df_ffh = pd.DataFrame(ffh_raw[1:], columns=[str(c).strip() for c in ffh_raw[0]])
# Ensure 'Invoicing Variable' col exists
if 'Invoicing Variable' not in df_ffh.columns:
    df_ffh['Invoicing Variable'] = '0'
df_ffh['Inv_Value'] = (df_ffh['Invoicing Variable']
                       .astype(str).str.replace(',','').str.strip()
                       .replace(['','-','N/A',' '],'0')
                       .apply(pnum))
df_ffh['Form_Date']  = pd.to_datetime(df_ffh['Form Date'],       format='%d/%b/%Y', errors='coerce')
df_ffh['Adm_Date']   = pd.to_datetime(df_ffh['Admission Date'],  format='%d/%b/%Y', errors='coerce')
df_ffh['Camp_Name']  = df_ffh['Campaign Name'].astype(str).str.strip()

# ── GROUP BY ACTIVITY DATE ────────────────────────────────────────────────────
# FFH → keyed on Form Date
ffh_grp = (df_ffh.dropna(subset=['Form_Date'])
           .groupby(['Form_Date','Camp_Name'])
           .size().reset_index(name='FFH_Count'))

# Adm + Inv → keyed on Admission Date (only rows with an actual admission date)
adm_grp = (df_ffh[df_ffh['Adm_Date'].notna() & (df_ffh['Admission Date'].str.strip() != '')]
           .groupby(['Adm_Date','Camp_Name'])
           .agg(Adm_Count=('Adm_Date','count'), Inv_Sum=('Inv_Value','sum'))
           .reset_index())

# ── BUILD CAMPAIGN LOOKUP FROM CAC ────────────────────────────────────────────
camp_lookup = {}
for _, row in df.iterrows():
    for key in (str(row.get('Ad Name','')).strip(), str(row.get('Campaign','')).strip()):
        if key:
            camp_lookup[key] = {
                'Platform': row.get('Platform','Unknown'),
                'Account':  row.get('Account','Unknown'),
                'Campaign': str(row.get('Campaign','')).strip(),
                'Ad Name':  str(row.get('Ad Name','')).strip(),
            }

# ── MERGE FFH BACK INTO CAC ROWS ─────────────────────────────────────────────
new_rows = []

def inject(date, camp, ffh_val, adm_val, inv_val, pipeline_only=False):
    """Try to find a matching CAC row and increment it; otherwise queue new row."""
    # If it's a pipeline-only injection, ALWAYS create a new row so we don't 
    # accidentally tag an existing CAC row (with spends/leads) as pipeline_only
    # and lose those spends in FTD.
    if not pipeline_only:
        mask_d = df['Date_Parsed'] == date
        mask_c = (df['Ad Name'].str.strip() == camp) | (df['Campaign'].str.strip() == camp)
        hits = df.index[mask_d & mask_c]
        if len(hits) > 0:
            idx = hits[0]
            df.at[idx, 'FFH']           += ffh_val
            df.at[idx, 'Adm']           += adm_val
            df.at[idx, 'Invoicing_Var'] += inv_val
            return

    # If pipeline_only OR no hit found, append new row
    meta = camp_lookup.get(camp, {'Platform':'Unknown','Account':'Unknown',
                                   'Campaign':camp,'Ad Name':camp})
    new_rows.append({
        'Platform': meta['Platform'], 'Account': meta['Account'],
        'Campaign': meta['Campaign'], 'Ad Name': meta['Ad Name'],
        'Date': date.strftime('%Y-%m-%d'), 'Date_Parsed': date,
        'Type': '', 'Spends': 0.0, 'Pannel_Lead': 0.0, 'Lead_LMS': 0.0,
        'FFH': ffh_val, 'Adm': adm_val, 'Invoicing_Var': inv_val,
        'pipeline_only': pipeline_only,
    })

# ── ATTRIBUTION RULES ────────────────────────────────────────────────────────
# FTD:  FFH keyed on Form Date. Adm+Inv only counted if Form Date == Adm Date
#       (same-day pipeline). Old leads admitted later must NOT inflate FTD.
# MTD/YTD: Adm+Inv keyed on Admission Date regardless of Form Date.
#
# Implementation:
#   Step 1 — inject FFH by Form Date (always)
#   Step 2 — inject same-day Adm+Inv by Form Date (Form Date == Adm Date)
#   Step 3 — inject old-pipeline Adm+Inv by Adm Date (Form Date < Adm Date)
#             These rows land on their Adm Date → outside FTD if Adm Date != Form Date.

# Step 1 — FFH by Form Date
for _, r in ffh_grp.iterrows():
    inject(r['Form_Date'], r['Camp_Name'], float(r['FFH_Count']), 0.0, 0.0)

# Split adm_grp into same-day vs old-pipeline
# We need per-row Form Date to compare — rebuild from df_ffh directly
df_ffh_adm = df_ffh[df_ffh['Adm_Date'].notna() & (df_ffh['Admission Date'].str.strip() != '')].copy()

# Step 2 — same-day: Form Date == Adm Date → inject on Form Date
same_day = df_ffh_adm[df_ffh_adm['Form_Date'].notna() & (df_ffh_adm['Form_Date'] == df_ffh_adm['Adm_Date'])]
same_day_grp = (same_day.groupby(['Form_Date','Camp_Name'])
                .agg(Adm_Count=('Adm_Date','count'), Inv_Sum=('Inv_Value','sum'))
                .reset_index())
for _, r in same_day_grp.iterrows():
    inject(r['Form_Date'], r['Camp_Name'], 0.0, float(r['Adm_Count']), float(r['Inv_Sum']))

# Step 3 — old-pipeline: Form Date != Adm Date (or no Form Date) → inject on Adm Date
old_pipe = df_ffh_adm[df_ffh_adm['Form_Date'].isna() | (df_ffh_adm['Form_Date'] != df_ffh_adm['Adm_Date'])]
old_pipe_grp = (old_pipe.groupby(['Adm_Date','Camp_Name'])
                .agg(Adm_Count=('Adm_Date','count'), Inv_Sum=('Inv_Value','sum'))
                .reset_index())
for _, r in old_pipe_grp.iterrows():
    inject(r['Adm_Date'], r['Camp_Name'], 0.0, float(r['Adm_Count']), float(r['Inv_Sum']), pipeline_only=True)

if new_rows:
    df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
    print(f"  Appended {len(new_rows)} unmatched CRM rows as Platform rows")

# ── ROGUE FUTURE DATE GUARD ───────────────────────────────────────────────────
df = df[df['Date_Parsed'] <= today]
print(f"  Final df rows: {len(df)}")

# ── VERIFICATION PRINT ────────────────────────────────────────────────────────
ftd_df = df[(df['Date_Parsed'].dt.date == today.date()) & (~df['pipeline_only'])]
mtd_df = df[df['Date_Parsed'] >= datetime(today.year, today.month, 1)]
print(f"\n── FTD ({today.date()}) ──────────────────────────")
print(f"  Spends:  ₹{ftd_df['Spends'].sum():,.2f}")
print(f"  P.Leads: {ftd_df['Pannel_Lead'].sum():.0f}  |  LMS Leads: {ftd_df['Lead_LMS'].sum():.0f}")
print(f"  FFH:     {ftd_df['FFH'].sum():.0f}  |  Adm: {ftd_df['Adm'].sum():.0f}  |  Inv: ₹{ftd_df['Invoicing_Var'].sum():,.2f}")
print(f"\n── MTD ({today.strftime('%b %Y')}) ──────────────────────────")
print(f"  Spends:  ₹{mtd_df['Spends'].sum():,.2f}")
print(f"  P.Leads: {mtd_df['Pannel_Lead'].sum():.0f}  |  LMS Leads: {mtd_df['Lead_LMS'].sum():.0f}")
print(f"  FFH:     {mtd_df['FFH'].sum():.0f}  |  Adm: {mtd_df['Adm'].sum():.0f}  |  Inv: ₹{mtd_df['Invoicing_Var'].sum():,.2f}")

# ── BUILD HTML SECTIONS ───────────────────────────────────────────────────────
print("\nBuilding tables...")
ov_f, f_gt = build_summary(ftd_df)
ov_m, m_gt = build_summary(mtd_df)
ov_y, y_gt = build_summary(df[df['Date_Parsed'] >= datetime(today.year, 1, 1)])

f_kpi = build_kpi('FTD', today.strftime('%d %b'), f_gt, 'For The Day')
m_kpi = build_kpi('MTD', today.strftime('%b %Y'), m_gt, 'Month to Date')
y_kpi = build_kpi('YTD', str(today.year),         y_gt, 'Year to Date')

f_ins, f_css, f_ht = build_drilldown(ftd_df, 'ftd')
m_ins, m_css, m_ht = build_drilldown(mtd_df, 'mtd')
y_ins, y_css, y_ht = build_drilldown(df[df['Date_Parsed'] >= datetime(today.year, 1, 1)], 'ytd')

p1 = (f'<h3 class="sec-title">Overall Summary (FTD)</h3>{f_kpi}{ov_f}'
      f'<h3 class="sec-title">Overall Summary (MTD)</h3>{m_kpi}{ov_m}'
      f'<h3 class="sec-title">Overall Summary (YTD)</h3>{y_kpi}{ov_y}'
      f'<h3 class="sec-title" style="margin-top:40px;">DETAILED DRILLDOWN (FTD)</h3>{f_ht}'
      f'<h3 class="sec-title">DETAILED DRILLDOWN (MTD)</h3>{m_ht}'
      f'<h3 class="sec-title">DETAILED DRILLDOWN (YTD)</h3>{y_ht}')

# ── GRAPHS ────────────────────────────────────────────────────────────────────
print("Generating trend charts (last 10 days)...")
dsa_l,  dsa_c  = make_charts(df, 'DSA',   'DSA')
brd_l,  brd_c  = make_charts(df, 'Brand', 'Brand')
meta_l, meta_c = make_charts(df, 'Meta',  'Meta Ads')

p2 = graph_wrap(dsa_l,  dsa_c)
p3 = graph_wrap(brd_l,  brd_c)
p4 = graph_wrap(meta_l, meta_c)

# ── LOAD CSS + JS ─────────────────────────────────────────────────────────────
with open('/workspace/clean_css.txt', 'r', errors='ignore') as f: base_css = f.read()
base_css = re.sub(r'#cb-[^}]+\{[^}]+\}', '', base_css)   # strip stale checkbox IDs

with open('/workspace/clean_js.txt', 'r', errors='ignore') as f: clean_js = f.read()

dyn_css = f_css + m_css + y_css

extra_css = """
.table-wrap{overflow:auto;-webkit-overflow-scrolling:touch;}
thead th{position:sticky;top:0;background:#f1f5f9;z-index:10;font-weight:800!important;color:#0f172a;}
.sticky-col{position:sticky;left:0;z-index:20;background:inherit;}
.kpi-band{margin-bottom:20px;}
.kpi-band-title{font-size:12px;font-weight:800;letter-spacing:1px;text-transform:uppercase;color:#475569;margin-bottom:10px;}
.kpi-scroll{display:flex;gap:10px;overflow-x:auto;scrollbar-width:none;padding-bottom:10px;}
.kc{flex-shrink:0;background:#ffffff;border:1px solid #e4e8ef;border-radius:12px;padding:13px 14px 11px;min-width:112px;box-shadow:0 1px 3px rgba(0,0,0,.08);position:relative;overflow:hidden;}
.kc::before{content:'';position:absolute;top:0;left:0;right:0;height:4px;background:#2563eb;}
.ac-blue::before{background:#2563eb;} .ac-cyan::before{background:#0891b2;} .ac-green::before{background:#059669;}
.ac-purple::before{background:#7c3aed;} .ac-amber::before{background:#d97706;} .ac-orange::before{background:#ea580c;}
.kc-lbl{font-size:10px;font-weight:700;text-transform:uppercase;color:#64748b;margin-bottom:7px;}
.kc-val{font-size:21px;font-weight:900;color:#1e293b;font-family:monospace;line-height:1;}
.kc-sub{font-size:10px;color:#9ca3af;margin-top:5px;font-weight:600;}
.camp-row td{background:#ffffff!important;color:#475569;font-weight:600;border-bottom:1px dashed #cbd5e1;}
.sec-title{font-size:20px;font-weight:800;margin:35px 0 20px;color:#1e293b;padding-bottom:12px;border-bottom:3px solid #2563eb;display:inline-block;}
.graph-card{padding:20px 10px;}
.graph-title{font-size:14px;font-weight:700;color:#1e293b;margin:0 0 10px 10px;}
.responsive-img{width:100%;max-width:100%;height:auto;border-radius:8px;border:1px solid #e4e8ef;}
"""

# Graph Builder toolbar (unchanged from v9)
p5_toolbar = """<div class="gb-desk"><div class="gb-bar"><div class="gb-grp"><em>Period</em><div class="gb-seg"><button class="gbtn on" data-gb="period" data-val="0">FTD</button><button class="gbtn" data-gb="period" data-val="1">MTD</button><button class="gbtn" data-gb="period" data-val="2">YTD</button></div></div><div class="gb-grp" id="gb-cmp-grp"><em>\u21c4 vs Period</em><div class="gb-seg"><button class="gbtn on" data-gb="cmp" data-val="">Off</button><button class="gbtn" data-gb="cmp" data-val="0">FTD</button><button class="gbtn" data-gb="cmp" data-val="1">MTD</button><button class="gbtn" data-gb="cmp" data-val="2">YTD</button></div></div><div class="gb-grp"><em>Compare By</em><div class="gb-seg"><button class="gbtn on" data-gb="compare" data-val="platform">Platforms</button><button class="gbtn" data-gb="compare" data-val="account">Accounts</button><button class="gbtn" data-gb="compare" data-val="campaign">Campaigns</button></div></div><div class="gb-grp"><em>Metric</em><select id="gbmet" class="gb-sel"><option value="1">Spend (\u20b9)</option><option value="2">Panel Leads</option><option value="3">LMS Leads</option><option value="4">Dup %</option><option value="5">FFH</option><option value="6">ADM</option><option value="7">Inv Var (\u20b9)</option><option value="8">CPL Panel (\u20b9)</option><option value="9">CPL LMS (\u20b9)</option><option value="10">CAC FFH (\u20b9)</option><option value="11">CAC ADM (\u20b9)</option><option value="12">ARPU (\u20b9)</option><option value="13">CAC/ARPU</option><option value="14">L2F %</option><option value="15">L2A %</option><option value="16">F2A %</option></select></div><div class="gb-grp"><em>Chart Type</em><div class="gb-seg"><button class="gbtn on" data-gb="chart" data-val="vbar">Bar</button><button class="gbtn" data-gb="chart" data-val="hbar">H-Bar</button><button class="gbtn" data-gb="chart" data-val="pie">Pie</button><button class="gbtn" data-gb="chart" data-val="donut">Donut</button></div></div><div class="gb-grp" id="gb-topn-grp"><em>Top N</em><select id="gbtopn" class="gb-sel"><option value="0">All</option><option value="10">Top 10</option><option value="20" selected>Top 20</option><option value="30">Top 30</option></select></div><div class="gb-grp" style="margin-left:auto;"><em>&nbsp;</em><div style="display:flex;gap:8px;align-items:center;"><button class="gb-go" onclick="gbRun()">Build Chart</button></div></div></div><div class="gb-area" id="gbarea"><p class="gb-ph" id="gbph"><span>\U0001f4c2</span>Select options above and click <strong>Build Chart</strong></p><canvas id="gbcv" style="display:none;"></canvas></div><div class="gb-st" id="gbst"></div></div>"""

# ── ASSEMBLE HTML ─────────────────────────────────────────────────────────────
# Checkboxes MUST be direct children of <body>, before .wrap — Safari requirement
all_ins = f_ins + m_ins + y_ins

HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=5">
<title>Degreefyd Master Dashboard — {today.strftime('%d %b %Y')}</title>
<style>
{base_css}
{dyn_css}
{extra_css}
</style>
</head>
<body>
{all_ins}
<input type="radio" name="tabs" id="t1" checked>
<input type="radio" name="tabs" id="t2">
<input type="radio" name="tabs" id="t3">
<input type="radio" name="tabs" id="t4">
<input type="radio" name="tabs" id="t5">
<div class="wrap">
  <div class="hdr">
    <h1>Degreefyd Master Dashboard</h1>
    <p>Intelligence &bull; {today.strftime('%d %b %Y')} &bull; v10 (Data-Verified)</p>
  </div>
  <div class="tabs">
    <label for="t1" class="lbl-t1">📊 SUMMARIES</label>
    <label for="t2" class="lbl-t2">🔷 DSA</label>
    <label for="t3" class="lbl-t3">🔶 BRAND</label>
    <label for="t4" class="lbl-t4">🟣 META ADS</label>
    <label for="t5" class="lbl-t5">📈 GRAPH BUILDER</label>
  </div>
  <div id="p1" class="panel">{p1}</div>
  <div id="p2" class="panel">{p2}</div>
  <div id="p3" class="panel">{p3}</div>
  <div id="p4" class="panel">{p4}</div>
  <div id="p5" class="panel" style="padding:0;">{p5_toolbar}<script>{clean_js}</script></div>
</div>
</body>
</html>"""

# ── WRITE FILE ────────────────────────────────────────────────────────────────
with open(OUTPUT_PATH, 'w', encoding='utf-8-sig', errors='ignore') as f:
    f.write(HTML)
print(f"\nWrote {OUTPUT_PATH}  ({os.path.getsize(OUTPUT_PATH)//1024} KB)")

# ── SEND VIA WHAPI ────────────────────────────────────────────────────────────
load_dotenv('/workspace/.env')
WHAPI_TOKEN    = os.getenv('WHAPI_TOKEN')
WHATSAPP_GROUP = os.getenv('WHATSAPP_GROUP')

with open(OUTPUT_PATH, 'rb') as f:
    b64 = base64.b64encode(f.read()).decode('utf-8')

caption = (f"📊 *DEGREEFYD MASTER DASHBOARD — {today.strftime('%d %b %Y').upper()}* (v10)\n\n"
           f"✅ FFH & Admissions: pulled from FFH sheet (Activity-Based Attribution)\n"
           f"✅ FTD FFH: {int(ftd_df['FFH'].sum())} | ADM: {int(ftd_df['Adm'].sum())} | Inv: ₹{ftd_df['Invoicing_Var'].sum():,.0f}\n"
           f"✅ MTD ADM: {int(mtd_df['Adm'].sum())} | Inv: ₹{mtd_df['Invoicing_Var'].sum():,.0f}\n"
           f"✅ Graphs: last {GRAPH_DAYS} active days, clean labels, rotated axis\n"
           f"✅ Rogue-date guard active")

for attempt in range(3):
    try:
        resp = requests.post(
            "https://gate.whapi.cloud/messages/document",
            headers={"authorization": f"Bearer {WHAPI_TOKEN}"},
            json={"to": WHATSAPP_GROUP,
                  "media": f"data:text/html;name=Degreefyd_Master_Dashboard_{today.strftime('%d%b%Y')}.html;base64,{b64}",
                  "caption": caption},
            timeout=60
        )
        print(f"WHAPI: {resp.status_code} {resp.text[:120]}")
        if resp.status_code < 300:
            break
    except Exception as e:
        print(f"WHAPI attempt {attempt+1} failed: {e}")

print("Done.")
