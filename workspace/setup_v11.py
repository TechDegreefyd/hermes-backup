import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = "/workspace" if os.path.isdir("/workspace") else SCRIPT_DIR
TEMPLATE = os.path.join(WORKSPACE, "build_v11_template.py")

with open(TEMPLATE, "r", encoding="utf-8") as f:
    code = f.read()

# Online
code_online = code.replace('SHEET_ID    = "1jzgnRxmmLIe_DAZ7nwHSRXeO6sI4CRxlTatc0T88ukY"', 'SHEET_ID    = "1jzgnRxmmLIe_DAZ7nwHSRXeO6sI4CRxlTatc0T88ukY"')
code_online = code_online.replace('OUTPUT_PATH = os.path.join(WORKSPACE, "Degreefyd_Final_Master_White.html")', 'OUTPUT_PATH = os.path.join(WORKSPACE, "Degreefyd_Online_v11.html")')
code_online = code_online.replace('LABEL       = "ONLINE"', 'LABEL       = "ONLINE"')
with open(os.path.join(WORKSPACE, "run_online_v11.py"), "w", encoding="utf-8") as f:
    f.write(code_online)

# Regular
code_regular = code.replace('SHEET_ID    = "1jzgnRxmmLIe_DAZ7nwHSRXeO6sI4CRxlTatc0T88ukY"', 'SHEET_ID    = "1QQ_Z50FDAhuBbVX5ioCjfgyFjfhr3y0gMGbQqteQ1f8"')
code_regular = code_regular.replace('OUTPUT_PATH = os.path.join(WORKSPACE, "Degreefyd_Final_Master_White.html")', 'OUTPUT_PATH = os.path.join(WORKSPACE, "Degreefyd_Regular_v11.html")')
code_regular = code_regular.replace('LABEL       = "ONLINE"', 'LABEL       = "REGULAR"')
with open(os.path.join(WORKSPACE, "run_regular_v11.py"), "w", encoding="utf-8") as f:
    f.write(code_regular)

print(f"Created run scripts in {WORKSPACE}")
