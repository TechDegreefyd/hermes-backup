User's Telegram bot: @hermes_degreefyd_bot (token stored in .env as TELEGRAM_BOT_TOKEN). Prefers Telegram for Hermes task assignment/integration over WhatsApp (avoids self-chat echoes). Provides details step-by-step when guided precisely.
§
Consultancy hierarchy: Supervisors (Varun, Sunil, Vishal, Siddhartha) and assigned Counsellors. Reports use 'Admission Target Vs Achievement' PDF with columns: Supervisor, Counselor, Achieve (count), FTD Achievement. Admissions exclude partial payments (fee_type NOT ILIKE '%partial%'). ICC uses first_icc_date. Admin group: 120363426619711887@g.us.
§
WSL(AsusZephyrusG16): /home/mohit/workspace/hermes-workspace. MCP lms_db server: command=/workspace/.venv/bin/python /workspace/mcp_server.py. Workspace UI: 3000, Dashboard: 8090, Gateway: 8642. MBA Fit bot: student_churn_bot.py, WHAPI group 120363426619711887@g.us.
§
LMS DB QUERY WORKFLOW (mandatory, every time):
Step 1 — MCP alive check: mcp_lms_db_list_databases() or simple SELECT to verify lms_db server is reachable.
Step 2 — Ask which DB: always ask "Which database(s)? regular_lms / regular_cgc_lms / regular_amity_lms / online_lms / all" if not explicitly stated.
Step 3 — Load DB rules: read /workspace/db-rules/<track>_rules.md (online_rules.md or regular_rules.md) — the rules are the primary reference.
Step 4 — Rules are NOT gospel: If stuck, getting unexpected results, or need schema details, use MCP tools (mcp_lms_db_describe_table, mcp_lms_db_run_select_query, mcp_lms_db_get_table_context) to verify against live DB.
Step 5 — Show SQL: Always display the exact SQL FIRST, then the result. Never skip the query block.
Step 6 — Query style: Use small, well-structured CTEs. Prefer window functions (LEAD, LAG, ROW_NUMBER, RANK). Break complex queries into multiple CTEs. Avoid unnecessary joins — use CTEs + analytical functions instead.
§
Combined sheet: 1I0KYVJjAFr6tsx_H10rPmkkzerKayJVziA68ShqzOPM. Master sheets READ-ONLY. Vishal fee target=₹20L (2000000) in report_config.json. LMS HTML scripts hang on WHAPI — verify output before sending. Regular config path bug: 'workspace/regular_report_config.json' → 'regular_report_config.json'. Branded recon uses FUZZY matching (15 patterns: LPU_Online, CU_Online, Amity_Online, Amity_University, Partner_Amity, Shoolini_Online, Galgotias, VGU_Online, Manipal_Online, GLA_Online, GLA_University, IGNOU, UA_MBA, F_UA) + 23 exact campaign IDs.
§
Architecture confirmed: Online LMS = single counsellor (L2 only, no L3). `assigned_counsellor_l3_id` is unpopulated. Regular LMS = L2/L3 split: L2 handles pre-application via `students.assigned_counsellor_id`, L3 handles application-onward via `course_status_journeys.assigned_l3_counsellor_id` (NOT `students.assigned_counsellor_l3_id` — sparsely populated). Regular L3 is course-wise (one student can have different L3 per course).
§
Campaign attribution: use `student_lead_activities.utm_campaign` via `DISTINCT ON(student_id) ORDER BY created_at ASC` for first-activity campaign. NOT students.first_source_url UTM parsing. sla has utm_campaign, utm_source, utm_medium, utm_campaign_id, utm_keyword, utm_adgroup_id, utm_creative_id. "No Campaign" = NULL/empty utm_campaign in sla.
§
Form Working Status Query (May 14, 2026): Active forms = latest csj status in 8-pipeline + had ANY csj activity during date range. "Not Worked" = status set by L2 (not L3) — join counsellors on csj.counsellor_id = status_by, check role='l2'. Buckets (0-3 / 4-6 / 6+ days) = last remark from ASSIGNED L3 only. Totals match verified against user reference for May 1-14, 2026: CU Lucknow 46, CU Mohali 248, LPU 101 = 395 total. NW=94 (71+14+9).
§
DAILY METRICS ATTRIBUTION (confirmed May 13): SHOW SQL every query. ATTEMPTED = leads day X → any remark ever. Total Unique → sr.counsellor_id. First Connected → sr.counsellor_id (who made first-ever Connected). First ICC → s.assigned_counsellor_id. First NI → sr.counsellor_id (first-ever remark for student with current_student_status='NotInterested'). Rules file patched. RULES FIRST, then query — never guess.
§
DB rules files at /workspace/db-rules/ can be edited on user instruction — update business rules, golden queries, pitfalls, or discovered patterns via text-to-sql-db-rules skill or direct file write.
§
NEVER create standalone Python scripts/files for DB queries — always use MCP tools (mcp_lms_db_run_select_query, etc.) or execute_code(). Writing scratch .py files for DB queries is wasteful and rejected by user. MCP handles complex queries (CTEs, CASE WHEN, FULL OUTER JOIN, ORDER BY) just fine.
§
Online LMS connected count discrepancy (May 13, 2026): raw `calling_status = 'Connected'` per team owner overcounts by 16 total vs user's reference (Sunil +8, Varun +2, Siddarth +6, Vishal =0). Investigated 6+ query variants — not same as unique-students, first-connection, or distinct-pairs. Unresolved; see online-lms-reporting references/team-owner-daily-metrics.md for the full investigation.
§
Online LMS `student_remarks` has undocumented columns: `lead_status`, `lead_sub_status`, `supervisor_id`, `feesamount` (lowercase variant of feesAmount). Orphaned remarks exist (counsellor_id=NULL) — 2 found on May 13. Counsellors table can have orphaned `assigned_to` references pointing to deleted counsellors (e.g., Manoj Kain → CNS-A55D5DF0 which doesn't exist). `student_remarks.supervisor_id` = 'SUP-6E3D9932' on some rows but that ID doesn't exist in counsellors table.
§
Common LMS reporting queries cheat sheet at /workspace/db-rules/common-reporting-queries-cheatsheet.md — contains 5 pre-verified queries with DB-specific overrides. When asked for these report types, load the cheatsheet and use it as the SQL reference instead of building from scratch: (1) yesterday counsellor-wise performance, (2) time slot performance, (3) lead funnel, (4) team owner remarks, (5) assignment & attempt. Key DB diffs already encoded: Online team owner filter = role='to' (exact), Regular = role ILIKE '%to%' (catches to_l3). Online ICC = "first_Icc_Date" (capital I, double-quoted), Regular ICC = first_icc_date (lowercase, no quotes). All-time-attempted rule is baked into queries 3 and 5.
§
Venv symlink breakage (May 14 2026, fixed): /workspace/.venv/bin/python3 points to /usr/bin/python3 which doesn't exist (Python is at /usr/local/bin/python3). Fix: ln -sf /usr/local/bin/python3 /workspace/.venv/bin/python3. Re-fix if MCP or terminal python silently fails.
§
College Status Report query (regular_amity_lms): For each (student_id,course_id) pair, find FIRST csj.created_at, get that CSJ's course_status as the status. Filter by first CSJ created_at in date range. NOT SCC-based. PATTERN 13 in regular_rules.md. Verified May 1-15 2026: matches 5/7 Amity universities; Gurugram Completed off by 2 (70 vs 68) — unresolved.
§
MCP lms_db fix (May 15, 2026): WSL has no /workspace/ — config.yaml paths must use /home/mohit/workspace/. Venv symlink chain: python → python3 → /usr/bin/python3 (NOT /usr/local/bin/python3). If MCP fails, check both paths first. Fix: ln -sf /usr/bin/python3 /home/mohit/workspace/.venv/bin/python3 and edit mcp_servers.lms_db paths in ~/.hermes/config.yaml.
§
Hermes WebUI Docker container fix (May 15, 2026): Container binds /home/mohit/workspace → /workspace and /home/mohit/.hermes → /home/hermeswebui/.hermes. But MCP config uses /home/mohit/workspace/ paths which don't exist inside container. Fixes needed after container recreate: (1) ln -sf /workspace /home/mohit/workspace, (2) In /workspace/.venv/bin/: rm python3 python3.12; ln -sf /usr/local/bin/python3 python3; ln -s python3 python3.12, (3) mkdir -p /root/.hermes && ln -sf /home/hermeswebui/.hermes/config.yaml /root/.hermes/config.yaml. Survives docker restart, needed after docker rm + docker run.
§
Discovered and patched hardcoded APIFY_TOKEN in scrape_60_ads.py (was hardcoded string literal, changed to os.getenv()). When creating token-free backups, always run Step 0 Pre-backup Token Scrub first — scan all .py/.js files for hardcoded token/secret assignments.