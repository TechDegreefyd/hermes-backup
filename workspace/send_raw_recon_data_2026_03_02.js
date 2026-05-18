const fs = require('fs');
const path = require('path');
const { Client } = require('pg');
const WORKDIR='/home/mohit/workspace';
function loadEnv(file){for(const line of fs.readFileSync(file,'utf8').split(/\r?\n/)){const m=line.match(/^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$/); if(!m)continue; let v=m[2]; if((v.startsWith('"')&&v.endsWith('"'))||(v.startsWith("'")&&v.endsWith("'"))) v=v.slice(1,-1); if(!(m[1] in process.env)) process.env[m[1]]=v;}}
loadEnv(path.join(WORKDIR,'.env'));
const QUERY = `SELECT scass.*, sla.utm_campaign FROM student_college_api_sent_status scass LEFT JOIN (SELECT DISTINCT ON (student_id) student_id, utm_campaign FROM student_lead_activities ORDER BY student_id, created_at DESC) sla ON scass.student_id = sla.student_id WHERE DATE(scass.created_at AT TIME ZONE 'Asia/Kolkata') = '2026-03-02';`;
function csvEsc(v){ if(v instanceof Date) v=v.toISOString(); v=String(v??''); return /[",\n\r]/.test(v)?'"'+v.replace(/"/g,'""')+'"':v; }
async function sendDoc(filePath, mime, caption){
 const token=process.env.WHAPI_TOKEN; const b64=fs.readFileSync(filePath).toString('base64');
 const media=`data:${mime};name=${path.basename(filePath)};base64,${b64}`;
 const res=await fetch('https://gate.whapi.cloud/messages/document',{method:'POST',headers:{accept:'application/json',authorization:`Bearer ${token}`,'content-type':'application/json'},body:JSON.stringify({to:'120363426619711887@g.us',media,caption})});
 return {status_code:res.status, text:(await res.text()).slice(0,500)};
}
async function main(){
 const client=new Client({host:process.env.REGULAR_LMS_DB_HOST, port:Number(process.env.REGULAR_LMS_DB_PORT||5432), database:process.env.REGULAR_LMS_DB_NAME||'regular_lms', user:process.env.REGULAR_LMS_DB_USER, password:process.env.REGULAR_LMS_DB_PASSWORD});
 await client.connect();
 let rows=[]; try { rows=(await client.query(QUERY)).rows; } finally { await client.end(); }
 const keys=Object.keys(rows[0]||{});
 const csvPath=path.join(WORKDIR,'RAW_ONLY_Correct_Recon_Query_2026-03-02.csv');
 fs.writeFileSync(csvPath, [keys.map(csvEsc).join(','), ...rows.map(r=>keys.map(k=>csvEsc(r[k])).join(','))].join('\n'), 'utf8');
 const collegeCounts={}; const campaignCounts={}; const collegeStatus={};
 for(const r of rows){
  const c=r.college_name || '(blank/null)'; collegeCounts[c]=(collegeCounts[c]||0)+1;
  const camp=(r.utm_campaign||'No UTM').trim()||'No UTM'; campaignCounts[camp]=(campaignCounts[camp]||0)+1;
  const key=`${c} || ${r.sent_type||''} || ${r.api_sent_status||''}`; collegeStatus[key]=(collegeStatus[key]||0)+1;
 }
 const auditPath=path.join(WORKDIR,'RAW_ONLY_Correct_Recon_Query_Audit_2026-03-02.json');
 fs.writeFileSync(auditPath, JSON.stringify({query_used:QUERY, total_records:rows.length, distinct_college_name_count:Object.keys(collegeCounts).length, college_counts:collegeCounts, college_status_counts:collegeStatus, top_utm_campaigns:Object.fromEntries(Object.entries(campaignCounts).sort((a,b)=>b[1]-a[1]).slice(0,50))},null,2),'utf8');
 const wa1=await sendDoc(csvPath,'text/csv',`Raw data only - Correct Recon Query\nDate: 2026-03-02 IST\nRows: ${rows.length}\nNote: raw query returns ${Object.keys(collegeCounts).length} college_name values.`);
 const wa2=await sendDoc(auditPath,'application/json',`Audit for missing college check\nRaw query returned college_name count: ${Object.keys(collegeCounts).length}`);
 console.log(JSON.stringify({csvPath,auditPath,total_records:rows.length, college_counts:collegeCounts, whatsapp_csv:wa1, whatsapp_audit:wa2},null,2));
}
main().catch(e=>{console.error(e); process.exit(1);});
