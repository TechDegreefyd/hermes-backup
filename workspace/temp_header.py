import asyncio
import os
import sys
import json
import pandas as pd
import asyncpg
from datetime import datetime, timedelta
from dotenv import load_dotenv
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side

load_dotenv('/workspace/.env')

DB_HOST = os.getenv("ONLINE_LMS_DB_HOST")
DB_PORT = int(os.getenv("ONLINE_LMS_DB_PORT", "54321"))
DB_NAME = os.getenv("ONLINE_LMS_DB_NAME")
DB_USER = os.getenv("ONLINE_LMS_DB_USER")
DB_PASSWORD = os.getenv("ONLINE_LMS_DB_PASSWORD")

# Load configuration and targets
CONFIG_FILE = '/workspace/report_config.json'
with open(CONFIG_FILE, 'r') as f:
    config = json.load(f)

# -------------------------------------------------------------
# DYNAMIC DATE LOGIC FOR FUTURE-PROOFING
# -------------------------------------------------------------
# If current time is before 6 AM IST, we consider "today's report" to be for yesterday.
now_utc = datetime.utcnow()
now_ist = now_utc + timedelta(hours=5, minutes=30)

if now_ist.hour < 6:
    report_date = now_ist - timedelta(days=1)
else:
    report_date = now_ist

FTD_DATE = report_date.strftime('%Y-%m-%d')

# 2. MTD is ALWAYS the 1st of the current month to the report date
MTD_START = report_date.replace(day=1).strftime('%Y-%m-%d')
MTD_END = FTD_DATE

# 3. Weekly/Target Period is pulled from the config file. 
WEEK_START = config.get("target_period", {}).get("start_date", (report_date - timedelta(days=report_date.weekday())).strftime('%Y-%m-%d'))
WEEK_END = config.get("target_period", {}).get("end_date", FTD_DATE)

print(f"Generating report for FTD: {FTD_DATE}, WEEK: {WEEK_START} to {WEEK_END}, MTD: {MTD_START} to {MTD_END}")

# Load Targets
SUPERVISOR_TARGETS = config.get("supervisor_targets", {})
REVENUE_TARGETS = config.get("counsellor_targets", {})
