"""
09_long_running_analysis.py
-----------------------------
Objective 4: Identify long-running monitoring incidents and fix root cause
by improving source logging.

Outputs:
  data/output/long_running_incidents.csv — flagged incidents with gap diagnosis
  data/output/long_running_report.md     — full diagnostic report with fixes
  data/output/long_running_stats.json    — stats for dashboard
"""

import json
import sys
from collections import Counter
from pathlib import Path

from llm_gateway import generate_text
from log_fidelity_utils import group_by, mean, read_table, write_table


LONG_RUNNING_PERCENTILE = 80
MIN_MTTR_MINUTES = 60
MIN_CLUSTER_SIZE = 3

SIGNAL_LABELS = {
    "Has_Timestamp":       "Event Timestamp",
    "Has_Source_System":   "Source System",
    "Has_Service_Name":    "Service Name",
    "Has_Impacted_Entity": "Impacted Entity",
    "Has_Error_Code":      "Error Code",
    "Has_Threshold":       "Threshold / Metric Value",
    "Has_Alert_URL":       "Alert URL",
    "Has_Correlation_ID":  "Correlation ID",
    "Has_Payload_Context": "Payload / Context",
    "Has_RCA":             "Root Cause Analysis",
    "Has_Action_Taken":    "Action Taken",
}


def safe_float(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def percentile(values: list[float], pct: int) -> float:
    if not values:
        return 0.0
    sv = sorted(values)
    idx = int(len(sv) * pct / 100)
    return sv[min(idx, len(sv) - 1)]


def missing_signals(row: dict) -> list[str]:
    return [label for sig, label in SIGNAL_LABELS.items() if str(row.get(sig, "")).lower() != "true"]


def build_cluster_prompt(cid: str, stats: dict) -> str:
    return f"""
You are an AIOps reliability engineer. For this cluster of "Actionable Alerts" (incidents created by a Bot but eventually closed by a Human), identify:
1. **Root Logging Gaps** — which fields did the bot fail to provide that forced the human to waste time investigating?
2. **Source System Fix** — exact change the team should make in their monitoring tool so the bot can auto-resolve this in the future
3. **Expected MTTR Reduction** — realistic estimate of time saved per incident
4. **Quick Win** — single most impactful log template change for this sprint

Return plain markdown. Be specific about field names and tooling.

Cluster: {cid}
Stats: {json.dumps(stats, indent=2)}
""".strip()


def build_summary_prompt(clusters: list[dict]) -> str:
    return f"""
Write a Long-Running Actionable Incident Diagnostic Report for engineering leadership.

Focus ONLY on tickets that were created by Bots but took a long time for Humans to manually close.

Sections:
1. **Overview** — how many actionable alerts are long-running, MTTR burden
2. **Top Offending Clusters** — worst platform/system combinations where bots fail to auto-resolve
3. **Common Root Cause Themes** — logging gaps forcing human intervention across clusters
4. **Priority Fix Roadmap** — ordered fixes with expected MTTR impact to achieve auto-resolution
5. **AIOps Readiness Gap** — gap between current state and zero-touch self-healing

Cluster summaries: {json.dumps(clusters, indent=2)}
""".strip()


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python src/09_long_running_analysis.py <scored.csv> <output_dir>")

    rows = read_table(sys.argv[1])
    output_dir = Path(sys.argv[2])
    output_dir.mkdir(parents=True, exist_ok=True)

    # Filter down to ONLY Actionable Alerts (Bot Created -> Human Closed)
    actionable = [r for r in rows if r.get("Ticket_Lifecycle") == "Actionable Alert"]

    with_mttr = [r for r in actionable if safe_float(r.get("MTTR_Minutes")) >= MIN_MTTR_MINUTES]
    all_mttr = sorted(safe_float(r.get("MTTR_Minutes")) for r in with_mttr)
    p80 = percentile(all_mttr, LONG_RUNNING_PERCENTILE)

    print(f"  Total Actionable Alerts: {len(actionable)}", flush=True)
    print(f"  MTTR P80 threshold: {p80:.0f} min ({len(with_mttr)} actionable incidents >= {MIN_MTTR_MINUTES} min)", flush=True)

    long_running = [r for r in with_mttr if safe_float(r.get("MTTR_Minutes")) >= p80]
    for row in long_running:
        row["Is_Long_Running"] = "true"
        row["Missing_Signals"] = " | ".join(missing_signals(row))
        row["MTTR_Percentile_Bucket"] = "P80+"

    print(f"  Long-running incidents: {len(long_running)}", flush=True)

    lr_path = output_dir / "long_running_incidents.csv"
    write_table(lr_path, long_running)
    print(f"  Long-running incidents -> {lr_path}")

    cluster_summaries = []
    cluster_diagnoses = []

    for platform, p_rows in sorted(group_by(long_running, "Platform").items()):
        for area, a_rows in sorted(group_by(p_rows, "System_Area").items()):
            if len(a_rows) < MIN_CLUSTER_SIZE:
                continue
            cid = f"{platform} | {area}"
            mttr_vals = [safe_float(r.get("MTTR_Minutes")) for r in a_rows]
            gap_counter: Counter = Counter()
            for r in a_rows:
                gap_counter.update(missing_signals(r))

            stats = {
                "cluster_id": cid,
                "incident_count": len(a_rows),
                "average_mttr_minutes": round(mean(mttr_vals), 1),
                "max_mttr_minutes": round(max(mttr_vals), 1),
                "average_log_fidelity_score": round(mean([safe_float(r.get("Log_Fidelity_Score")) for r in a_rows]), 2),
                "top_missing_signals": [{"signal": s, "count": c} for s, c in gap_counter.most_common(5)],
                "example_incident_ids": [r.get("Incident_ID", "") for r in a_rows[:3]],
            }
            cluster_summaries.append(stats)

            print(f"  Analysing cluster: {cid} ({len(a_rows)} incidents) ...", flush=True)
            try:
                diagnosis = generate_text(build_cluster_prompt(cid, stats), max_output_tokens=800)
                cluster_diagnoses.append(f"## {cid}\n\n{diagnosis.strip()}\n")
            except Exception as exc:
                print(f"  [WARNING] LLM failed for {cid}: {exc}", flush=True)
                cluster_diagnoses.append(f"## {cid}\n\n*LLM analysis unavailable: {exc}*\n")

    print("  Generating full long-running report ...", flush=True)
    try:
        summary_text = generate_text(build_summary_prompt(cluster_summaries), max_output_tokens=2000)
    except Exception as exc:
        summary_text = f"*Summary generation failed: {exc}*"

    report = "\n\n".join(
        ["# Long-Running Incident Diagnostic Report\n", summary_text.strip(),
         "\n---\n\n# Per-Cluster Diagnoses\n"] + cluster_diagnoses
    )
    report_path = output_dir / "long_running_report.md"
    report_path.write_text(report + "\n", encoding="utf-8")
    print(f"  Long-running report -> {report_path}")

    stats_path = output_dir / "long_running_stats.json"
    stats_path.write_text(
        json.dumps({"p80_threshold_minutes": p80, "total_long_running": len(long_running), "clusters": cluster_summaries}, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
