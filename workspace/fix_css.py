import re

with open("/workspace/generate_final_white_fixed.py", "r", encoding="utf-8") as f:
    code = f.read()

code = code.replace("thead th { position: sticky; top: 0; z-index: 10; background: #f8fafc; }", "thead th {{ position: sticky; top: 0; z-index: 10; background: #f8fafc; }}")
code = code.replace("thead th.sticky-col { position: sticky; left: 0; top: 0; z-index: 20; background: #f8fafc !important; }", "thead th.sticky-col {{ position: sticky; left: 0; top: 0; z-index: 20; background: #f8fafc !important; }}")
code = code.replace("td.sticky-col { position: sticky; left: 0; z-index: 5; border-right: 2px solid #cbd5e1; }", "td.sticky-col {{ position: sticky; left: 0; z-index: 5; border-right: 2px solid #cbd5e1; }}")
code = code.replace(".account-row td.sticky-col { background: #f8fafc !important; }", ".account-row td.sticky-col {{ background: #f8fafc !important; }}")
code = code.replace(".camp-row td.sticky-col { background: #fff !important; }", ".camp-row td.sticky-col {{ background: #fff !important; }}")
code = code.replace(".daily-row td.sticky-col { background: #fdfdfd !important; }", ".daily-row td.sticky-col {{ background: #fdfdfd !important; }}")

with open("/workspace/generate_final_white_fixed.py", "w", encoding="utf-8") as f:
    f.write(code)
print("Fixed CSS escaping.")
