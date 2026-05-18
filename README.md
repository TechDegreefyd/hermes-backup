# Hermes Agent — Full Workspace Backup (2026-05-18)

> **147 MB | 2,641 files** — Comprehensive backup of the Hermes agent workspace,
> cron jobs, skills, memories, scripts, and report templates.
>
> 🔒 **All API tokens scrubbed** — Meta/Facebook tokens, Google creds, .env files
> removed. Paths to `~/.hermes/google_token.json` preserved as references only.

---

## 📁 Top-Level Structure

```
workspace/
├── *.py                  # 314 Python scripts (report generators, cron, utilities)
├── *.html                # 113 generated dashboard/report files
├── *.json                # Config files (report_config.json, mappings)
├── *.xlsx / *.csv        # Spreadsheets & data exports
├── db-rules/             # LMS DB query rules (online_rules.md, regular_rules.md)
├── mcp_server.py         # MCP server for LMS DB queries
├── hermes-workspace/     # Hermes Workspace web UI codebase
├── generated_ads/        # Ad creative generation assets
├── meetings/             # Meeting notes & tools
├── scripts/              # Helper scripts
├── services/             # Service configs (open-webui.service)
└── .env.example          # Environment template (no actual secrets)

home/hermeswebui/.hermes/
├── config.yaml           # Hermes agent configuration
├── cron/                 # All 7 cron job definitions + run history
│   ├── jobs.json         # Cron job schedule & config
│   └── output/           # Run logs by job ID
├── skills/               # 100+ skills organized by category
│   ├── data-science/     #   LMS reporting, attribution, dashboards
│   ├── autonomous-ai-agents/  # Claude Code, Codex, Hermes agent
│   ├── marketing/        #   Ad generation, backlinks, competitor intel
│   ├── apis/             #   Meta/Google/API integrations
│   └── ...               #   (many more)
├── memories/             # Hermes agent's persistent memory
│   ├── MEMORY.md         # Agent memory (system notes)
│   └── USER.md           # User profile (preferences, facts)
└── *.json                # Channel/gateway/MCP state files
```

---

## 🧩 7 Cron Jobs Captured

| # | Job Name | Key Scripts | Skills Used |
|---|----------|-------------|-------------|
| 1 | **Daily Online LMS Reports** | `generate_and_send_lms_html.py` | online-lms-reporting |
| 2 | **Daily Regular LMS Reports** | `generate_and_send_regular_lms_html.py` | regular-lms-reporting |
| 3 | **Degreefyd Dashboards (Both)** | `run_online_v11.py`, `run_regular_v11.py` | degreefyd-ads-dashboard-generation |
| 4 | **Daily Regular API Recon** | `generate_regular_recon_report.py` | regular-lms-reconciliation-reporting |
| 5 | **Regular Admissions Graph** | `cron_regular_dashboard.py` | — |
| 6 | **Online Admissions Graph** | `cron_online_dashboard.py` | — |
| 7 | **Meta Ad Details** | — | degreefyd-meta-lms-attribution |

---

## 🔑 Key Report Generators (the "beautiful HTMLs")

| Script | Output |
|--------|--------|
| `run_online_v11.py` | `Degreefyd_Online_v11.html` |
| `run_regular_v11.py` | `Degreefyd_Regular_v11.html` |
| `build_v11_template.py` | Shared v11 template builder |
| `generate_and_send_lms_html.py` | `Online_LMS_HTML_*.html` |
| `generate_and_send_regular_lms_html.py` | `Regular_LMS_HTML_*.html` |
| `generate_regular_recon_report.py` | `Regular_Recon_*.html` |
| `generate_regular_reports.py` | `Regular_LMS_*.xlsx` |

---

## 📊 Generated Reports Backed Up

- `Degreefyd_Online_v11.html`, `Degreefyd_Regular_v11.html` — master dashboards
- `Online_LMS_HTML_2026-05-*.html` — daily online LMS reports
- `Regular_LMS_HTML_2026-05-*.html` — daily regular LMS reports
- `Regular_Recon_*` / `Branded_Recon_*` — API reconciliation reports
- `*_dashboard*.html` — various dashboard visualizations
- `ANALYSE_THIS.html`, `almost_final_report.html` — exploratory reports

---

## 🔒 Security: What Was Scrubbed

Before backup, **all hardcoded API tokens were removed** from source files:

| Type | Tokens Found | Action |
|------|-------------|--------|
| **Meta/Facebook** (EAA...) | 5 unique tokens across 47 files | Replaced with `""` |
| **Google API** (AIza...) | 0 found | — |
| **Apify Token** | 1 file (`scrape_60_ads.py`) | Changed to `os.getenv()` |
| **Google Token Files** | `~/.hermes/google_token.json` | Paths preserved, files excluded |
| **.env files** | `/workspace/.env`, `/workspace/hermes-workspace/.env` | Excluded from archive |
| **Auth files** | `auth.json`, `google_client_secret.json`, `fresh_token.json` | Excluded from archive |

> ⚠️ To restore functionality, set these env vars on the target machine:
> - `META_ACCESS_TOKEN` — for Meta/Facebook API scripts
> - `WHAPI_TOKEN` — for WhatsApp messaging
> - `APIFY_TOKEN` — for Apify scraping
> - `*_LMS_DB_*` — database connection vars (from the .env file)

---

## 📥 Restore Instructions

```bash
# Extract to a fresh workspace:
cd /home/mohit/workspace  # or your target dir
tar xzf hermes-full-backup-2026-05-18.tar.gz

# Copy config to Hermes home:
cp -r home/hermeswebui/.hermes/* ~/.hermes/

# Set env vars (create .env from template):
cp workspace/.env.example workspace/.env
# Then edit workspace/.env with your actual tokens

# Skills are already in ~/.hermes/skills/
# Cron jobs are in ~/.hermes/cron/jobs.json — restore via:
# hermes cron import ~/.hermes/cron/jobs.json  (if supported)

# Rebuild venv if needed:
python3 -m venv workspace/.venv
source workspace/.venv/bin/activate
pip install -r workspace/requirements.txt  # (if available)
```
