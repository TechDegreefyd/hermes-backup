const fs = require('fs');
const path = require('path');
const { Client } = require('pg');

const WORKDIR = '/home/mohit/workspace';
const REPORT_DATE = '2026-03-02';
const WHATSAPP_GROUP = '120363426619711887@g.us';

function loadEnv(file) {
  const txt = fs.readFileSync(file, 'utf8');
  for (const line of txt.split(/\r?\n/)) {
    const m = line.match(/^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$/);
    if (!m) continue;
    let v = m[2];
    if ((v.startsWith('"') && v.endsWith('"')) || (v.startsWith("'") && v.endsWith("'"))) v = v.slice(1, -1);
    if (!(m[1] in process.env)) process.env[m[1]] = v;
  }
}
loadEnv(path.join(WORKDIR, '.env'));

// USER-CORRECTED SOURCE QUERY. Do not add DB filters/joins beyond this query.
const QUERY = `SELECT 
    scass.*,
    sla.utm_campaign
FROM student_college_api_sent_status scass
LEFT JOIN (
    SELECT DISTINCT ON (student_id)
        student_id,
        utm_campaign
    FROM student_lead_activities
    ORDER BY student_id, created_at DESC
) sla
ON scass.student_id = sla.student_id
WHERE DATE(scass.created_at AT TIME ZONE 'Asia/Kolkata') = '2026-03-02';`;

function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}
function csvEsc(v) {
  if (v instanceof Date) v = v.toISOString();
  v = String(v ?? '');
  return /[",\n\r]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v;
}
function normStatus(status) {
  const s = String(status ?? '').trim().toLowerCase();
  if (s === 'proceed') return 'proceed';
  if (s.includes('technical issues') || s.includes('failed')) return 'failed';
  if (s === 'do not proceed' || s.includes('dnp') || s.includes('do not')) return 'dnp';
  return 'other';
}
function normSent(sentType) {
  const s = String(sentType ?? '').trim().toLowerCase();
  if (s === 'auto') return 'auto';
  if (s === 'manual') return 'manual';
  return 'other';
}
function blankCounts() { return {proceed:0, failed:0, dnp:0, other:0}; }
function pct(n, d) { return d ? (n/d*100).toFixed(1)+'%' : '0.0%'; }

async function fetchRows() {
  const client = new Client({
    host: process.env.REGULAR_LMS_DB_HOST,
    port: Number(process.env.REGULAR_LMS_DB_PORT || 5432),
    database: process.env.REGULAR_LMS_DB_NAME || process.env.REGULAR_LMS_DB_DATABASE || 'regular_lms',
    user: process.env.REGULAR_LMS_DB_USER,
    password: process.env.REGULAR_LMS_DB_PASSWORD,
    ssl: process.env.REGULAR_LMS_DB_SSL === 'true' ? {rejectUnauthorized:false} : undefined,
  });
  await client.connect();
  try {
    const res = await client.query(QUERY);
    return res.rows;
  } finally {
    await client.end();
  }
}

function writeCsv(rows, outPath) {
  if (!rows.length) { fs.writeFileSync(outPath, 'No data found\n'); return; }
  const keys = Object.keys(rows[0]);
  const lines = [keys.map(csvEsc).join(',')];
  for (const r of rows) lines.push(keys.map(k => csvEsc(r[k])).join(','));
  fs.writeFileSync(outPath, lines.join('\n'), 'utf8');
}

function summarize(rows) {
  const data = new Map();
  const seenStudents = new Set();
  let duplicateStudentRecords = 0;
  for (const r of rows) {
    const college = r.college_name || r.college || r.college_for_applied || 'Unknown';
    if (!data.has(college)) data.set(college, {auto: blankCounts(), manual: blankCounts(), other: blankCounts(), campaigns: new Map()});
    const d = data.get(college);
    d[normSent(r.sent_type)][normStatus(r.api_sent_status)]++;
    if (r.student_id !== null && r.student_id !== undefined) {
      if (seenStudents.has(String(r.student_id))) duplicateStudentRecords++;
      seenStudents.add(String(r.student_id));
    }
    const camp = String(r.utm_campaign || 'No UTM').trim() || 'No UTM';
    d.campaigns.set(camp, (d.campaigns.get(camp) || 0) + 1);
  }
  return {data, uniqueStudents: seenStudents.size, duplicateStudentRecords};
}

function buildHtml(rows, summary) {
  const totals = {auto: blankCounts(), manual: blankCounts(), other: blankCounts()};
  const body = [];
  const colleges = [...summary.data.keys()].sort();
  for (const college of colleges) {
    const d = summary.data.get(college);
    for (const sent of ['auto','manual','other']) for (const st of ['proceed','failed','dnp','other']) totals[sent][st] += d[sent][st];
    const a = d.auto, m = d.manual, o = d.other;
    const totalProceed = a.proceed + m.proceed + o.proceed;
    const totalFailed = a.failed + m.failed + o.failed;
    const totalDnp = a.dnp + m.dnp + o.dnp;
    const totalOther = a.other + m.other + o.other;
    const collegeTotal = Object.values(a).reduce((x,y)=>x+y,0) + Object.values(m).reduce((x,y)=>x+y,0) + Object.values(o).reduce((x,y)=>x+y,0);
    const topCampaigns = [...d.campaigns.entries()].sort((x,y)=>y[1]-x[1]).slice(0,3).map(([k,v]) => `${esc(k)} <b>${v}</b>`).join('<br>');
    body.push(`<tr><td class="college">${esc(college)}</td><td>${a.proceed}</td><td>${a.failed}</td><td>${a.dnp}</td><td>${a.other}</td><td>${m.proceed}</td><td>${m.failed}</td><td>${m.dnp}</td><td>${m.other}</td><td>${totalProceed}</td><td>${totalFailed}</td><td>${totalDnp}</td><td>${totalOther}</td><td class="total">${collegeTotal}</td><td class="campaign">${topCampaigns}</td></tr>`);
  }
  const autoTotal = Object.values(totals.auto).reduce((x,y)=>x+y,0);
  const manualTotal = Object.values(totals.manual).reduce((x,y)=>x+y,0);
  const otherTotal = Object.values(totals.other).reduce((x,y)=>x+y,0);
  const grandTotal = autoTotal + manualTotal + otherTotal;
  const gp = totals.auto.proceed + totals.manual.proceed + totals.other.proceed;
  const gf = totals.auto.failed + totals.manual.failed + totals.other.failed;
  const gd = totals.auto.dnp + totals.manual.dnp + totals.other.dnp;
  const go = totals.auto.other + totals.manual.other + totals.other.other;
  const generated = new Date().toLocaleString('en-IN', {timeZone: 'Asia/Kolkata', dateStyle: 'medium', timeStyle: 'short'});
  return `<!doctype html><html><head><meta charset="utf-8"><title>Correct Recon Report ${REPORT_DATE}</title><style>
body{margin:0;background:#0f172a;color:#e2e8f0;font-family:Inter,Arial,sans-serif;padding:24px}.wrap{max-width:1400px;margin:auto}h1{margin:0;color:#38bdf8;font-size:26px}.sub{color:#94a3b8;margin:8px 0 22px}.cards{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:20px}.card{background:#1e293b;border:1px solid #334155;border-radius:14px;padding:14px}.label{font-size:11px;text-transform:uppercase;color:#94a3b8;letter-spacing:.08em}.val{font-size:26px;font-weight:800;margin-top:6px;color:white}table{width:100%;border-collapse:separate;border-spacing:0;background:#1e293b;border:1px solid #334155;border-radius:14px;overflow:hidden}th{position:sticky;top:0;background:#020617;color:#93c5fd;font-size:11px;text-transform:uppercase;padding:10px 8px;border-bottom:1px solid #334155}td{padding:10px 8px;border-bottom:1px solid #334155;border-right:1px solid #334155;text-align:center;font-size:13px}.college{text-align:left;font-weight:700;color:#f8fafc;min-width:250px;background:#172033}.campaign{text-align:left;font-size:11px;color:#cbd5e1;min-width:260px}.total{font-weight:800;color:#38bdf8}.grand td{background:#020617;color:#38bdf8;font-weight:800}pre{white-space:pre-wrap;background:#020617;border:1px solid #334155;border-radius:12px;padding:14px;color:#cbd5e1;font-size:12px}.note{color:#fbbf24;font-weight:700}</style></head><body><div class="wrap"><h1>Correct Regular LMS Recon Report</h1><div class="sub">Date: ${REPORT_DATE} IST | Generated: ${esc(generated)} | Source: exactly the user-corrected query below.</div><div class="cards"><div class="card"><div class="label">Query Records</div><div class="val">${grandTotal}</div></div><div class="card"><div class="label">Unique Students</div><div class="val">${summary.uniqueStudents}</div></div><div class="card"><div class="label">Auto Total</div><div class="val">${autoTotal}</div></div><div class="card"><div class="label">Manual Total</div><div class="val">${manualTotal}</div></div><div class="card"><div class="label">Proceed Rate</div><div class="val">${pct(gp, grandTotal)}</div></div></div><table><thead><tr><th rowspan="2">College</th><th colspan="4">Auto Recon</th><th colspan="4">Manual Recon</th><th colspan="4">Total Status</th><th rowspan="2">Total</th><th rowspan="2">Top UTM Campaigns</th></tr><tr><th>Proceed</th><th>Failed</th><th>DNP</th><th>Other</th><th>Proceed</th><th>Failed</th><th>DNP</th><th>Other</th><th>Proceed</th><th>Failed</th><th>DNP</th><th>Other</th></tr></thead><tbody>${body.join('')}<tr class="grand"><td class="college">Grand Total</td><td>${totals.auto.proceed}</td><td>${totals.auto.failed}</td><td>${totals.auto.dnp}</td><td>${totals.auto.other}</td><td>${totals.manual.proceed}</td><td>${totals.manual.failed}</td><td>${totals.manual.dnp}</td><td>${totals.manual.other}</td><td>${gp}</td><td>${gf}</td><td>${gd}</td><td>${go}</td><td>${grandTotal}</td><td>Duplicate student records in query: ${summary.duplicateStudentRecords}</td></tr></tbody></table><h2>Exact Query Used</h2><pre>${esc(QUERY)}</pre><div class="sub note">No branded/source filters, no extra DB query, no replacement logic. This report is built only from the returned rows of the query above.</div></div></body></html>`;
}

async function sendWhatsappDocument(filePath, caption) {
  const token = process.env.WHAPI_TOKEN;
  if (!token) return {skipped: true, reason: 'WHAPI_TOKEN missing'};
  const b64 = fs.readFileSync(filePath).toString('base64');
  const media = `data:text/html;name=${path.basename(filePath)};base64,${b64}`;
  const res = await fetch('https://gate.whapi.cloud/messages/document', {
    method: 'POST',
    headers: {'accept': 'application/json', 'authorization': `Bearer ${token}`, 'content-type': 'application/json'},
    body: JSON.stringify({to: WHATSAPP_GROUP, media, caption})
  });
  const text = await res.text();
  return {status_code: res.status, text: text.slice(0, 1000)};
}

(async function main() {
  const rows = await fetchRows();
  const summary = summarize(rows);
  const htmlPath = path.join(WORKDIR, `Correct_Recon_Report_${REPORT_DATE}.html`);
  const csvPath = path.join(WORKDIR, `Correct_Recon_Raw_Query_Data_${REPORT_DATE}.csv`);
  writeCsv(rows, csvPath);
  fs.writeFileSync(htmlPath, buildHtml(rows, summary), 'utf8');
  const caption = `✅ Correct Regular LMS Recon Report\n📅 Date: ${REPORT_DATE} IST\nSource: only the corrected query provided by Mohit.\nRecords: ${rows.length} | Unique Students: ${summary.uniqueStudents}`;
  const wa = await sendWhatsappDocument(htmlPath, caption);
  console.log(JSON.stringify({query_records: rows.length, unique_students: summary.uniqueStudents, duplicate_student_records: summary.duplicateStudentRecords, html_report: htmlPath, raw_csv: csvPath, whatsapp_result: wa}, null, 2));
})().catch(err => { console.error(err); process.exit(1); });
