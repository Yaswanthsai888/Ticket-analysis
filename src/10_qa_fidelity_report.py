"""
10_qa_fidelity_report.py
--------------------------
Objective 5: Enable QA alert / email generation to assess log fidelity
before production.

Groups incidents by Assignment Group, scores each team's fidelity, generates
an LLM paragraph per team, and renders a styled HTML email digest.

Outputs:
  data/output/qa_fidelity_alerts.csv   — per-team alert list (assignable)
  data/output/qa_fidelity_report.html  — rich HTML email digest
"""

import json
import sys
from collections import Counter
from pathlib import Path

from llm_gateway import generate_text
from log_fidelity_utils import group_by, mean, read_table, write_table


SIGNAL_LABELS = {
    "Has_Timestamp":       "Event Timestamp",
    "Has_Source_System":   "Source System",
    "Has_Service_Name":    "Service Name",
    "Has_Impacted_Entity": "Impacted Entity",
    "Has_Error_Code":      "Error Code",
    "Has_Threshold":       "Threshold / Metric",
    "Has_Alert_URL":       "Alert URL",
    "Has_Correlation_ID":  "Correlation ID",
    "Has_Payload_Context": "Payload / Context",
    "Has_RCA":             "Root Cause Analysis",
    "Has_Action_Taken":    "Action Taken",
}

MIN_TEAM_SIZE = 5


def safe_float(v) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def rag_status(score: float) -> str:
    if score >= 65:
        return "Green"
    if score >= 45:
        return "Amber"
    return "Red"


def missing_signals(row: dict) -> list[str]:
    return [label for sig, label in SIGNAL_LABELS.items() if str(row.get(sig, "")).lower() != "true"]


def team_summary(group: str, rows: list[dict]) -> dict:
    avg_score = round(mean([safe_float(r.get("Log_Fidelity_Score")) for r in rows]), 2)
    avg_mttr = round(
        mean([safe_float(r.get("MTTR_Minutes")) for r in rows if safe_float(r.get("MTTR_Minutes")) > 0]),
        1,
    )
    poor = sum(1 for r in rows if r.get("Quality_Bucket") in {"Poor", "Needs Improvement"})
    gap_counter: Counter = Counter()
    for r in rows:
        gap_counter.update(missing_signals(r))

    worst = sorted(rows, key=lambda r: safe_float(r.get("Log_Fidelity_Score")))[:3]
    return {
        "assignment_group": group,
        "incident_count": len(rows),
        "average_log_fidelity_score": avg_score,
        "rag_status": rag_status(avg_score),
        "average_mttr_minutes": avg_mttr,
        "poor_or_needs_improvement_count": poor,
        "top_missing_signals": [s for s, _ in gap_counter.most_common(3)],
        "worst_incidents": [
            {"id": r.get("Incident_ID"), "score": r.get("Log_Fidelity_Score"), "desc": r.get("Short_Description", "")[:120]}
            for r in worst
        ],
    }


def build_team_prompt(summary: dict) -> str:
    return f"""
Write a short, plain-English paragraph (3-4 sentences) for an engineering team lead.

Tell them:
- Their team's current log fidelity situation and RAG status
- The 1-2 most impactful missing fields causing investigation delays
- One specific, concrete action they can take this sprint to improve

Be direct, specific, and avoid jargon. Do NOT use bullet points — plain paragraph only.

Team data: {json.dumps(summary, indent=2)}
""".strip()


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Log Fidelity QA Report</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f0f4f8; margin: 0; padding: 24px; color: #1a202c; }}
  .container {{ max-width: 900px; margin: 0 auto; }}
  h1 {{ font-size: 28px; color: #2d3748; border-bottom: 3px solid #4299e1; padding-bottom: 12px; }}
  h2 {{ font-size: 18px; margin: 0 0 8px; }}
  .summary-bar {{ display: flex; gap: 16px; margin: 20px 0; flex-wrap: wrap; }}
  .stat-card {{ background: white; border-radius: 10px; padding: 16px 24px; flex: 1; min-width: 140px;
                box-shadow: 0 1px 4px rgba(0,0,0,0.1); text-align: center; }}
  .stat-card .value {{ font-size: 32px; font-weight: 700; }}
  .stat-card .label {{ font-size: 12px; color: #718096; margin-top: 4px; }}
  .team-card {{ background: white; border-radius: 10px; padding: 20px 24px; margin: 16px 0;
                box-shadow: 0 1px 4px rgba(0,0,0,0.1); border-left: 6px solid {color}; }}
  .rag-badge {{ display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 13px;
                font-weight: 600; background: {badge_bg}; color: {badge_fg}; margin-left: 10px; }}
  .score {{ font-size: 26px; font-weight: 700; color: {score_color}; }}
  .gaps {{ margin: 8px 0; font-size: 13px; color: #4a5568; }}
  .gap-tag {{ display: inline-block; background: #edf2f7; border-radius: 4px; padding: 2px 8px;
              margin: 2px; font-size: 12px; }}
  .worst-table {{ width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 13px; }}
  .worst-table th {{ background: #f7fafc; padding: 6px 10px; text-align: left; color: #4a5568; }}
  .worst-table td {{ padding: 6px 10px; border-top: 1px solid #e2e8f0; }}
  .narrative {{ background: #fffbeb; border-left: 4px solid #f6ad55; padding: 12px 16px;
                border-radius: 0 8px 8px 0; margin: 12px 0; font-size: 14px; line-height: 1.6; }}
  .footer {{ text-align: center; color: #a0aec0; font-size: 12px; margin-top: 32px; }}
  .red {{ color: #c53030; }}
  .amber {{ color: #c05621; }}
  .green {{ color: #276749; }}
</style>
</head>
<body>
<div class="container">
  <h1>Log Fidelity QA Report</h1>
  <p style="color:#718096">{generated_at}</p>
  <div class="summary-bar">
    <div class="stat-card"><div class="value">{total_incidents}</div><div class="label">Total Incidents</div></div>
    <div class="stat-card"><div class="value">{total_teams}</div><div class="label">Teams Assessed</div></div>
    <div class="stat-card"><div class="value red">{red_count}</div><div class="label">Red Teams</div></div>
    <div class="stat-card"><div class="value amber">{amber_count}</div><div class="label">Amber Teams</div></div>
    <div class="stat-card"><div class="value green">{green_count}</div><div class="label">Green Teams</div></div>
  </div>
  {team_cards}
  <div class="footer">Generated by USECASE-1 Log Fidelity Assessment Pipeline</div>
</div>
</body>
</html>"""

TEAM_CARD_TEMPLATE = """
  <div class="team-card" style="border-left-color:{border_color}">
    <h2>{group}
      <span class="rag-badge" style="background:{badge_bg};color:{badge_fg}">{rag}</span>
    </h2>
    <div class="score" style="color:{score_color}">{avg_score} / 100</div>
    <div style="font-size:13px;color:#718096;margin:4px 0">
      {incident_count} incidents &nbsp;|&nbsp; Avg MTTR: {avg_mttr} min
      &nbsp;|&nbsp; Poor/NI: {poor_count}
    </div>
    <div class="gaps">
      <strong>Top gaps:</strong>
      {gap_tags}
    </div>
    <div class="narrative">{narrative}</div>
    <table class="worst-table">
      <tr><th>Incident ID</th><th>Score</th><th>Description</th></tr>
      {worst_rows}
    </table>
  </div>
"""

RAG_STYLES = {
    "Red":   {"border": "#fc8181", "badge_bg": "#fff5f5", "badge_fg": "#c53030", "score": "#c53030"},
    "Amber": {"border": "#f6ad55", "badge_bg": "#fffaf0", "badge_fg": "#c05621", "score": "#c05621"},
    "Green": {"border": "#68d391", "badge_bg": "#f0fff4", "badge_fg": "#276749", "score": "#276749"},
}


def render_team_card(summary: dict, narrative: str) -> str:
    rag = summary["rag_status"]
    style = RAG_STYLES[rag]
    gap_tags = "".join(f'<span class="gap-tag">{g}</span>' for g in summary["top_missing_signals"])
    worst_rows = "".join(
        f'<tr><td>{w["id"]}</td><td>{w["score"]}</td><td>{w["desc"]}</td></tr>'
        for w in summary["worst_incidents"]
    )
    return TEAM_CARD_TEMPLATE.format(
        group=summary["assignment_group"],
        rag=rag,
        border_color=style["border"],
        badge_bg=style["badge_bg"],
        badge_fg=style["badge_fg"],
        score_color=style["score"],
        avg_score=summary["average_log_fidelity_score"],
        incident_count=summary["incident_count"],
        avg_mttr=summary["average_mttr_minutes"],
        poor_count=summary["poor_or_needs_improvement_count"],
        gap_tags=gap_tags,
        narrative=narrative.replace("\n", " "),
        worst_rows=worst_rows,
    )


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python src/10_qa_fidelity_report.py <scored.csv> <output_dir>")

    rows = read_table(sys.argv[1])
    rows = [r for r in rows if r.get("Ticket_Lifecycle") != "Monitoring Blind Spot"]
    output_dir = Path(sys.argv[2])
    output_dir.mkdir(parents=True, exist_ok=True)

    from datetime import datetime
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    teams = {
        grp: team_rows
        for grp, team_rows in group_by(rows, "Assignment_Group").items()
        if len(team_rows) >= MIN_TEAM_SIZE and grp and grp != "Unknown"
    }

    print(f"  Generating QA report for {len(teams)} teams ...", flush=True)

    summaries = []
    alert_rows = []
    team_cards_html = []

    for group in sorted(teams):
        team_rows = teams[group]
        summary = team_summary(group, team_rows)
        summaries.append(summary)
        alert_rows.append({
            "Assignment_Group": summary["assignment_group"],
            "RAG_Status": summary["rag_status"],
            "Avg_Log_Fidelity_Score": summary["average_log_fidelity_score"],
            "Incident_Count": summary["incident_count"],
            "Poor_Or_Needs_Improvement": summary["poor_or_needs_improvement_count"],
            "Avg_MTTR_Minutes": summary["average_mttr_minutes"],
            "Top_Missing_Signals": " | ".join(summary["top_missing_signals"]),
        })

        print(f"  [{summary['rag_status']:5s}] {group} — score {summary['average_log_fidelity_score']}", flush=True)

        try:
            narrative = generate_text(build_team_prompt(summary), max_output_tokens=200)
        except Exception as exc:
            narrative = f"LLM unavailable: {exc}"

        team_cards_html.append(render_team_card(summary, narrative.strip()))

    # Write alerts CSV
    alerts_path = output_dir / "qa_fidelity_alerts.csv"
    write_table(alerts_path, alert_rows)
    print(f"  QA alerts CSV -> {alerts_path}")

    # Count RAG
    red = sum(1 for s in summaries if s["rag_status"] == "Red")
    amber = sum(1 for s in summaries if s["rag_status"] == "Amber")
    green = sum(1 for s in summaries if s["rag_status"] == "Green")

    html = HTML_TEMPLATE.format(
        generated_at=f"Generated: {generated_at}",
        total_incidents=len(rows),
        total_teams=len(teams),
        red_count=red,
        amber_count=amber,
        green_count=green,
        team_cards="".join(team_cards_html),
        color="#fc8181",
        badge_bg="#fff5f5",
        badge_fg="#c53030",
        score_color="#c53030",
    )

    html_path = output_dir / "qa_fidelity_report.html"
    html_path.write_text(html, encoding="utf-8")
    print(f"  QA fidelity report (HTML) -> {html_path}")


if __name__ == "__main__":
    main()
