# Hermes Operations & VPS Migration Guide

## 🚀 Core Philosophy
- **Telegram First**: All agent control and task assignments happen via Telegram (@hermes_degreefyd_bot).
- **WHAPI for Delivery**: All reports (PDF, Excel, HTML) must be delivered to the WhatsApp Admin Group (`120363426619711887@g.us`) using the WHAPI integration.
- **Blunt & Proactive**: Hermes speaks directly, avoids fluff, and executes scripts autonomously. If a limit is hit, it reports it immediately.
- **INR (₹) Always**: All financial data, ad spends, and CAC metrics must be in Indian Rupees.

## 🛠 Tech Stack Requirements (WSL/VPS)
- **OS**: Debian/Ubuntu (WSL2 supported).
- **Runtime**: Node.js v22+, Python 3.10+.
- **Database**: External PostgreSQL (credentials in `.env`).
- **Dependencies**: 
    - `pnpm` for Node packages.
    - `pip install pandas psycopg2-binary requests python-dotenv openpyxl jinja2 plotly`.
    - **Browser Tools**: For screenshot generation, install `playwright` and its system dependencies (`libglib-2.0.so.0`, `libnss3`, etc.).

## 📂 Key Files Explained
- `.env`: Contains all API tokens (Meta, WHAPI, Database, Google). **DO NOT LOSE THIS.**
- `report_config.json`: Defines weekly/monthly targets for the Online LMS reports.
- `regular_report_config.json`: Defines targets for the Regular LMS reports.
- `generate_final_white_fixed.py`: The master script for the "Premium White" aesthetic dashboard.
- `extract_metrics.py`: The logic for pulling lead and admission data from the DB.

## 🔄 Daily Workflow (Crons)
1. **Admission Tracking**: `daily_admission_cron.py` runs to monitor admission targets.
2. **Online Reports**: `send_daily_report_cron.py` triggers the extraction, HTML generation, and WhatsApp delivery.
3. **Regular Reports**: `cron_regular_report.py` handles the non-online lead tracking.

## ⚠️ Critical Rules for Hermes
1. **Pathing**: Always use absolute paths (e.g., `/workspace/file.py`) to avoid issues with cron working directories.
2. **Admission Criteria**: Admissions exclude partial payments (`fee_type NOT ILIKE '%partial%'`).
3. **ICC Logic**: ICC is tracked via the `first_icc_date` column in the `students` table.
4. **Target Extraction**: If the user provides targets in raw text, Hermes must update the `.json` configs automatically.
