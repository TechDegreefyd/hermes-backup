const fs = require('fs');
const path = require('path');
const { Client } = require('pg');
const WORKDIR='/home/mohit/workspace';
function loadEnv(file){for(const line of fs.readFileSync(file,'utf8').split(/\r?\n/)){const m=line.match(/^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$/); if(!m)continue; let v=m[2]; if((v.startsWith('"')&&v.endsWith('"'))||(v.startsWith("'")&&v.endsWith("'"))) v=v.slice(1,-1); if(!(m[1] in process.env)) process.env[m[1]]=v;}}
loadEnv(path.join(WORKDIR,'.env'));
const QUERY = `SELECT scass.*, sla.utm_campaign FROM student_college_api_sent_status scass LEFT JOIN (SELECT DISTINCT ON (student_id) student_id, utm_campaign FROM student_lead_activities ORDER BY student_id, created_at DESC) sla ON scass.student_id = sla.student_id WHERE DATE(scass.created_at AT TIME ZONE 'Asia/Kolkata') = '2026-03-02';`;
async function main(){
 const client=new Client({host:process.env.REGULAR_LMS_DB_HOST, port:Number(process.env.REGULAR_LMS_DB_PORT||5432), database:process.env.REGULAR_LMS_DB_NAME||'regular_lms', user:process.env.REGULAR_LMS_DB_USER, password:process.env.REGULAR_LMS_DB_PASSWORD});
 await client.connect();
 try{
  const r=await client.query(QUERY);
  const counts={}; for(const row of r.rows){const c=row.college_name || '(blank/null)'; counts[c]=(counts[c]||0)+1;}
  console.log('RAW QUERY COLLEGE COUNTS'); console.log(JSON.stringify(counts,null,2));
  const byStatus={}; for(const row of r.rows){const c=row.college_name||'(blank/null)'; const key=c+' | '+row.sent_type+' | '+row.api_sent_status; byStatus[key]=(byStatus[key]||0)+1;} console.log('BY STATUS'); console.log(JSON.stringify(byStatus,null,2));
  // Check if student table has applied college for the same query students where college_name is blank or for all.
  const ids=[...new Set(r.rows.map(x=>x.student_id).filter(x=>x!==null&&x!==undefined))];
  const sr=await client.query(`SELECT student_id, college_for_applied, source FROM students WHERE student_id = ANY($1)`, [ids]);
  const smap=new Map(sr.rows.map(x=>[String(x.student_id), x]));
  const fallback={}; for(const row of r.rows){const s=smap.get(String(row.student_id)); const c=row.college_name || (s&&s.college_for_applied) || '(blank/null)'; fallback[c]=(fallback[c]||0)+1;}
  console.log('WITH STUDENTS.COLLEGE_FOR_APPLIED FALLBACK COUNTS (investigation only, not original report query)'); console.log(JSON.stringify(fallback,null,2));
  const missingRows=r.rows.filter(row=>!row.college_name).map(row=>({student_id:row.student_id, college_name:row.college_name, fallback:smap.get(String(row.student_id))?.college_for_applied, status:row.api_sent_status, sent_type:row.sent_type, utm_campaign:row.utm_campaign}));
  console.log('BLANK COLLEGE ROWS WITH FALLBACK'); console.log(JSON.stringify(missingRows,null,2));
 } finally {await client.end();}
}
main().catch(e=>{console.error(e); process.exit(1);});
