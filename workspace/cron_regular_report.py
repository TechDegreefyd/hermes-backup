import subprocess
import sys

BASE = "workspace"

def run_step(label, cmd):
    print(f"\n--- {label} ---")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    print(proc.stdout)
    if proc.returncode != 0:
        print(proc.stderr)
        raise SystemExit(proc.returncode)


def run():
    run_step("Generating Regular LMS Excel data", [sys.executable, f"{BASE}/generate_regular_reports.py"])
    run_step("Generating + sending Regular LMS HTML report", [sys.executable, f"{BASE}/generate_and_send_regular_lms_html.py"])

if __name__ == "__main__":
    run()
