import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "output"

# ── Custom CSS Injection ────────────────────────────────────────────────────────
CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }
    
    /* Dark Theme Background */
    .stApp {
        background: radial-gradient(circle at top left, #121927, #080b12);
        color: #e2e8f0;
    }

    /* Custom Header Styling */
    h1, h2, h3, h4 {
        color: #f8fafc !important;
        font-weight: 600;
        letter-spacing: -0.02em;
    }
    
    h1 {
        background: -webkit-linear-gradient(45deg, #00f2fe, #4facfe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        padding-bottom: 20px;
    }

    /* Glassmorphic Metric Cards */
    .metric-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        transition: transform 0.3s ease, box-shadow 0.3s ease, border 0.3s ease;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 30px rgba(0, 242, 254, 0.15);
        border: 1px solid rgba(0, 242, 254, 0.3);
    }
    
    .metric-value {
        font-size: 36px;
        font-weight: 700;
        background: -webkit-linear-gradient(45deg, #e2e8f0, #ffffff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 8px;
    }
    
    .metric-label {
        font-size: 13px;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 600;
    }

    /* Tab Styling */
    div[data-baseweb="tab-list"] {
        background: rgba(0,0,0,0.2);
        padding: 10px;
        border-radius: 12px;
        gap: 10px;
    }
    div[data-baseweb="tab"] {
        border-radius: 8px !important;
        padding: 8px 16px !important;
        background: transparent !important;
        border: none !important;
        color: #94a3b8 !important;
        transition: all 0.2s ease;
    }
    div[aria-selected="true"] {
        background: rgba(0, 242, 254, 0.15) !important;
        color: #00f2fe !important;
        font-weight: 600 !important;
        border: 1px solid rgba(0, 242, 254, 0.3) !important;
    }

    /* DataFrame Styling */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    /* Expander Styling */
    .streamlit-expanderHeader {
        background: rgba(255,255,255,0.02) !important;
        border-radius: 8px !important;
        border: 1px solid rgba(255,255,255,0.05) !important;
    }

    /* Divider */
    hr {
        border-color: rgba(255,255,255,0.1) !important;
    }
</style>
"""

# Premium Color Palette for Plotly
COLORS = ["#00f2fe", "#4facfe", "#f093fb", "#f5576c", "#5ee7df", "#b490ca", "#ff0844", "#ffb199", "#84fab0"]

def create_metric_card(label: str, value: str) -> str:
    return f"""
    <div class="metric-card">
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """

def load_csv(name: str) -> pd.DataFrame | None:
    path = OUTPUT / name
    if not path.exists():
        return None
    try:
        return pd.read_csv(path)
    except Exception:
        return None

def load_json(name: str) -> dict | None:
    path = OUTPUT / name
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

def load_md(name: str) -> str | None:
    path = OUTPUT / name
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")

def not_ready(label: str) -> None:
    st.info(f"**{label}** data is currently generating or missing. Check back shortly.")


# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="AIOps Log Fidelity", layout="wide", page_icon="⚡")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
st.markdown("<h1>⚡ AIOps Log Fidelity Intelligence</h1>", unsafe_allow_html=True)

scored_path = OUTPUT / "incidents_scored.csv"
if not scored_path.exists():
    st.warning("Run `python run_pipeline.py --input <path_to_incidents>` first.")
    st.stop()

df = pd.read_csv(scored_path)

# ── Top-level KPI strip ────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
k1.markdown(create_metric_card("Total Incidents", f"{len(df):,}"), unsafe_allow_html=True)
k2.markdown(create_metric_card("Avg Fidelity Score", f"{df['Log_Fidelity_Score'].mean():.1f}/100"), unsafe_allow_html=True)
poor_count = df["Quality_Bucket"].isin(["Poor", "Needs Improvement"]).sum()
k3.markdown(create_metric_card("Critical Gaps", f"{poor_count:,}"), unsafe_allow_html=True)
k4.markdown(create_metric_card("Monitored Platforms", f"{df['Platform'].nunique()}"), unsafe_allow_html=True)
k5.markdown(create_metric_card("System Areas", f"{df['System_Area'].nunique()}"), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Tabs ───────────────────────────────────────────────────────────────────────
tabs = st.tabs([
    "🎯 Executive", "💻 Platform Quality", "⚠️ Log Gaps", "🤖 AIOps Recommendations",
    "📜 Standards Schema", "💸 Business Impact", "⏱️ Long-Running", "📧 QA Alerts"
])

# ── Tab 1: Executive ───────────────────────────────────────────────────────────
with tabs[0]:
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Log Quality Distribution")
        fig = px.histogram(df, x="Quality_Bucket", color="Platform", barmode="group",
                           category_orders={"Quality_Bucket": ["Poor", "Needs Improvement", "Good", "Excellent"]},
                           color_discrete_sequence=COLORS, template="plotly_dark")
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Incident Distribution by System Area")
        # Ensure we only plot areas that exist
        area_df = df.groupby(["Platform", "System_Area"]).size().reset_index(name="Count")
        fig2 = px.sunburst(area_df, path=["Platform", "System_Area"], values="Count",
                           color="Platform", color_discrete_sequence=COLORS, template="plotly_dark")
        fig2.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=0, l=0, r=0, b=0))
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Executive Narrative")
    summary_md = load_md("executive_summary.md")
    if summary_md:
        st.markdown(f"<div style='background:rgba(255,255,255,0.02); padding: 20px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1);'>{summary_md}</div>", unsafe_allow_html=True)
    else:
        not_ready("Executive Summary")

    with st.expander("View Raw Incident Data"):
        st.dataframe(df[["Incident_ID", "Platform", "System_Area", "Assignment_Group", "Log_Fidelity_Score", "Quality_Bucket", "Ticket_Lifecycle"]], use_container_width=True)


# ── Tab 2: Platform Quality ────────────────────────────────────────────────────
with tabs[1]:
    platform = load_csv("platform_quality_metrics.csv")
    if platform is not None:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Fidelity Score by Platform")
            fig = px.bar(platform, x="Platform", y="Average_Log_Fidelity_Score",
                         color="Platform", text_auto=True,
                         color_discrete_sequence=COLORS, template="plotly_dark")
            fig.update_layout(showlegend=False, yaxis_range=[0, 100], plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            if "Average_MTTR_Minutes" in platform.columns:
                st.subheader("MTTR Impact by Platform (minutes)")
                fig2 = px.bar(platform, x="Platform", y="Average_MTTR_Minutes",
                              color="Platform", text_auto=True,
                              color_discrete_sequence=COLORS[::-1], template="plotly_dark") # Reverse colors
                fig2.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig2, use_container_width=True)
                
        with st.expander("Platform Metrics Data"):
            st.dataframe(platform, use_container_width=True)
    else:
        not_ready("Platform Quality Metrics")

# ── Tab 3: Missing Fields ──────────────────────────────────────────────────────
with tabs[2]:
    missing = load_csv("missing_field_summary.csv")
    if missing is not None:
        st.subheader("Critical Signal Gaps across all Logs")
        fig = px.bar(missing.sort_values("Missing_Rate", ascending=False),
                     x="Signal", y="Missing_Rate", text_auto=".1%",
                     color="Missing_Rate", color_continuous_scale="Purp", template="plotly_dark")
        fig.update_layout(yaxis_tickformat=".0%", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        not_ready("Missing Field Summary")

# ── Tab 4: Recommendations ─────────────────────────────────────────────────────
with tabs[3]:
    recommendations = load_csv("ai_recommendations.csv")
    if recommendations is not None and {"Segment_ID", "Segment_Assessment"}.issubset(recommendations.columns):
        st.subheader("LLM Log Remediation Strategies")
        selected = st.selectbox("Select Target Cluster:", recommendations["Segment_ID"].tolist())
        row = recommendations[recommendations["Segment_ID"] == selected].iloc[0]
        
        c1, c2, c3 = st.columns(3)
        c1.markdown(create_metric_card("Incidents Affected", str(row.get("Incident_Count", "–"))), unsafe_allow_html=True)
        c2.markdown(create_metric_card("Cluster Score", f"{row.get('Average_Log_Fidelity_Score', '–')} / 100"), unsafe_allow_html=True)
        c3.markdown(create_metric_card("MTTR Drag", f"{row.get('Average_MTTR_Minutes', '–')} min"), unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style="background: rgba(0, 242, 254, 0.05); padding: 24px; border-radius: 12px; border-left: 4px solid #00f2fe; margin-bottom: 24px;">
            <h4 style="margin-top:0;">Assessment</h4>
            <p style="font-size: 15px; line-height: 1.6;">{row["Segment_Assessment"]}</p>
        </div>
        """, unsafe_allow_html=True)
        
        c_left, c_right = st.columns(2)
        with c_left:
            st.markdown(f"**RCA Gaps:**<br><span style='color:#f8fafc'>{row.get('RCA_Gaps', '')}</span>", unsafe_allow_html=True)
            st.markdown(f"<br>**Expected MTTR Impact:**<br><span style='color:#84fab0'>{row.get('Expected_MTTR_Impact', '')}</span>", unsafe_allow_html=True)
        with c_right:
            st.markdown(f"**Automation Gaps:**<br><span style='color:#ffb199'>{row.get('Automation_Gaps', '')}</span>", unsafe_allow_html=True)
            st.markdown(f"<br>**Logging Standard Changes:**<br><span style='color:#f8fafc'>{row.get('Logging_Standard_Changes', '')}</span>", unsafe_allow_html=True)
            
        st.markdown("<br>**Improved Log Template Schema:**", unsafe_allow_html=True)
        st.code(row.get("Improved_Log_Template", ""), language="json")
    else:
        not_ready("AI Recommendations")

# ── Tab 5: Log Standards ───────────────────────────────────────────────────────
with tabs[4]:
    st.subheader("AIOps Prescriptive Logging Standards")
    log_std_md = load_md("log_standards.md")
    log_std_json = load_json("log_standards.json")

    if log_std_md:
        st.markdown(f"<div style='background:rgba(255,255,255,0.02); padding: 20px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1);'>{log_std_md}</div>", unsafe_allow_html=True)
    else:
        not_ready("Log Standards")

    if log_std_json:
        with st.expander("Machine-Readable JSON Configuration Schema"):
            st.json(log_std_json)

# ── Tab 6: Alert Lifecycle & Business Impact ──────────────────────────────────
with tabs[5]:
    st.subheader("Business Impact & Lifecycle Funnel")
    biz_stats = load_json("business_impact_stats.json")
    biz_gaps_md = load_md("business_impact_gaps.md")

    if biz_stats:
        m1, m2, m3, m4 = st.columns(4)
        m1.markdown(create_metric_card("Total Tickets", str(biz_stats.get("total_tickets", "–"))), unsafe_allow_html=True)
        m2.markdown(create_metric_card("Bot Noise", f"{biz_stats.get('auto_resolved_noise_count', 0)} ({biz_stats.get('noise_rate_pct', 0)}%)"), unsafe_allow_html=True)
        m3.markdown(create_metric_card("Actionable Alert", f"{biz_stats.get('actionable_alert_count', 0)} ({biz_stats.get('actionable_rate_pct', 0)}%)"), unsafe_allow_html=True)
        m4.markdown(create_metric_card("Blind Spots", f"{biz_stats.get('blind_spot_count', 0)} ({biz_stats.get('blind_spot_rate_pct', 0)}%)"), unsafe_allow_html=True)

        # Lifecycle Funnel Visual
        funnel_data = dict(
            stage=["Total Raised", "Bot Noise (Auto-Closed)", "Actionable Alerts (Human Intervened)"],
            count=[
                biz_stats.get("total_tickets", 0), 
                biz_stats.get("auto_resolved_noise_count", 0),
                biz_stats.get("actionable_alert_count", 0)
            ]
        )
        col_f1, col_f2 = st.columns([1,1])
        with col_f1:
            fig_funnel = px.funnel(funnel_data, x='count', y='stage', template="plotly_dark",
                                  color_discrete_sequence=["#00f2fe", "#4facfe", "#f5576c"])
            fig_funnel.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_funnel, use_container_width=True)

        with col_f2:
            if biz_stats.get("top_blind_spot_groups"):
                bs_df = pd.DataFrame(biz_stats["top_blind_spot_groups"])
                fig2 = px.bar(bs_df.head(5), y="group", x="unmonitored_business_tickets", orientation='h',
                              color="unmonitored_business_tickets", color_continuous_scale="Sunset", template="plotly_dark",
                              title="Top Monitoring Blind Spots")
                fig2.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig2, use_container_width=True)
    else:
        not_ready("Lifecycle Stats")

    if biz_gaps_md:
        with st.expander("Read Full Diagnostic Narrative", expanded=True):
            st.markdown(biz_gaps_md)

# ── Tab 7: Long-Running Analysis ──────────────────────────────────────────────
with tabs[6]:
    st.subheader("Long-Running Incident Heatmap")
    lr_stats = load_json("long_running_stats.json")
    lr_report_md = load_md("long_running_report.md")

    if lr_stats and lr_stats.get("clusters"):
        c1, c2 = st.columns(2)
        c1.markdown(create_metric_card("P80 MTTR Threshold", f"{lr_stats.get('p80_threshold_minutes', 0):.0f} min"), unsafe_allow_html=True)
        c2.markdown(create_metric_card("Long-Running Incidents", str(lr_stats.get("total_long_running", 0))), unsafe_allow_html=True)

        cl_df = pd.DataFrame(lr_stats["clusters"])
        fig2 = px.scatter(cl_df, x="average_log_fidelity_score", y="average_mttr_minutes",
                          size="incident_count", color="cluster_id",
                          hover_name="cluster_id", template="plotly_dark",
                          color_discrete_sequence=COLORS, title="Fidelity vs Resolution Time (Actionable Alerts Only)")
        fig2.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        not_ready("Long-Running Stats")

    if lr_report_md:
        with st.expander("Read LLM Gap Assessment Report", expanded=True):
            st.markdown(lr_report_md)

# ── Tab 8: QA Report ──────────────────────────────────────────────────────────
with tabs[7]:
    st.subheader("QA Platform Email Alerts")
    qa_df = load_csv("qa_fidelity_alerts.csv")

    if qa_df is not None:
        col1, col2 = st.columns([1, 2])
        with col1:
            rag_counts = qa_df["RAG_Status"].value_counts().reset_index()
            rag_counts.columns = ["Status", "Count"]
            fig = px.pie(rag_counts, names="Status", values="Count",
                         color="Status", hole=0.6, template="plotly_dark",
                         color_discrete_map={"Red": "#ff0844", "Amber": "#f6ad55", "Green": "#84fab0"})
            fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=0, l=0, r=0, b=0))
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig2 = px.bar(qa_df.sort_values("Avg_Log_Fidelity_Score"),
                          x="Assignment_Group", y="Avg_Log_Fidelity_Score",
                          color="RAG_Status", template="plotly_dark",
                          color_discrete_map={"Red": "#ff0844", "Amber": "#f6ad55", "Green": "#84fab0"},
                          text_auto=True, title="Team Fidelity Scoring Matrix")
            fig2.update_layout(xaxis_tickangle=-30, yaxis_range=[0, 100], plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig2, use_container_width=True)

        html_path = OUTPUT / "qa_fidelity_report.html"
        if html_path.exists():
            st.success("HTML Email Digest ready for distribution.")
            with st.expander("Preview QA Team Emails"):
                st.components.v1.html(html_path.read_text(encoding="utf-8"), height=600, scrolling=True)
    else:
        not_ready("QA Fidelity Report")
