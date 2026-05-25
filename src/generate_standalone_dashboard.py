
#!/usr/bin/env python3
"""
Generate a self-contained HTML dashboard with all analytics embedded.

This script creates a standalone HTML file that includes:
- All CSV data embedded as JSON
- All JSON data embedded
- Markdown content converted to HTML
- Plotly.js visualizations
- 8-tab structure matching the Streamlit dashboard
- Glassmorphic dark theme styling
- Interactive tabs using pure HTML/CSS/JavaScript
"""

import json
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional
import html


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "output"


def load_csv_as_json(filename: str) -> Optional[List[Dict[str, Any]]]:
    """Load CSV file and convert to JSON-serializable list of dicts."""
    path = OUTPUT / filename
    if not path.exists():
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return None


def load_json_file(filename: str) -> Optional[Dict[str, Any]]:
    """Load JSON file."""
    path = OUTPUT / filename
    if not path.exists():
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return None


def load_markdown(filename: str) -> Optional[str]:
    """Load markdown file."""
    path = OUTPUT / filename
    if not path.exists():
        return None
    try:
        return path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return None


def load_html_file(filename: str) -> Optional[str]:
    """Load HTML file."""
    path = OUTPUT / filename
    if not path.exists():
        return None
    try:
        return path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return None


def markdown_to_html(md_text: str) -> str:
    """Simple markdown to HTML converter for basic formatting."""
    if not md_text:
        return ""
    
    lines = md_text.split('\n')
    html_lines = []
    in_code_block = False
    code_block_lines = []
    
    for line in lines:
        # Code blocks
        if line.strip().startswith('```'):
            if in_code_block:
                # End code block
                html_lines.append('<pre><code>' + html.escape('\n'.join(code_block_lines)) + '</code></pre>')
                code_block_lines = []
                in_code_block = False
            else:
                # Start code block
                in_code_block = True
            continue
        
        if in_code_block:
            code_block_lines.append(line)
            continue
        
        # Headers
        if line.startswith('#### '):
            html_lines.append(f'<h4>{html.escape(line[5:])}</h4>')
        elif line.startswith('### '):
            html_lines.append(f'<h3>{html.escape(line[4:])}</h3>')
        elif line.startswith('## '):
            html_lines.append(f'<h2>{html.escape(line[3:])}</h2>')
        elif line.startswith('# '):
            html_lines.append(f'<h1>{html.escape(line[2:])}</h1>')
        # Lists
        elif line.strip().startswith('- ') or line.strip().startswith('* '):
            html_lines.append(f'<li>{html.escape(line.strip()[2:])}</li>')
        # Bold
        elif '**' in line:
            line = line.replace('**', '<strong>', 1).replace('**', '</strong>', 1)
            html_lines.append(f'<p>{line}</p>')
        # Empty lines
        elif line.strip() == '':
            html_lines.append('<br>')
        # Regular paragraphs
        else:
            html_lines.append(f'<p>{html.escape(line)}</p>')
    
    return '\n'.join(html_lines)


def generate_html_dashboard() -> str:
    """Generate the complete standalone HTML dashboard."""
    
    # Load all data files
    print("Loading data files...")
    incidents_scored = load_csv_as_json("incidents_scored.csv")
    platform_quality = load_csv_as_json("platform_quality_metrics.csv")
    missing_fields = load_csv_as_json("missing_field_summary.csv")
    ai_recommendations = load_csv_as_json("ai_recommendations.csv")
    qa_alerts = load_csv_as_json("qa_fidelity_alerts.csv")
    
    executive_summary = load_markdown("executive_summary.md")
    log_standards_md = load_markdown("log_standards.md")
    business_impact_gaps = load_markdown("business_impact_gaps.md")
    long_running_report = load_markdown("long_running_report.md")
    
    business_impact_stats = load_json_file("business_impact_stats.json")
    long_running_stats = load_json_file("long_running_stats.json")
    log_standards_json = load_json_file("log_standards.json")
    
    qa_report_html = load_html_file("qa_fidelity_report.html")
    
    # Convert markdown to HTML
    executive_summary_html = markdown_to_html(executive_summary) if executive_summary else ""
    log_standards_html = markdown_to_html(log_standards_md) if log_standards_md else ""
    business_impact_gaps_html = markdown_to_html(business_impact_gaps) if business_impact_gaps else ""
    long_running_report_html = markdown_to_html(long_running_report) if long_running_report else ""
    
    # Generate the HTML
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AIOps Log Fidelity Intelligence Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', sans-serif;
            background: radial-gradient(circle at top left, #121927, #080b12);
            color: #e2e8f0;
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        h1 {{
            background: -webkit-linear-gradient(45deg, #00f2fe, #4facfe);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2.5rem;
            font-weight: 600;
            letter-spacing: -0.02em;
            margin-bottom: 30px;
            padding-bottom: 20px;
        }}
        
        h2, h3, h4 {{
            color: #f8fafc;
            font-weight: 600;
            letter-spacing: -0.02em;
            margin: 20px 0 10px 0;
        }}
        
        /* KPI Metrics Strip */
        .kpi-strip {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .metric-card {{
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.08);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-radius: 16px;
            padding: 24px;
            text-align: center;
            transition: transform 0.3s ease, box-shadow 0.3s ease, border 0.3s ease;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        }}
        
        .metric-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0, 242, 254, 0.15);
            border: 1px solid rgba(0, 242, 254, 0.3);
        }}
        
        .metric-value {{
            font-size: 36px;
            font-weight: 700;
            background: -webkit-linear-gradient(45deg, #e2e8f0, #ffffff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 8px;
        }}
        
        .metric-label {{
            font-size: 13px;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-weight: 600;
        }}
        
        /* Tabs */
        .tabs {{
            background: rgba(0,0,0,0.2);
            padding: 10px;
            border-radius: 12px;
            display: flex;
            gap: 10px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }}
        
        .tab {{
            border-radius: 8px;
            padding: 12px 20px;
            background: transparent;
            border: 1px solid transparent;
            color: #94a3b8;
            cursor: pointer;
            transition: all 0.2s ease;
            font-size: 14px;
            font-weight: 500;
        }}
        
        .tab:hover {{
            color: #00f2fe;
        }}
        
        .tab.active {{
            background: rgba(0, 242, 254, 0.15);
            color: #00f2fe;
            font-weight: 600;
            border: 1px solid rgba(0, 242, 254, 0.3);
        }}
        
        /* Tab Content */
        .tab-content {{
            display: none;
        }}
        
        .tab-content.active {{
            display: block;
            animation: fadeIn 0.3s ease;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        /* Content Sections */
        .content-section {{
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 20px;
        }}
        
        .grid-2 {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        .chart-container {{
            background: rgba(0, 0, 0, 0.2);
            border-radius: 12px;
            padding: 20px;
            min-height: 400px;
        }}
        
        /* Info Box */
        .info-box {{
            background: rgba(0, 242, 254, 0.05);
            padding: 20px;
            border-radius: 12px;
            border-left: 4px solid #00f2fe;
            margin: 20px 0;
        }}
        
        .warning-box {{
            background: rgba(255, 165, 0, 0.05);
            padding: 20px;
            border-radius: 12px;
            border-left: 4px solid #f6ad55;
            margin: 20px 0;
        }}
        
        /* Code blocks */
        pre {{
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            padding: 16px;
            overflow-x: auto;
            margin: 10px 0;
        }}
        
        code {{
            font-family: 'Courier New', monospace;
            font-size: 13px;
            color: #84fab0;
        }}
        
        /* Tables */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        th {{
            background: rgba(0, 242, 254, 0.1);
            color: #00f2fe;
            font-weight: 600;
        }}
        
        tr:hover {{
            background: rgba(255, 255, 255, 0.02);
        }}
        
        /* Expander */
        .expander {{
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            margin: 10px 0;
            overflow: hidden;
        }}
        
        .expander-header {{
            padding: 15px 20px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background 0.2s ease;
        }}
        
        .expander-header:hover {{
            background: rgba(255, 255, 255, 0.03);
        }}
        
        .expander-content {{
            padding: 0 20px;
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease, padding 0.3s ease;
        }}
        
        .expander.open .expander-content {{
            max-height: 2000px;
            padding: 20px;
        }}
        
        .expander-icon {{
            transition: transform 0.3s ease;
        }}
        
        .expander.open .expander-icon {{
            transform: rotate(180deg);
        }}
        
        /* Select dropdown */
        select {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            padding: 10px 15px;
            color: #e2e8f0;
            font-family: 'Inter', sans-serif;
            font-size: 14px;
            cursor: pointer;
            margin: 10px 0;
            min-width: 300px;
        }}
        
        select:focus {{
            outline: none;
            border-color: #00f2fe;
        }}
        
        option {{
            background: #1a202c;
            color: #e2e8f0;
        }}
        
        /* Iframe */
        iframe {{
            width: 100%;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            background: white;
        }}
        
        .not-ready {{
            background: rgba(255, 165, 0, 0.1);
            border: 1px solid rgba(255, 165, 0, 0.3);
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            color: #f6ad55;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>⚡ AIOps Log Fidelity Intelligence</h1>
        
        <!-- KPI Strip -->
        <div class="kpi-strip" id="kpi-strip"></div>
        
        <!-- Tabs -->
        <div class="tabs">
            <div class="tab active" onclick="switchTab(0)">🎯 Executive</div>
            <div class="tab" onclick="switchTab(1)">💻 Platform Quality</div>
            <div class="tab" onclick="switchTab(2)">⚠️ Log Gaps</div>
            <div class="tab" onclick="switchTab(3)">🤖 AIOps Recommendations</div>
            <div class="tab" onclick="switchTab(4)">📜 Standards Schema</div>
            <div class="tab" onclick="switchTab(5)">💸 Business Impact</div>
            <div class="tab" onclick="switchTab(6)">⏱️ Long-Running</div>
            <div class="tab" onclick="switchTab(7)">📧 QA Alerts</div>
        </div>
        
        <!-- Tab Contents -->
        <div id="tab-0" class="tab-content active"></div>
        <div id="tab-1" class="tab-content"></div>
        <div id="tab-2" class="tab-content"></div>
        <div id="tab-3" class="tab-content"></div>
        <div id="tab-4" class="tab-content"></div>
        <div id="tab-5" class="tab-content"></div>
        <div id="tab-6" class="tab-content"></div>
        <div id="tab-7" class="tab-content"></div>
    </div>
    
    <script>
        // Embedded Data
        const DATA = {{
            incidents_scored: {json.dumps(incidents_scored)},
            platform_quality: {json.dumps(platform_quality)},
            missing_fields: {json.dumps(missing_fields)},
            ai_recommendations: {json.dumps(ai_recommendations)},
            qa_alerts: {json.dumps(qa_alerts)},
            business_impact_stats: {json.dumps(business_impact_stats)},
            long_running_stats: {json.dumps(long_running_stats)},
            log_standards_json: {json.dumps(log_standards_json)},
            executive_summary_html: {json.dumps(executive_summary_html)},
            log_standards_html: {json.dumps(log_standards_html)},
            business_impact_gaps_html: {json.dumps(business_impact_gaps_html)},
            long_running_report_html: {json.dumps(long_running_report_html)},
            qa_report_html: {json.dumps(qa_report_html)}
        }};
        
        // Color palette
        const COLORS = ["#00f2fe", "#4facfe", "#f093fb", "#fb6f92", "#feca57", "#48dbfb", "#ff9ff3", "#54a0ff", "#00d2d3"];
        
        // Plotly layout template
        const PLOTLY_LAYOUT = {{
            plot_bgcolor: 'rgba(0,0,0,0)',
            paper_bgcolor: 'rgba(0,0,0,0)',
            font: {{ color: '#e2e8f0', family: 'Inter' }},
            margin: {{ t: 40, r: 20, b: 40, l: 60 }}
        }};
        
        // Tab switching
        function switchTab(index) {{
            document.querySelectorAll('.tab').forEach((tab, i) => {{
                tab.classList.toggle('active', i === index);
            }});
            document.querySelectorAll('.tab-content').forEach((content, i) => {{
                content.classList.toggle('active', i === index);
            }});
        }}
        
        // Toggle expander
        function toggleExpander(id) {{
            const expander = document.getElementById(id);
            expander.classList.toggle('open');
        }}
        
        // Initialize KPIs
        function initKPIs() {{
            const incidents = DATA.incidents_scored;
            if (!incidents || incidents.length === 0) {{
                document.getElementById('kpi-strip').innerHTML = '<div class="not-ready">No incident data available. Run the pipeline first.</div>';
                return;
            }}
            
            const totalIncidents = incidents.length;
            const avgScore = (incidents.reduce((sum, inc) => sum + parseFloat(inc.Log_Fidelity_Score || 0), 0) / totalIncidents).toFixed(1);
            const poorCount = incidents.filter(inc => ['Poor', 'Needs Improvement'].includes(inc.Quality_Bucket)).length;
            const platforms = new Set(incidents.map(inc => inc.Platform)).size;
            const systemAreas = new Set(incidents.map(inc => inc.System_Area)).size;
            
            document.getElementById('kpi-strip').innerHTML = `
                <div class="metric-card">
                    <div class="metric-value">${{totalIncidents.toLocaleString()}}</div>
                    <div class="metric-label">Total Incidents</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${{avgScore}}/100</div>
                    <div class="metric-label">Avg Fidelity Score</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${{poorCount.toLocaleString()}}</div>
                    <div class="metric-label">Critical Gaps</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${{platforms}}</div>
                    <div class="metric-label">Monitored Platforms</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${{systemAreas}}</div>
                    <div class="metric-label">System Areas</div>
                </div>
            `;
        }}
        
        // Tab 0: Executive
        function initExecutiveTab() {{
            const incidents = DATA.incidents_scored;
            if (!incidents || incidents.length === 0) {{
                document.getElementById('tab-0').innerHTML = '<div class="not-ready">No incident data available.</div>';
                return;
            }}
            
            let html = '<div class="grid-2">';
            html += '<div class="chart-container" id="chart-quality-dist"></div>';
            html += '<div class="chart-container" id="chart-sunburst"></div>';
            html += '</div>';
            
            if (DATA.executive_summary_html) {{
                html += `<div class="content-section"><h3>Executive Narrative</h3>${{DATA.executive_summary_html}}</div>`;
            }}
            
            html += `
                <div class="expander" id="expander-raw-data">
                    <div class="expander-header" onclick="toggleExpander('expander-raw-data')">
                        <span><strong>View Raw Incident Data</strong></span>
                        <span class="expander-icon">▼</span>
                    </div>
                    <div class="expander-content">
                        <div style="overflow-x: auto;">
                            <table>
                                <thead>
                                    <tr>
                                        <th>Incident ID</th>
                                        <th>Platform</th>
                                        <th>System Area</th>
                                        <th>Assignment Group</th>
                                        <th>Fidelity Score</th>
                                        <th>Quality Bucket</th>
                                        <th>Lifecycle</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${{incidents.slice(0, 100).map(inc => `
                                        <tr>
                                            <td>${{inc.Incident_ID || '–'}}</td>
                                            <td>${{inc.Platform || '–'}}</td>
                                            <td>${{inc.System_Area || '–'}}</td>
                                            <td>${{inc.Assignment_Group || '–'}}</td>
                                            <td>${{inc.Log_Fidelity_Score || '–'}}</td>
                                            <td>${{inc.Quality_Bucket || '–'}}</td>
                                            <td>${{inc.Ticket_Lifecycle || '–'}}</td>
                                        </tr>
                                    `).join('')}}
                                </tbody>
                            </table>
                            ${{incidents.length > 100 ? '<p style="text-align: center; color: #94a3b8; margin-top: 10px;">Showing first 100 of ' + incidents.length + ' incidents</p>' : ''}}
                        </div>
                    </div>
                </div>
            `;
            
            document.getElementById('tab-0').innerHTML = html;
            
            // Chart 1: Quality Distribution
            const qualityBuckets = {{}};
            const platformColors = {{}};
            incidents.forEach(inc => {{
                const bucket = inc.Quality_Bucket || 'Unknown';
                const platform = inc.Platform || 'Unknown';
                if (!qualityBuckets[bucket]) qualityBuckets[bucket] = {{}};
                qualityBuckets[bucket][platform] = (qualityBuckets[bucket][platform] || 0) + 1;
            }});
            
            const bucketOrder = ['Poor', 'Needs Improvement', 'Good', 'Excellent'];
            const traces = [];
            const platforms = [...new Set(incidents.map(inc => inc.Platform))];
            
            platforms.forEach((platform, idx) => {{
                traces.push({{
                    x: bucketOrder,
                    y: bucketOrder.map(bucket => qualityBuckets[bucket]?.[platform] || 0),
                    name: platform,
                    type: 'bar',
                    marker: {{ color: COLORS[idx % COLORS.length] }}
                }});
            }});
            
            Plotly.newPlot('chart-quality-dist', traces, {{
                ...PLOTLY_LAYOUT,
                title: 'Log Quality Distribution',
                barmode: 'group',
                xaxis: {{ title: 'Quality Bucket' }},
                yaxis: {{ title: 'Count' }}
            }});
            
            // Chart 2: Sunburst
            const sunburstData = [];
            const platformSystemCounts = {{}};
            
            incidents.forEach(inc => {{
                const platform = inc.Platform || 'Unknown';
                const system = inc.System_Area || 'Unknown';
                const key = `${{platform}}|${{system}}`;
                platformSystemCounts[key] = (platformSystemCounts[key] || 0) + 1;
            }});
            
            const labels = ['Total'];
            const parents = [''];
            const values = [incidents.length];
            
            platforms.forEach(platform => {{
                labels.push(platform);
                parents.push('Total');
                const platformCount = incidents.filter(inc => inc.Platform === platform).length;
                values.push(platformCount);
            }});
            
            Object.entries(platformSystemCounts).forEach(([key, count]) => {{
                const [platform, system] = key.split('|');
                labels.push(system);
                parents.push(platform);
                values.push(count);
            }});
            
            Plotly.newPlot('chart-sunburst', [{{
                type: 'sunburst',
                labels: labels,
                parents: parents,
                values: values,
                marker: {{ colors: COLORS }},
                branchvalues: 'total'
            }}], {{
                ...PLOTLY_LAYOUT,
                title: 'Incident Distribution by System Area',
                margin: {{ t: 40, r: 0, b: 0, l: 0 }}
            }});
        }}
        
        // Tab 1: Platform Quality
        function initPlatformQualityTab() {{
            const platform = DATA.platform_quality;
            if (!platform || platform.length === 0) {{
                document.getElementById('tab-1').innerHTML = '<div class="not-ready">Platform quality metrics are currently generating or missing.</div>';
                return;
            }}
            
            let html = '<div class="grid-2">';
            html += '<div class="chart-container" id="chart-platform-fidelity"></div>';
            html += '<div class="chart-container" id="chart-platform-mttr"></div>';
            html += '</div>';
            
            html += `
                <div class="expander" id="expander-platform-data">
                    <div class="expander-header" onclick="toggleExpander('expander-platform-data')">
                        <span><strong>Platform Metrics Data</strong></span>
                        <span class="expander-icon">▼</span>
                    </div>
                    <div class="expander-content">
                        <div style="overflow-x: auto;">
                            <table>
                                <thead>
                                    <tr>
                                        ${{Object.keys(platform[0]).map(key => `<th>${{key}}</th>`).join('')}}
                                    </tr>
                                </thead>
                                <tbody>
                                    ${{platform.map(row => `
                                        <tr>
                                            ${{Object.values(row).map(val => `<td>${{val}}</td>`).join('')}}
                                        </tr>
                                    `).join('')}}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            `;
            
            document.getElementById('tab-1').innerHTML = html;
            
            // Chart 1: Fidelity Score by Platform
            Plotly.newPlot('chart-platform-fidelity', [{{
                x: platform.map(p => p.Platform),
                y: platform.map(p => parseFloat(p.Average_Log_Fidelity_Score || 0)),
                type: 'bar',
                marker: {{ color: COLORS }},
                text: platform.map(p => parseFloat(p.Average_Log_Fidelity_Score || 0).toFixed(1)),
                textposition: 'outside'
            }}], {{
                ...PLOTLY_LAYOUT,
                title: 'Fidelity Score by Platform',
                xaxis: {{ title: 'Platform' }},
                yaxis: {{ title: 'Average Log Fidelity Score', range: [0, 100] }},
                showlegend: false
            }});
            
            // Chart 2: MTTR by Platform
            if (platform[0].Average_MTTR_Minutes) {{
                Plotly.newPlot('chart-platform-mttr', [{{
                    x: platform.map(p => p.Platform),
                    y: platform.map(p => parseFloat(p.Average_MTTR_Minutes || 0)),
                    type: 'bar',
                    marker: {{ color: COLORS.slice().reverse() }},
                    text: platform.map(p => parseFloat(p.Average_MTTR_Minutes || 0).toFixed(0)),
                    textposition: 'outside'
                }}], {{
                    ...PLOTLY_LAYOUT,
                    title: 'MTTR Impact by Platform (minutes)',
                    xaxis: {{ title: 'Platform' }},
                    yaxis: {{ title: 'Average MTTR (minutes)' }},
                    showlegend: false
                }});
            }}
        }}
        
        // Tab 2: Log Gaps
        function initLogGapsTab() {{
            const missing = DATA.missing_fields;
            if (!missing || missing.length === 0) {{
                document.getElementById('tab-2').innerHTML = '<div class="not-ready">Missing field summary is currently generating or missing.</div>';
                return;
            }}
            
            let html = '<div class="content-section">';
            html += '<h3>Critical Signal Gaps across all Logs</h3>';
            html += '<div class="chart-container" id="chart-missing-fields"></div>';
            html += '</div>';
            
            document.getElementById('tab-2').innerHTML = html;
            
            // Sort by missing rate descending
            const sorted = missing.sort((a, b) => parseFloat(b.Missing_Rate || 0) - parseFloat(a.Missing_Rate || 0));
            
            Plotly.newPlot('chart-missing-fields', [{{
                x: sorted.map(m => m.Signal),
                y: sorted.map(m => parseFloat(m.Missing_Rate || 0) * 100),
                type: 'bar',
                marker: {{
                    color: sorted.map(m => parseFloat(m.Missing_Rate || 0)),
                    colorscale: 'Purples',
                    showscale: true
                }},
                text: sorted.map(m => (parseFloat(m.Missing_Rate || 0) * 100).toFixed(1) + '%'),
                textposition: 'outside'
            }}], {{
                ...PLOTLY_LAYOUT,
                title: 'Missing Rate by Signal',
                xaxis: {{ title: 'Signal', tickangle: -45 }},
                yaxis: {{ title: 'Missing Rate (%)', tickformat: '.0f' }}
            }});
        }}
        
        // Tab 3: AI Recommendations
        function initRecommendationsTab() {{
            const recommendations = DATA.ai_recommendations;
            if (!recommendations || recommendations.length === 0 || !recommendations[0].Segment_ID) {{
                document.getElementById('tab-3').innerHTML = '<div class="not-ready">AI recommendations are currently generating or missing.</div>';
                return;
            }}
            
            let html = '<div class="content-section">';
            html += '<h3>LLM Log Remediation Strategies</h3>';
            html += '<label for="segment-select">Select Target Cluster:</label><br>';
            html += '<select id="segment-select" onchange="updateRecommendation()">';
            recommendations.forEach(rec => {{
                html += `<option value="${{rec.Segment_ID}}">${{rec.Segment_ID}}</option>`;
            }});
            html += '</select>';
            html += '<div id="recommendation-details"></div>';
            html += '</div>';
            
            document.getElementById('tab-3').innerHTML = html;
            updateRecommendation();
        }}
        
        function updateRecommendation() {{
            const select = document.getElementById('segment-select');
            const segmentId = select.value;
            const rec = DATA.ai_recommendations.find(r => r.Segment_ID === segmentId);
            
            if (!rec) return;
            
            let html = '<div style="margin-top: 20px;">';
            html += '<div class="grid-2" style="grid-template-columns: repeat(3, 1fr);">';
            html += `
                <div class="metric-card">
                    <div class="metric-value">${{rec.Incident_Count || '–'}}</div>
                    <div class="metric-label">Incidents Affected</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${{rec.Average_Log_Fidelity_Score || '–'}} / 100</div>
                    <div class="metric-label">Cluster Score</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${{rec.Average_MTTR_Minutes || '–'}} min</div>
                    <div class="metric-label">MTTR Drag</div>
                </div>
            `;
            html += '</div>';
            
            html += `
                <div class="info-box">
                    <h4 style="margin-top: 0;">Assessment</h4>
                    <p style="font-size: 15px; line-height: 1.6;">${{rec.Segment_Assessment || 'No assessment available'}}</p>
                </div>
            `;
            
            html += '<div class="grid-2">';
            html += `
                <div>
                    <p><strong>RCA Gaps:</strong></p>
                    <p style="color: #f8fafc;">${{rec.RCA_Gaps || 'N/A'}}</p>
                    <br>
                    <p><strong>Expected MTTR Impact:</strong></p>
                    <p style="color: #84fab0;">${{rec.Expected_MTTR_Impact || 'N/A'}}</p>
                </div>
                <div>
                    <p><strong>Automation Gaps:</strong></p>
                    <p style="color: #ffb199;">${{rec.Automation_Gaps || 'N/A'}}</p>
                    <br>
                    <p><strong>Logging Standard Changes:</strong></p>
                    <p style="color: #f8fafc;">${{rec.Logging_Standard_Changes || 'N/A'}}</p>
                </div>
            `;
            html += '</div>';
            
            html += '<br><p><strong>Improved Log Template Schema:</strong></p>';
            html += `<pre><code>${{rec.Improved_Log_Template || 'N/A'}}</code></pre>`;
            html += '</div>';
            
            document.getElementById('recommendation-details').innerHTML = html;
        }}
        
        // Tab 4: Log Standards
        function initLogStandardsTab() {{
            let html = '<div class="content-section">';
            html += '<h3>AIOps Prescriptive Logging Standards</h3>';
            
            if (DATA.log_standards_html) {{
                html += `<div class="content-section">${{DATA.log_standards_html}}</div>`;
            }} else {{
                html += '<div class="not-ready">Log standards are currently generating or missing.</div>';
            }}
            
            if (DATA.log_standards_json) {{
                html += `
                    <div class="expander" id="expander-log-json">
                        <div class="expander-header" onclick="toggleExpander('expander-log-json')">
                            <span><strong>Machine-Readable JSON Configuration Schema</strong></span>
                            <span class="expander-icon">▼</span>
                        </div>
                        <div class="expander-content">
                            <pre><code>${{JSON.stringify(DATA.log_standards_json, null, 2)}}</code></pre>
                        </div>
                    </div>
                `;
            }}
            
            html += '</div>';
            document.getElementById('tab-4').innerHTML = html;
        }}
        
        // Tab 5: Business Impact
        function initBusinessImpactTab() {{
            const stats = DATA.business_impact_stats;
            
            let html = '<div class="content-section">';
            html += '<h3>Business Impact & Lifecycle Funnel</h3>';
            
            if (stats) {{
                html += '<div class="kpi-strip" style="grid-template-columns: repeat(4, 1fr);">';
                html += `
                    <div class="metric-card">
                        <div class="metric-value">${{(stats.total_tickets || 0).toLocaleString()}}</div>
                        <div class="metric-label">Total Tickets</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${{(stats.auto_resolved_noise_count || 0).toLocaleString()}} (${{stats.noise_rate_pct || 0}}%)</div>
                        <div class="metric-label">Bot Noise</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${{(stats.actionable_alert_count || 0).toLocaleString()}} (${{stats.actionable_rate_pct || 0}}%)</div>
                        <div class="metric-label">Actionable Alert</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${{(stats.blind_spot_count || 0).toLocaleString()}} (${{stats.blind_spot_rate_pct || 0}}%)</div>
                        <div class="metric-label">Blind Spots</div>
                    </div>
                `;
                html += '</div>';
                
                html += '<div class="grid-2">';
                html += '<div class="chart-container" id="chart-funnel"></div>';
                html += '<div class="chart-container" id="chart-blind-spots"></div>';
                html += '</div>';
            }} else {{
                html += '<div class="not-ready">Lifecycle stats are currently generating or missing.</div>';
            }}
            
            if (DATA.business_impact_gaps_html) {{
                html += `
                    <div class="expander open" id="expander-biz-gaps">
                        <div class="expander-header" onclick="toggleExpander('expander-biz-gaps')">
                            <span><strong>Read Full Diagnostic Narrative</strong></span>
                            <span class="expander-icon">▼</span>
                        </div>
                        <div class="expander-content">
                            ${{DATA.business_impact_gaps_html}}
                        </div>
                    </div>
                `;
            }}
            
            html += '</div>';
            document.getElementById('tab-5').innerHTML = html;
            
            if (stats) {{
                // Funnel chart
                Plotly.newPlot('chart-funnel', [{{
                    type: 'funnel',
                    y: ['Total Raised', 'Bot Noise (Auto-Closed)', 'Actionable Alerts (Human Intervened)'],
                    x: [
                        stats.total_tickets || 0,
                        stats.auto_resolved_noise_count || 0,
                        stats.actionable_alert_count || 0
                    ],
                    marker: {{ color: ['#00f2fe', '#4facfe', '#fb6f92'] }}
                }}], {{
                    ...PLOTLY_LAYOUT,
                    title: 'Alert Lifecycle Funnel'
                }});
                
                // Blind spots chart
                if (stats.top_blind_spot_groups && stats.top_blind_spot_groups.length > 0) {{
                    const topBlindSpots = stats.top_blind_spot_groups.slice(0, 5);
                    Plotly.newPlot('chart-blind-spots', [{{
                        type: 'bar',
                        y: topBlindSpots.map(bs => bs.group),
                        x: topBlindSpots.map(bs => bs.unmonitored_business_tickets),
                        orientation: 'h',
                        marker: {{
                            color: topBlindSpots.map(bs => bs.unmonitored_business_tickets),
                            colorscale: 'Sunset',
                            showscale: true
                        }}
                    }}], {{
                        ...PLOTLY_LAYOUT,
                        title: 'Top Monitoring Blind Spots',
                        xaxis: {{ title: 'Unmonitored Business Tickets' }},
                        yaxis: {{ title: 'Assignment Group' }}
                    }});
                }}
            }}
        }}
        
        // Tab 6: Long-Running
        function initLongRunningTab() {{
            const stats = DATA.long_running_stats;
            
            let html = '<div class="content-section">';
            html += '<h3>Long-Running Incident Heatmap</h3>';
            
            if (stats && stats.clusters) {{
                html += '<div class="grid-2" style="grid-template-columns: repeat(2, 1fr);">';
                html += `
                    <div class="metric-card">
                        <div class="metric-value">${{(stats.p80_threshold_minutes || 0).toFixed(0)}} min</div>
                        <div class="metric-label">P80 MTTR Threshold</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${{(stats.total_long_running || 0).toLocaleString()}}</div>
                        <div class="metric-label">Long-Running Incidents</div>
                    </div>
                `;
                html += '</div>';
                
                html += '<div class="chart-container" id="chart-long-running"></div>';
            }} else {{
                html += '<div class="not-ready">Long-running stats are currently generating or missing.</div>';
            }}
            
            if (DATA.long_running_report_html) {{
                html += `
                    <div class="expander open" id="expander-lr-report">
                        <div class="expander-header" onclick="toggleExpander('expander-lr-report')">
                            <span><strong>Read LLM Gap Assessment Report</strong></span>
                            <span class="expander-icon">▼</span>
                        </div>
                        <div class="expander-content">
                            ${{DATA.long_running_report_html}}
                        </div>
                    </div>
                `;
            }}
            
            html += '</div>';
            document.getElementById('tab-6').innerHTML = html;
            
            if (stats && stats.clusters) {{
                const clusters = stats.clusters;
                Plotly.newPlot('chart-long-running', [{{
                    x: clusters.map(c => c.average_log_fidelity_score),
                    y: clusters.map(c => c.average_mttr_minutes),
                    mode: 'markers',
                    type: 'scatter',
                    marker: {{
                        size: clusters.map(c => Math.sqrt(c.incident_count) * 5),
                        color: COLORS,
                        opacity: 0.7
                    }},
                    text: clusters.map(c => c.cluster_id),
                    hovertemplate: '<b>%{{text}}</b><br>Fidelity: %{{x:.1f}}<br>MTTR: %{{y:.0f}} min<extra></extra>'
                }}], {{
                    ...PLOTLY_LAYOUT,
                    title: 'Fidelity vs Resolution Time (Actionable Alerts Only)',
                    xaxis: {{ title: 'Average Log Fidelity Score' }},
                    yaxis: {{ title: 'Average MTTR (minutes)' }}
                }});
            }}
        }}
        
        // Tab 7: QA Alerts
        function initQATab() {{
            const qa = DATA.qa_alerts;
            if (!qa || qa.length === 0) {{
                document.getElementById('tab-7').innerHTML = '<div class="not-ready">QA fidelity report is currently generating or missing.</div>';
                return;
            }}
            
            let html = '<div class="content-section">';
            html += '<h3>QA Platform Email Alerts</h3>';
            html += '<div class="grid-2">';
            html += '<div class="chart-container" id="chart-rag-pie"></div>';
            html += '<div class="chart-container" id="chart-team-fidelity"></div>';
            html += '</div>';
            
            html += `
                <div class="expander" id="expander-qa-data">
                    <div class="expander-header" onclick="toggleExpander('expander-qa-data')">
                        <span><strong>View QA Alert Details</strong></span>
                        <span class="expander-icon">▼</span>
                    </div>
                    <div class="expander-content">
                        <div style="overflow-x: auto;">
                            <table>
                                <thead>
                                    <tr>
                                        ${{Object.keys(qa[0]).map(key => `<th>${{key}}</th>`).join('')}}
                                    </tr>
                                </thead>
                                <tbody>
                                    ${{qa.map(row => `
                                        <tr>
                                            ${{Object.values(row).map(val => `<td>${{val}}</td>`).join('')}}
                                        </tr>
                                    `).join('')}}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            `;
            
            html += '</div>';
            document.getElementById('tab-7').innerHTML = html;
            
            // RAG Status Pie Chart
            const ragCounts = {{}};
            qa.forEach(row => {{
                const status = row.RAG_Status || 'Unknown';
                ragCounts[status] = (ragCounts[status] || 0) + 1;
            }});
            
            const ragLabels = Object.keys(ragCounts);
            const ragValues = Object.values(ragCounts);
            const ragColorMap = {{'Red': '#ff0844', 'Amber': '#f6ad55', 'Green': '#84fab0'}};
            
            Plotly.newPlot('chart-rag-pie', [{{
                type: 'pie',
                labels: ragLabels,
                values: ragValues,
                hole: 0.6,
                marker: {{ colors: ragLabels.map(label => ragColorMap[label] || '#999') }}
            }}], {{
                ...PLOTLY_LAYOUT,
                title: 'RAG Status Distribution'
            }});
            
            // Team Fidelity Bar Chart
            const teamFidelity = qa.sort((a, b) => parseFloat(a.Avg_Log_Fidelity_Score || 0) - parseFloat(b.Avg_Log_Fidelity_Score || 0));
            const uniqueTeams = [...new Set(qa.map(row => row.Assignment_Group))];
            
            Plotly.newPlot('chart-team-fidelity', [{{
                x: teamFidelity.map(row => row.Assignment_Group),
                y: teamFidelity.map(row => parseFloat(row.Avg_Log_Fidelity_Score || 0)),
                type: 'bar',
                marker: {{
                    color: teamFidelity.map(row => {{
                        const score = parseFloat(row.Avg_Log_Fidelity_Score || 0);
                        if (row.RAG_Status === 'Red') return '#ff0844';
                        if (row.RAG_Status === 'Amber') return '#f6ad55';
                        return '#84fab0';
                    }})
                }},
                text: teamFidelity.map(row => parseFloat(row.Avg_Log_Fidelity_Score || 0).toFixed(1)),
                textposition: 'outside'
            }}], {{
                ...PLOTLY_LAYOUT,
                title: 'Team Fidelity Scoring Matrix',
                xaxis: {{ title: 'Assignment Group', tickangle: -30 }},
                yaxis: {{ title: 'Avg Log Fidelity Score', range: [0, 100] }},
                showlegend: false
            }});
        }}
        
        // Initialize all tabs on page load
        document.addEventListener('DOMContentLoaded', function() {{
            initKPIs();
            initExecutiveTab();
            initPlatformQualityTab();
            initLogGapsTab();
            initRecommendationsTab();
            initLogStandardsTab();
            initBusinessImpactTab();
            initLongRunningTab();
            initQATab();
        }});
    </script>
</body>
</html>
"""
    
    return html_content


def main():
    """Main entry point."""
    try:
        print("Generating standalone HTML dashboard...")
        html = generate_html_dashboard()
        
        output_path = OUTPUT / "dashboard.html"
        output_path.write_text(html, encoding='utf-8')
        
        print(f"✓ Dashboard generated successfully!")
        print(f"  File: {output_path}")
        print(f"  Size: {len(html) / 1024:.1f} KB")
        print(f"\nOpen in browser: file:///{output_path}")
        
    except Exception as e:
        print(f"✗ Error generating dashboard: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
