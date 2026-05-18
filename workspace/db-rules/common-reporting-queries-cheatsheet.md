# Common LMS Reporting Queries — Cheat Sheet (All 4 Databases)

> **Scope**: `regular_lms`, `regular_cgc_lms`, `regular_amity_lms`, `online_lms`
>
> **Timezone**: UTC+0 in DB. IST = UTC+5:30.
>   - May 12 IST = `'2026-05-11 18:30:00+00'` to `'2026-05-12 18:30:00+00'`
>   - Shortcut: `(created_at AT TIME ZONE 'Asia/Kolkata')::date = 'YYYY-MM-DD'`

---

## ⚡ Database-Specific Overrides — Read First

| Aspect | Online (`online_lms`) | Regular (`regular_lms` / `cgc` / `amity`) |
|--------|----------------------|--------------------------------------------|
| **Team owner filter** | `role = 'to'` (exact) | `role ILIKE '%to%'` (catches `to`, `to_l3`) |
| **ICC column** | `"first_Icc_Date"` (double-quoted, capital I) | `first_icc_date` (lowercase, no quotes) |
| **`preferred_university`** | `character varying` → use `ILIKE '%Name%'` | ARRAY type → use `= ANY(preferred_university)` |
| **Forms** | `course_status = 'Application'` | Per-DB method (see rules) |
| **Admissions** | `csj.course_status = 'Admission'` + exclude partial | Same |
| **Supervisors** | Varun, Sunil, Siddarth Kumar, Vishal Gaur | Gurvinder Singh, etc. |
| **Payment tables** | None (deposit in csj) | `payment`, `payment_orders`, `pricing_snapshots` |
| **Team owner hierarchy** | `c.assigned_to` → manager. TOs with `[default]`/NULL = self-remarks → "No Supervisor" | Same principle |

---

## 1️⃣ Yesterday Counsellor-Wise Performance Report (Online LMS)

**Metrics**: First ICC, First NI, Connected Calls, Total Students with Remarks

**Counsellor attribution**: Use `sr.counsellor_id` (who made the remark), NEVER `s.assigned_counsellor_id`.

```sql
-- Example: May 13, 2026
WITH target_date AS (
    SELECT '2026-05-13'::date AS dt
),
-- Total students with remarks per counsellor
students_remarked AS (
    SELECT sr.counsellor_id, COUNT(DISTINCT sr.student_id) AS students_with_remarks
    FROM student_remarks sr, target_date t
    WHERE (sr.created_at AT TIME ZONE 'Asia/Kolkata')::date = t.dt
      AND sr.isdisabled = false
    GROUP BY sr.counsellor_id
),
-- First Connected: earliest Connected remark per student
first_conn AS (
    SELECT fc.counsellor_id, COUNT(*) AS first_connected FROM (
        SELECT DISTINCT ON (sr_inner.student_id) sr_inner.student_id,
               sr_inner.counsellor_id, sr_inner.created_at
        FROM student_remarks sr_inner
        WHERE sr_inner.calling_status = 'Connected'
        ORDER BY sr_inner.student_id, sr_inner.created_at ASC
    ) fc, target_date t
    WHERE (fc.created_at AT TIME ZONE 'Asia/Kolkata')::date = t.dt
    GROUP BY fc.counsellor_id
),
-- First ICC: remark closest to ICC timestamp
first_icc AS (
    SELECT ir.counsellor_id, COUNT(*) AS first_icc_cnt FROM (
        SELECT DISTINCT ON (icc.student_id) icc.student_id, sr.counsellor_id
        FROM (SELECT student_id, "first_Icc_Date" AS icc_ts FROM students, target_date t
              WHERE ("first_Icc_Date" AT TIME ZONE 'Asia/Kolkata')::date = t.dt) icc
        JOIN student_remarks sr ON icc.student_id = sr.student_id
        WHERE (sr.created_at AT TIME ZONE 'Asia/Kolkata')::date = (SELECT dt FROM target_date)
        ORDER BY icc.student_id, ABS(EXTRACT(EPOCH FROM (sr.created_at - icc.icc_ts)))
    ) ir
    WHERE ir.counsellor_id IS NOT NULL
    GROUP BY ir.counsellor_id
),
-- First NI: currently NI students whose first-ever remark was on target date
first_ni AS (
    SELECT fr.counsellor_id, COUNT(*) AS first_ni_cnt FROM (
        SELECT DISTINCT ON (sr.student_id) sr.student_id, sr.counsellor_id, sr.created_at
        FROM student_remarks sr
        JOIN students s ON sr.student_id = s.student_id
        WHERE s.current_student_status = 'NotInterested'
        ORDER BY sr.student_id, sr.created_at ASC
    ) fr, target_date t
    WHERE (fr.created_at AT TIME ZONE 'Asia/Kolkata')::date = t.dt
    GROUP BY fr.counsellor_id
)
SELECT COALESCE(c.counsellor_name, sr.counsellor_id) AS counsellor,
       sr.students_with_remarks,
       COALESCE(fc.first_connected, 0) AS first_connected,
       COALESCE(fi.first_icc_cnt, 0) AS first_icc,
       COALESCE(fn.first_ni_cnt, 0) AS first_ni
FROM students_remarked sr
LEFT JOIN counsellors c ON sr.counsellor_id = c.counsellor_id
LEFT JOIN first_conn fc ON sr.counsellor_id = fc.counsellor_id
LEFT JOIN first_icc fi ON sr.counsellor_id = fi.counsellor_id
LEFT JOIN first_ni fn ON sr.counsellor_id = fn.counsellor_id
ORDER BY sr.students_with_remarks DESC;
```

> ⚠️ **First NI is often 0 for everyone** — most NI remarks are follow-ups, not the student's first-ever NI. A "first NI" only counts if the student's earliest-ever remark on the system happened on the target date AND they are currently NotInterested.

---

## 2️⃣ Time Slot Performance Report

**Metrics per slot**: New Leads, ICC Done, Calls Connected
**Slots**: Till 11 AM | 11–12 | 13–14 | 14–15 | 15–16 | 16–17 | 17–18 | 18–19 | After 7 PM

**Time slot mapping** (h = IST hour of `created_at`):
```sql
CASE
    WHEN h < 11 THEN 'Till 11 AM'
    WHEN h = 11 THEN '11-12'
    WHEN h = 13 THEN '13-14'
    WHEN h = 14 THEN '14-15'
    WHEN h = 15 THEN '15-16'
    WHEN h = 16 THEN '16-17'
    WHEN h = 17 THEN '17-18'
    WHEN h = 18 THEN '18-19'
    ELSE 'After 7 PM'
END AS time_slot
```

```sql
WITH leads AS (
    SELECT EXTRACT(HOUR FROM s.created_at AT TIME ZONE 'Asia/Kolkata')::int AS h
    FROM students s
    WHERE s.created_at >= '2026-05-11 18:30:00+00'
      AND s.created_at <  '2026-05-12 18:30:00+00'
),
icc AS (
    SELECT EXTRACT(HOUR FROM s."first_Icc_Date" AT TIME ZONE 'Asia/Kolkata')::int AS h
    FROM students s
    WHERE s."first_Icc_Date" >= '2026-05-11 18:30:00+00'
      AND s."first_Icc_Date" < '2026-05-12 18:30:00+00'
),
-- For Regular DB: use first_icc_date (lowercase, no quotes)
calls AS (
    SELECT EXTRACT(HOUR FROM sr.created_at AT TIME ZONE 'Asia/Kolkata')::int AS h
    FROM student_remarks sr
    WHERE sr.created_at >= '2026-05-11 18:30:00+00'
      AND sr.created_at <  '2026-05-12 18:30:00+00'
      AND sr.calling_status = 'Connected'
      AND sr.isdisabled = false
),
slots(h_min, h_max, slot_name) AS (
    VALUES (0, 10, 'Till 11 AM'), (11, 11, '11-12'), (13, 13, '13-14'),
           (14, 14, '14-15'), (15, 15, '15-16'), (16, 16, '16-17'),
           (17, 17, '17-18'), (18, 18, '18-19'), (19, 23, 'After 7 PM')
)
SELECT s.slot_name,
       COUNT(DISTINCT l.*) AS new_leads,
       COUNT(DISTINCT i.*) AS icc_done,
       COUNT(DISTINCT c.*) AS calls_connected
FROM slots s
LEFT JOIN leads l ON l.h BETWEEN s.h_min AND s.h_max
LEFT JOIN icc i ON i.h BETWEEN s.h_min AND s.h_max
LEFT JOIN calls c ON c.h BETWEEN s.h_min AND s.h_max
GROUP BY s.slot_name, s.h_min
ORDER BY s.h_min;
```

> ⏰ Note: `12-13` is NOT a slot in the user's schema (lunch break — no data expected).
> 💡 For Regular DB, replace `"first_Icc_Date"` with `first_icc_date` (lowercase, no quotes).

---

## 3️⃣ Lead Cohort Funnel Report

**Metrics for leads of a specific day**: Attempted, Connected, ICC, Forms, Admissions, Pre-NI + percentages.

**🔑 ALL downstream metrics = ALL-TIME (ever)**, NOT same-day. The only date boundary is `students.created_at`.

```sql
WITH cohort AS (
    SELECT student_id FROM students
    WHERE created_at >= '2026-05-12 18:30:00+00'   -- May 13 IST
      AND created_at <  '2026-05-13 18:30:00+00'
),
totals AS (SELECT COUNT(*) AS leads FROM cohort),
attempted AS (
    SELECT COUNT(DISTINCT sr.student_id) AS val
    FROM cohort c JOIN student_remarks sr ON c.student_id = sr.student_id
    WHERE sr.isdisabled = false                -- ⚠️ NO date filter on remarks
),
connected AS (
    SELECT COUNT(DISTINCT sr.student_id) AS val
    FROM cohort c JOIN student_remarks sr ON c.student_id = sr.student_id
    WHERE sr.calling_status = 'Connected' AND sr.isdisabled = false
),
icc AS (
    SELECT COUNT(*) AS val
    FROM cohort c JOIN students s ON c.student_id = s.student_id
    WHERE s."first_Icc_Date" IS NOT NULL       -- ⚠️ "ever", NOT date-filtered
),
forms AS (
    SELECT COUNT(DISTINCT csj.student_id) AS val
    FROM cohort c
    JOIN course_status_journeys csj ON c.student_id = csj.student_id
    WHERE csj.course_status = 'Application'    -- Online; see Regular override below
),
admissions AS (
    SELECT COUNT(DISTINCT csj.student_id) AS val
    FROM cohort c
    JOIN course_status_journeys csj ON c.student_id = csj.student_id
    WHERE csj.course_status IN ('Admission','Enrolled')
      AND (csj.course_status = 'Enrolled' OR csj.fee_type NOT ILIKE '%partial%')
),
pre_ni AS (
    SELECT COUNT(*) AS val
    FROM cohort c JOIN students s ON c.student_id = s.student_id
    WHERE s.current_student_status = 'NotInterested'
      AND s."first_Icc_Date" IS NULL
      AND NOT EXISTS (
        SELECT 1 FROM course_status_journeys csj
        WHERE csj.student_id = c.student_id
          AND csj.course_status IN ('Application','Admission','Enrolled')
      )
)
SELECT t.leads, a.val AS attempted, c.val AS connected,
       i.val AS icc, f.val AS forms, ad.val AS admissions, p.val AS pre_ni
FROM totals t, attempted a, connected c, icc i, forms f, admissions ad, pre_ni p;
```

**Percentages**:
- `connected%` = connected / attempted * 100
- `icc%` = icc / attempted * 100
- `lead_to_form%` = forms / leads * 100
- `form_to_admission%` = admissions / forms * 100
- `lead_to_admission%` = admissions / leads * 100
- `pre_ni%` = pre_ni / leads * 100

### 🔄 Regular DB Overrides for Funnel

| Metric | Online SQL | Regular SQL |
|--------|-----------|-------------|
| **ICC** | `"first_Icc_Date"` (double-quoted, capital I) | `first_icc_date` (lowercase, no quotes) |
| **Forms** | `csj.course_status = 'Application'` | `regular_lms`: `scas.api_sent_status = 'Proceed'` |
| | | `cgc/amity`: `csj.course_status IN ('Form Submitted – Portal Pending','Form Submitted – Completed','Walkin Completed','Walkin Marked','Exam/Interview Scheduled','Offer Letter/Results Pending','Offer Letter/Results Released','Ready For Admission')` |
| **preferred_university** | `ILIKE '%Name%'` (varchar) | `= ANY(preferred_university)` (ARRAY) |

---

## 4️⃣ Team Owner Remarks Report

**Metric**: Total remarks made by each team owner's team on a specific day.
**Definition**: Counts every remark row (effort), not distinct students (coverage).

### Online — `role = 'to'` (exact)
```sql
WITH target_remarks AS (
    SELECT sr.counsellor_id, sr.remark_id, sr.calling_status
    FROM student_remarks sr
    WHERE (sr.created_at AT TIME ZONE 'Asia/Kolkata')::date = '2026-05-13'
      AND sr.isdisabled = false
),
team_hierarchy AS (
    SELECT c.counsellor_id,
           CASE WHEN c.role = 'to' AND (c.assigned_to IS NULL OR c.assigned_to = '[default]')
                THEN 'No Supervisor'
                ELSE COALESCE(to_c.counsellor_name, 'unmapped')
           END AS team_owner
    FROM counsellors c
    LEFT JOIN counsellors to_c ON c.assigned_to = to_c.counsellor_id AND to_c.role = 'to'
)
SELECT th.team_owner,
       COUNT(mr.remark_id) AS total_remarks,
       COUNT(DISTINCT mr.counsellor_id) AS active_counsellors,
       COUNT(DISTINCT CASE WHEN mr.calling_status = 'Connected' THEN mr.remark_id END) AS connected
FROM target_remarks mr
JOIN team_hierarchy th ON mr.counsellor_id = th.counsellor_id
GROUP BY th.team_owner
ORDER BY total_remarks DESC;
```

### Regular — `role ILIKE '%to%'` (like match)
```sql
WITH target_remarks AS (
    SELECT sr.counsellor_id, sr.remark_id, sr.calling_status
    FROM student_remarks sr
    WHERE (sr.created_at AT TIME ZONE 'Asia/Kolkata')::date = '2026-05-13'
      AND sr.isdisabled = false
),
team_hierarchy AS (
    SELECT c.counsellor_id,
           CASE WHEN c.role ILIKE '%to%' AND (c.assigned_to IS NULL OR c.assigned_to = '[default]')
                THEN 'No Supervisor'
                ELSE COALESCE(to_c.counsellor_name, 'unmapped')
           END AS team_owner
    FROM counsellors c
    LEFT JOIN counsellors to_c ON c.assigned_to = to_c.counsellor_id AND to_c.role ILIKE '%to%'
)
SELECT th.team_owner,
       COUNT(mr.remark_id) AS total_remarks,
       COUNT(DISTINCT mr.counsellor_id) AS active_counsellors,
       COUNT(DISTINCT CASE WHEN mr.calling_status = 'Connected' THEN mr.remark_id END) AS connected
FROM target_remarks mr
JOIN team_hierarchy th ON mr.counsellor_id = th.counsellor_id
GROUP BY th.team_owner
ORDER BY total_remarks DESC;
```

> ⚠️ **"No Supervisor" row**: Team Owners who have no manager (`assigned_to IS NULL` or `'[default]'`) — their own personal remarks go into "No Supervisor", NOT their team's count. Only the remarks of counsellors UNDER them count toward their team total.

---

## 5️⃣ Counsellor Assignment & Attempt Report

**Metrics for leads created on a specific day**: How many assigned to each counsellor, how many of those were ever attempted.

**🔑 "Attempted" = ALL-TIME (any remark, any date)**, NOT same-day.

```sql
WITH cohort_leads AS (
    SELECT s.student_id, s.assigned_counsellor_id
    FROM students s
    WHERE s.created_at >= '2026-05-11 18:30:00+00'    -- May 12 IST
      AND s.created_at <  '2026-05-12 18:30:00+00'
      AND s.assigned_counsellor_id IS NOT NULL
),
assigned_counts AS (
    SELECT assigned_counsellor_id, COUNT(DISTINCT student_id) AS total_assigned
    FROM cohort_leads GROUP BY assigned_counsellor_id
),
attempted AS (
    SELECT c.assigned_counsellor_id,
           COUNT(DISTINCT sr.student_id) AS attempted
    FROM cohort_leads c
    LEFT JOIN student_remarks sr ON c.student_id = sr.student_id AND sr.isdisabled = false
    GROUP BY c.assigned_counsellor_id
)
SELECT COALESCE(coun.counsellor_name, ac.assigned_counsellor_id) AS counsellor,
       ac.total_assigned,
       COALESCE(a.attempted, 0) AS attempted,
       ROUND(100.0 * COALESCE(a.attempted, 0) / NULLIF(ac.total_assigned, 0), 1) AS attempt_rate_pct
FROM assigned_counts ac
LEFT JOIN attempted a ON ac.assigned_counsellor_id = a.assigned_counsellor_id
LEFT JOIN counsellors coun ON ac.assigned_counsellor_id = coun.counsellor_id
ORDER BY ac.total_assigned DESC;
```

---

## 🔄 Quick-Reference: Database Diff Table

| Feature | `online_lms` | `regular_lms` | `regular_cgc_lms` | `regular_amity_lms` |
|---------|-------------|--------------|-------------------|---------------------|
| **Team owner role filter** | `= 'to'` | `ILIKE '%to%'` | `ILIKE '%to%'` | `ILIKE '%to%'` |
| **ICC column** | `"first_Icc_Date"` | `first_icc_date` | `first_icc_date` | `first_icc_date` |
| **Form detection** | `csj.course_status = 'Application'` | `api_sent_status = 'Proceed'` | 8-pipeline statuses | 8-pipeline statuses |
| **`preferred_university` type** | varchar (`ILIKE`) | ARRAY (`= ANY()`) | ARRAY | ARRAY |
| **Supervisors** | Sunil, Varun, Siddarth, Vishal | Gurvinder Singh, Divya Chouhan, etc. | (same as regular) | (same as regular) |
| **Payment** | csj.deposit_amount only | `payment` + `payment_orders` + `pricing_snapshots` | `payment_orders` only | `payment_orders` only |
| **L3 model** | Single counsellor per student (`assigned_counsellor_l3_id`) | Course-wise L3 (`csj.assigned_l3_counsellor_id`) | Same | Same |

## 🚫 Common Pitfalls

| Pitfall | Right Way |
|---------|-----------|
| Using `s.assigned_counsellor_id` for daily metrics | Use `sr.counsellor_id` (the remarker) |
| Filtering attempts same-day | Filter by `students.created_at` only, NOT `sr.created_at` |
| ICC date-filtered in funnel | Use `IS NOT NULL` (ever), not date range |
| `role = 'to'` on Regular DB | Use `role ILIKE '%to%'` to catch `to_l3` |
| `ILIKE '%to%'` on Online DB | Use `role = 'to'` (would match `admission_to` incorrectly) |
| Confusing "leads" with "forms" | Leads = `students.created_at`. Forms = pipeline status |
| `COUNT(*)` after JOIN | Always `COUNT(DISTINCT student_id)` |
| `Counting` ICC by `current_student_status` | Use `"first_Icc_Date" IS NOT NULL` (Online) or `first_icc_date IS NOT NULL` (Regular) |
| Self-remarks of TOs merged into team count | TOs with no manager → "No Supervisor" bucket |
