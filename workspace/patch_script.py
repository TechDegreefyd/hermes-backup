import re

with open("/workspace/generate_final_white_fixed.py", "r", encoding="utf-8") as f:
    code = f.read()

# Replace the table headers
new_th = '<div class="table-wrap"><table><thead><tr><th class="text-left sticky-col">Account / Campaign</th><th class="num">Spends</th><th class="num">Pannel_Leads</th><th class="num">Leads_LMS</th><th class="num">FFH</th><th class="num">ADM</th><th class="num">Inv_Var</th><th class="num">CPL_Pannel</th><th class="num">CPL_LMS</th><th class="num">CAC_FFH</th><th class="num">CAC_Adm</th><th class="num">ARPU</th><th class="num">CAC/ARPU</th><th class="num">L2F</th><th class="num">L2A</th><th class="num">F2A</th></tr></thead>'
code = re.sub(r'<div class="table-wrap"><table><thead><tr><th.*?</tr></thead>', new_th, code)

# Replace the 'rats' function and values unpack
rats_def = """            def rats(v):
                sp, lp, ll, ff, ad, iv = v['Spends'], v['Pannel_Lead'], v['Lead_LMS'], v['FFH'], v['Adm'], v['Invoicing_Var']
                cpl_p = sp/lp if lp>0 else 0
                cpl_l = sp/ll if ll>0 else 0
                cac_f = sp/ff if ff>0 else 0
                cac_a = sp/ad if ad>0 else 0
                arpu = iv/ad if ad>0 else 0
                cac_arpu = cac_a/arpu if arpu>0 else 0
                l2f = ff/ll*100 if ll>0 else 0
                l2a = ad/ll*100 if ll>0 else 0
                f2a = ad/ff*100 if ff>0 else 0
                return cpl_p, cpl_l, cac_f, cac_a, arpu, cac_arpu, l2f, l2a, f2a
            cpl_p, cpl_l, cac_f, cac_a, arpu, cac_arpu, l2f, l2a, f2a = rats(s)"""
code = re.sub(r'            def rats\(v\):.*?cl, ca, ar, du, l2, f2 = rats\(s\)', rats_def, code, flags=re.DOTALL)

# Replace account row building
acc_row = r"""html += f'<tbody><tr class="account-row"><td class="text-left sticky-col"><label for="{cid}" class="exp-lbl"><span class="chev">▶</span> {pi} <strong>{acct}</strong></label></td><td class="num"><strong>{format_currency(s["Spends"])}</strong></td><td class="num"><strong>{format_num(s["Pannel_Lead"])}</strong></td><td class="num"><strong>{format_num(s["Lead_LMS"])}</strong></td><td class="num"><strong>{format_num(s["FFH"])}</strong></td><td class="num"><strong>{format_num(s["Adm"])}</strong></td><td class="num"><strong>{format_currency(s["Invoicing_Var"])}</strong></td><td class="num"><strong>{format_currency(cpl_p)}</strong></td><td class="num"><strong>{format_currency(cpl_l)}</strong></td><td class="num"><strong>{format_currency(cac_f)}</strong></td><td class="num"><strong>{format_currency(cac_a)}</strong></td><td class="num"><strong>{format_currency(arpu)}</strong></td><td class="num"><strong>{format_pct(cac_arpu*100)}</strong></td><td class="num"><strong>{format_pct(l2f)}</strong></td><td class="num"><strong>{format_pct(l2a)}</strong></td><td class="num"><strong>{format_pct(f2a)}</strong></td></tr></tbody><tbody class="camp-body" id="body-{cid}">'"""
code = re.sub(r'html \+= f\'<tbody><tr class="account-row">.*?<tbody class="camp-body" id="body-{cid}">\'', acc_row, code)

# Replace camp values unpack
code = code.replace("ccl, cca, car, cdu, cl2, cf2 = rats(c)", "ccpl_p, ccpl_l, ccac_f, ccac_a, carpu, ccac_arpu, cl2f, cl2a, cf2a = rats(c)")

# Replace camp row building
camp_row = r"""html += f'<tr class="camp-row"><td class="text-left sticky-col">{clb}</td><td class="num">{format_currency(c["Spends"])}</td><td class="num">{format_num(c["Pannel_Lead"])}</td><td class="num">{format_num(c["Lead_LMS"])}</td><td class="num">{format_num(c["FFH"])}</td><td class="num">{format_num(c["Adm"])}</td><td class="num">{format_currency(c["Invoicing_Var"])}</td><td class="num">{format_currency(ccpl_p)}</td><td class="num">{format_currency(ccpl_l)}</td><td class="num">{format_currency(ccac_f)}</td><td class="num">{format_currency(ccac_a)}</td><td class="num">{format_currency(carpu)}</td><td class="num">{format_pct(ccac_arpu*100)}</td><td class="num">{format_pct(cl2f)}</td><td class="num">{format_pct(cl2a)}</td><td class="num">{format_pct(cf2a)}</td></tr>'"""
code = re.sub(r'html \+= f\'<tr class="camp-row">.*?</tr>\'', camp_row, code)

# Fix daily rows CSS and colspan
daily_hdr = r"""html += f'<tbody class="daily-body" id="body-{iid}"><tr class="daily-hdr"><th colspan="16" style="text-align:left; padding-left:50px; background:#f8fafc;">Daily</th></tr>'"""
code = re.sub(r'html \+= f\'<tbody class="daily-body".*?Daily</th></tr>\'', daily_hdr, code)

daily_row = r"""for _, r in c['rows'].iterrows(): html += f'<tr class="daily-row"><td class="text-left sticky-col" style="padding-left:50px; font-size:11px;"><strong>{r["Date"]}</strong><br>{r["Ad Name"]}</td><td class="num">{format_currency(r["Spends"])}</td><td class="num">{format_num(r["Pannel_Lead"])}</td><td class="num">{format_num(r["Lead_LMS"])}</td><td class="num">{format_num(r["FFH"])}</td><td class="num">{format_num(r["Adm"])}</td><td class="num">{format_currency(r["Invoicing_Var"])}</td><td colspan="9"></td></tr>'"""
code = re.sub(r'for _, r in c\[\'rows\'\].iterrows\(\): html \+= f\'<tr class="daily-row">.*?</tr>\'', daily_row, code)

# Finally, inject the CSS we wrote earlier
css_fix = """
/* Top header lock - only target thead to prevent daily-hdr from sticking */
thead th { position: sticky; top: 0; z-index: 10; background: #f8fafc; }
/* Top-left corner lock */
thead th.sticky-col { position: sticky; left: 0; top: 0; z-index: 20; background: #f8fafc !important; }
/* Left column lock for all body rows */
td.sticky-col { position: sticky; left: 0; z-index: 5; border-right: 2px solid #cbd5e1; }
/* Solid backgrounds for left column to prevent overlapping when scrolling horizontally */
.account-row td.sticky-col { background: #f8fafc !important; }
.camp-row td.sticky-col { background: #fff !important; }
.daily-row td.sticky-col { background: #fdfdfd !important; }
</style>"""
code = code.replace("</style>", css_fix)

with open("/workspace/generate_final_white_fixed.py", "w", encoding="utf-8") as f:
    f.write(code)
print("Patched script.")
