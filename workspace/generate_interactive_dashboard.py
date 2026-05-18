import json

# Load the full data
with open('/workspace/full_report_data.json', 'r') as f:
    data = json.load(f)

# Helper for JSON data embedding
json_data_str = json.dumps(data)

html_template = f"""
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DegreeFYD Advanced Analytics Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Plus Jakarta Sans', sans-serif; }}
        .glass {{ background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.1); }}
        .tab-active {{ border-bottom: 3px solid #38bdf8; color: #38bdf8; }}
        .card-grad {{ background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); }}
        .hide {{ display: none; }}
        input::placeholder {{ color: #64748b; }}
    </style>
</head>
<body class="bg-[#020617] text-slate-100 min-h-screen pb-20">
    <!-- Data Source -->
    <script id="report-data" type="application/json">{json_data_str}</script>

    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8">
        <!-- Header -->
        <div class="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
            <div>
                <h1 class="text-4xl font-extrabold tracking-tight text-white">DegreeFYD <span class="text-sky-400">Pro</span></h1>
                <p class="text-slate-400 mt-1">Advanced Performance Intelligence • April 30, 2026</p>
            </div>
            <div class="flex p-1 bg-slate-800 rounded-xl">
                <button onclick="switchTrack('online')" id="btn-online" class="px-6 py-2 rounded-lg font-semibold transition-all duration-200 bg-sky-500 text-white shadow-lg">Online LMS</button>
                <button onclick="switchTrack('regular')" id="btn-regular" class="px-6 py-2 rounded-lg font-semibold transition-all duration-200 text-slate-400 hover:text-white">Regular LMS</button>
            </div>
        </div>

        <!-- Global Summary -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8" id="top-metrics">
            <!-- Dynamic Content via JS -->
        </div>

        <!-- Charts Row -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
            <div class="lg:col-span-2 glass rounded-3xl p-6">
                <div class="flex items-center justify-between mb-6">
                    <h3 class="text-xl font-bold">Revenue Distribution</h3>
                    <span class="text-xs font-semibold text-sky-400 bg-sky-400/10 px-2 py-1 rounded">LIVE TREND</span>
                </div>
                <div class="h-[300px]">
                    <canvas id="mainChart"></canvas>
                </div>
            </div>
            <div class="glass rounded-3xl p-6">
                <h3 class="text-xl font-bold mb-6">Target Completion</h3>
                <div class="h-[300px] flex items-center justify-center">
                    <canvas id="gaugeChart"></canvas>
                </div>
            </div>
        </div>

        <!-- Search & Bifurcation -->
        <div class="mb-8">
            <div class="relative max-w-md">
                <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <svg class="h-5 w-5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
                </div>
                <input type="text" id="tableSearch" onkeyup="filterTable()" class="block w-full pl-10 pr-3 py-3 border-none rounded-2xl bg-slate-800 text-slate-200 placeholder-slate-500 focus:ring-2 focus:ring-sky-500" placeholder="Search by name, college or supervisor...">
            </div>
        </div>

        <!-- Tables -->
        <div class="glass rounded-3xl overflow-hidden mb-8 shadow-2xl">
            <div class="overflow-x-auto">
                <table class="w-full text-left" id="dataTable">
                    <thead class="bg-slate-800/50">
                        <tr id="tableHeaders">
                            <!-- Dynamic -->
                        </tr>
                    </thead>
                    <tbody id="tableBody" class="divide-y divide-slate-700/50">
                        <!-- Dynamic -->
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        const rawData = JSON.parse(document.getElementById('report-data').textContent);
        let currentTrack = 'online';
        let mainChart, gaugeChart;

        function formatINR(val) {{
            if (typeof val === 'string') return val;
            return '₹' + new Intl.NumberFormat('en-IN').format(val);
        }}

        function switchTrack(track) {{
            currentTrack = track;
            document.getElementById('btn-online').className = track === 'online' ? 'px-6 py-2 rounded-lg font-semibold bg-sky-500 text-white shadow-lg' : 'px-6 py-2 rounded-lg font-semibold text-slate-400 hover:text-white';
            document.getElementById('btn-regular').className = track === 'regular' ? 'px-6 py-2 rounded-lg font-semibold bg-sky-500 text-white shadow-lg' : 'px-6 py-2 rounded-lg font-semibold text-slate-400 hover:text-white';
            render();
        }}

        function render() {{
            renderMetrics();
            renderCharts();
            renderTable();
        }}

        function renderMetrics() {{
            const container = document.getElementById('top-metrics');
            container.innerHTML = '';
            
            if (currentTrack === 'online') {{
                const gt = rawData.online.supervisor_revenue.find(r => r.Supervisor === 'Grand Total');
                const colGt = rawData.online.college_performance.find(r => r.Colleges === 'Total');
                
                const metrics = [
                    {{ label: 'Total Revenue', value: formatINR(gt.Achieved), sub: 'MTD Collection', color: 'text-sky-400' }},
                    {{ label: 'Today (FTD)', value: formatINR(gt.FTD), sub: 'Daily Collection', color: 'text-emerald-400' }},
                    {{ label: 'Total Admissions', value: colGt['MTD Admissions'], sub: 'Verified Enrollments', color: 'text-amber-400' }},
                    {{ label: 'Total Forms', value: colGt['MTD Forms'], sub: 'Interest Pipelined', color: 'text-indigo-400' }}
                ];
                
                metrics.forEach(m => {{
                    container.innerHTML += `
                        <div class="glass p-5 rounded-2xl border-l-4 border-l-sky-500">
                            <p class="text-xs font-bold text-slate-400 uppercase tracking-widest">${{m.label}}</p>
                            <h2 class="text-2xl font-black mt-2 ${{m.color}}">${{m.value}}</h2>
                            <p class="text-xs text-slate-500 mt-1">${{m.sub}}</p>
                        </div>
                    `;
                }});
            }} else {{
                const gt = rawData.regular.admissions.find(r => r.College === 'Total');
                const metrics = [
                    {{ label: 'Reg. Admissions', value: gt['Apr Ach'], sub: 'April Achievement', color: 'text-sky-400' }},
                    {{ label: 'Today (FTD)', value: gt['FTD Ach'], sub: 'Fresh Closures', color: 'text-emerald-400' }},
                    {{ label: 'Forms Managed', value: rawData.regular.forms.find(r => r.College === 'Total')['Apr Ach'], sub: 'Portal Activity', color: 'text-amber-400' }},
                    {{ label: 'Achievement %', value: gt['Apr Ach %'], sub: 'Vs Monthly Target', color: 'text-indigo-400' }}
                ];
                metrics.forEach(m => {{
                    container.innerHTML += `
                        <div class="glass p-5 rounded-2xl border-l-4 border-l-sky-500">
                            <p class="text-xs font-bold text-slate-400 uppercase tracking-widest">${{m.label}}</p>
                            <h2 class="text-2xl font-black mt-2 ${{m.color}}">${{m.value}}</h2>
                            <p class="text-xs text-slate-500 mt-1">${{m.sub}}</p>
                        </div>
                    `;
                }});
            }}
        }}

        function renderCharts() {{
            if (mainChart) mainChart.destroy();
            if (gaugeChart) gaugeChart.destroy();

            const ctxMain = document.getElementById('mainChart').getContext('2d');
            const ctxGauge = document.getElementById('gaugeChart').getContext('2d');

            if (currentTrack === 'online') {{
                const sups = rawData.online.supervisor_revenue.filter(r => r.Supervisor !== 'Grand Total');
                mainChart = new Chart(ctxMain, {{
                    type: 'bar',
                    data: {{
                        labels: sups.map(r => r.Supervisor),
                        datasets: [
                            {{ label: 'Achieved', data: sups.map(r => r.Achieved), backgroundColor: '#38bdf8', borderRadius: 8 }},
                            {{ label: 'Target', data: sups.map(r => r.Target), backgroundColor: 'rgba(255,255,255,0.1)', borderRadius: 8 }}
                        ]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{ legend: {{ display: false }} }},
                        scales: {{ y: {{ grid: {{ color: 'rgba(255,255,255,0.05)' }} }}, x: {{ grid: {{ display: false }} }} }}
                    }}
                }});

                const gt = rawData.online.supervisor_revenue.find(r => r.Supervisor === 'Grand Total');
                const pct = parseFloat(gt['Ach %']);
                gaugeChart = new Chart(ctxGauge, {{
                    type: 'doughnut',
                    data: {{
                        labels: ['Complete', 'Remaining'],
                        datasets: [{{
                            data: [pct, 100 - pct],
                            backgroundColor: ['#38bdf8', '#1e293b'],
                            borderWidth: 0,
                            circumference: 180,
                            rotation: 270
                        }}]
                    }},
                    options: {{ 
                        plugins: {{ legend: {{ display: false }} }},
                        cutout: '80%'
                    }}
                }});
            }} else {{
                const colleges = rawData.regular.admissions.filter(r => r.College !== 'Total');
                mainChart = new Chart(ctxMain, {{
                    type: 'bar',
                    data: {{
                        labels: colleges.map(r => r.College),
                        datasets: [
                            {{ label: 'Achieved', data: colleges.map(r => r['Apr Ach']), backgroundColor: '#818cf8', borderRadius: 8 }},
                            {{ label: 'Target', data: colleges.map(r => r['Apr Target']), backgroundColor: 'rgba(255,255,255,0.1)', borderRadius: 8 }}
                        ]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{ legend: {{ display: false }} }},
                        scales: {{ y: {{ grid: {{ color: 'rgba(255,255,255,0.05)' }} }}, x: {{ grid: {{ display: false }} }} }}
                    }}
                }});

                const gt = rawData.regular.admissions.find(r => r.College === 'Total');
                const pct = parseFloat(gt['Apr Ach %']);
                gaugeChart = new Chart(ctxGauge, {{
                    type: 'doughnut',
                    data: {{
                        labels: ['Complete', 'Remaining'],
                        datasets: [{{
                            data: [pct, 100 - pct],
                            backgroundColor: ['#818cf8', '#1e293b'],
                            borderWidth: 0,
                            circumference: 180,
                            rotation: 270
                        }}]
                    }},
                    options: {{ 
                        plugins: {{ legend: {{ display: false }} }},
                        cutout: '80%'
                    }}
                }});
            }}
        }}

        function renderTable() {{
            const head = document.getElementById('tableHeaders');
            const body = document.getElementById('tableBody');
            head.innerHTML = '';
            body.innerHTML = '';

            if (currentTrack === 'online') {{
                const cols = ['Supervisor', 'Counsellor', 'Target', 'Achieved', 'Ach %', 'FTD'];
                cols.forEach(c => head.innerHTML += `<th class="px-6 py-4 font-bold text-xs uppercase tracking-wider text-slate-400">${{c}}</th>`);
                
                rawData.online.counsellor_revenue.forEach(r => {{
                    const isTotal = r.Supervisor.includes('Total') || r.Supervisor === 'Grand Total';
                    const rowClass = isTotal ? 'bg-slate-800/30 font-bold' : 'hover:bg-slate-800/20';
                    body.innerHTML += `
                        <tr class="${{rowClass}} transition-colors">
                            <td class="px-6 py-4">${{r.Supervisor}}</td>
                            <td class="px-6 py-4 text-sky-400">${{r.Counsellor || '-'}}</td>
                            <td class="px-6 py-4">${{formatINR(r.Target)}}</td>
                            <td class="px-6 py-4 font-semibold">${{formatINR(r.Achieved)}}</td>
                            <td class="px-6 py-4">
                                <div class="flex items-center gap-2">
                                    <span class="text-xs font-mono">${{r['Ach %']}}</span>
                                    <div class="w-16 h-1 bg-slate-700 rounded-full overflow-hidden">
                                        <div class="h-full bg-sky-500" style="width: ${{r['Ach %']}}"></div>
                                    </div>
                                </div>
                            </td>
                            <td class="px-6 py-4 text-emerald-400">${{formatINR(r.FTD)}}</td>
                        </tr>
                    `;
                }});
            }} else {{
                const cols = ['College', 'YTD', 'Apr Tgt', 'Apr Ach', 'Ach %', 'Week Tgt', 'Week Ach', 'FTD'];
                cols.forEach(c => head.innerHTML += `<th class="px-6 py-4 font-bold text-xs uppercase tracking-wider text-slate-400">${{c}}</th>`);
                
                rawData.regular.admissions.forEach(r => {{
                    const isTotal = r.College === 'Total';
                    const rowClass = isTotal ? 'bg-slate-800/30 font-bold' : 'hover:bg-slate-800/20';
                    body.innerHTML += `
                        <tr class="${{rowClass}} transition-colors">
                            <td class="px-6 py-4 font-semibold">${{r.College}}</td>
                            <td class="px-6 py-4 text-slate-400">${{r['YTD Ach']}}</td>
                            <td class="px-6 py-4">${{r['Apr Target']}}</td>
                            <td class="px-6 py-4 text-sky-400">${{r['Apr Ach']}}</td>
                            <td class="px-6 py-4 text-xs font-mono">${{r['Apr Ach %']}}</td>
                            <td class="px-6 py-4">${{r['Week 5 Target']}}</td>
                            <td class="px-6 py-4 text-indigo-400">${{r['Week 5 Ach']}}</td>
                            <td class="px-6 py-4 text-emerald-400 font-bold">${{r['FTD Ach']}}</td>
                        </tr>
                    `;
                }});
            }}
        }}

        function filterTable() {{
            const input = document.getElementById('tableSearch');
            const filter = input.value.toUpperCase();
            const table = document.getElementById('dataTable');
            const tr = table.getElementsByTagName('tr');

            for (let i = 1; i < tr.length; i++) {{
                let found = false;
                const tds = tr[i].getElementsByTagName('td');
                for (let j = 0; j < tds.length; j++) {{
                    if (tds[j].innerHTML.toUpperCase().indexOf(filter) > -1) {{
                        found = true;
                        break;
                    }}
                }}
                tr[i].style.display = found ? "" : "none";
            }}
        }}

        render();
    </script>
</body>
</html>
"""

with open('/workspace/interactive_dashboard.html', 'w') as f:
    f.write(html_template)

print("Interactive dashboard generated.")
