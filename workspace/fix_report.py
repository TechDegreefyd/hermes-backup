import re

with open('/workspace/almost_final_report.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update CSS
css_additions = """
th { position: sticky; top: 0; z-index: 10; }
th.sticky-col { position: sticky; left: 0; top: 0; z-index: 15; background: #f8fafc !important; }
.account-row td.sticky-col { background: #f8fafc !important; z-index: 5; }
.camp-row td.sticky-col { background: #fff !important; z-index: 5; }
.daily-row td.sticky-col { background: #fdfdfd !important; z-index: 5; }
.daily-hdr th.sticky-col { background: #f8fafc !important; z-index: 15; }
</style>
"""
content = content.replace('</style>', css_additions)

# 2. Add graphs to p1
p1_graphs = """<div id="p1" class="panel"><div class="graph-card">
  <img class="responsive-img" src="Degreefyd_Online_overall_CAC_27-04-2026.jpeg" alt="Overall CAC">
  <img class="responsive-img" src="Degreefyd_Online_CAC_FTD_27-04-2026.jpeg" alt="CAC FTD">
  <img class="responsive-img" src="Degreefyd_Online_CAC_MTD_27-04-2026.jpeg" alt="CAC MTD">
  <img class="responsive-img" src="Degreefyd_Online_CAC_YTD_27-04-2026.jpeg" alt="CAC YTD">
</div>"""
content = content.replace('<div id="p1" class="panel">', p1_graphs)

# 3. Replace graphs in p2
p2_graphs = """<div id="p2" class="panel"><div class="graph-card">
  <img class="responsive-img" src="Degreefyd_Online_Google_ads_DSA_campaign_lead_pannel_and_lead_lms.jpeg" alt="DSA Lead">
  <img class="responsive-img" src="Degreefyd_Online_Google_ads_DSA_campaign_cpl_pannel_and_cpl_lms.jpeg" alt="DSA CPL">
</div>"""
content = re.sub(r'<div id="p2" class="panel">\s*<div class="graph-card">.*?</div>', p2_graphs, content, count=1, flags=re.DOTALL)

# 4. Replace graphs in p3
p3_graphs = """<div id="p3" class="panel"><div class="graph-card">
  <img class="responsive-img" src="Degreefyd_Online_Google_ads_Brand_campaign_lead_pannel_and_lead_lms.jpeg" alt="Brand Lead">
  <img class="responsive-img" src="Degreefyd_Online_Google_ads_Brand_campaign_cpl_pannel_and_cpl_lms.jpeg" alt="Brand CPL">
</div>"""
content = re.sub(r'<div id="p3" class="panel">\s*<div class="graph-card">.*?</div>', p3_graphs, content, count=1, flags=re.DOTALL)

# 5. Replace graphs in p4
p4_graphs = """<div id="p4" class="panel"><div class="graph-card">
  <img class="responsive-img" src="Degreefyd_Online_META_ads_lead_pannel_and_lead_lms.jpeg" alt="Meta Lead">
  <img class="responsive-img" src="Degreefyd_Online_META_ads_cpl_pannel_and_cpl_lms.jpeg" alt="Meta CPL">
</div>"""
content = re.sub(r'<div id="p4" class="panel">\s*<div class="graph-card">.*?</div>', p4_graphs, content, count=1, flags=re.DOTALL)

with open('/workspace/almost_final_report_fixed.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done")
