import json
import sys
from pathlib import Path

from llm_gateway import generate_text
from log_fidelity_utils import group_by, mean, read_table


def as_float(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def build_summary_payload(rows: list[dict[str, str]]) -> dict[str, object]:
    total = len(rows)
    avg_score = round(mean([as_float(row.get("Log_Fidelity_Score")) for row in rows]), 2)
    poor_or_needs = sum(1 for row in rows if row.get("Quality_Bucket") in {"Poor", "Needs Improvement"})
    automation_ready = sum(1 for row in rows if as_float(row.get("Automation_Readiness_Score")) >= 8)

    platform_quality = []
    for platform, platform_rows in sorted(group_by(rows, "Platform").items()):
        platform_quality.append(
            {
                "platform": platform,
                "incident_count": len(platform_rows),
                "average_score": round(mean([as_float(row.get("Log_Fidelity_Score")) for row in platform_rows]), 2),
                "average_mttr_minutes": round(
                    mean([as_float(row.get("MTTR_Minutes")) for row in platform_rows if as_float(row.get("MTTR_Minutes")) > 0]),
                    2,
                ),
                "poor_or_needs_improvement": sum(
                    1 for row in platform_rows if row.get("Quality_Bucket") in {"Poor", "Needs Improvement"}
                ),
            }
        )

    missing_counts = {
        "correlation_or_issue_id": sum(1 for row in rows if row.get("Has_Correlation_ID") != "true"),
        "impacted_entity": sum(1 for row in rows if row.get("Has_Impacted_Entity") != "true"),
        "threshold_or_trigger_condition": sum(1 for row in rows if row.get("Has_Threshold") != "true"),
        "root_cause": sum(1 for row in rows if row.get("Has_RCA") != "true"),
        "action_taken": sum(1 for row in rows if row.get("Has_Action_Taken") != "true"),
        "payload_context": sum(1 for row in rows if row.get("Has_Payload_Context") != "true"),
        "alert_url": sum(1 for row in rows if row.get("Has_Alert_URL") != "true"),
    }

    weakest_examples = sorted(rows, key=lambda row: as_float(row.get("Log_Fidelity_Score")))[:10]
    examples = [
        {
            "incident_id": row.get("Incident_ID", ""),
            "platform": row.get("Platform", ""),
            "score": row.get("Log_Fidelity_Score", ""),
            "bucket": row.get("Quality_Bucket", ""),
            "short_description": row.get("Short_Description", ""),
            "missing": [
                name
                for name, signal in [
                    ("correlation ID", "Has_Correlation_ID"),
                    ("impacted entity", "Has_Impacted_Entity"),
                    ("threshold", "Has_Threshold"),
                    ("RCA", "Has_RCA"),
                    ("action taken", "Has_Action_Taken"),
                ]
                if row.get(signal) != "true"
            ],
        }
        for row in weakest_examples
    ]

    return {
        "total_incidents": total,
        "average_log_fidelity_score": avg_score,
        "poor_or_needs_improvement_count": poor_or_needs,
        "automation_ready_count": automation_ready,
        "platform_quality": platform_quality,
        "missing_counts": missing_counts,
        "weakest_examples": examples,
    }


def build_prompt(payload: dict[str, object]) -> str:
    return f"""
You are writing an executive summary for a Log Fidelity Assessment POC.

Use the metrics below to produce a clear markdown report for business and engineering stakeholders.

Required sections:
1. Overall Verdict
2. Business Impact
3. Platform Quality
4. Most Common Fidelity Gaps
5. Good Log Standard
6. Recommendations to Improve MTTR and Self-Healing Readiness

Be specific, concise, and data-driven. Do not invent numbers beyond the provided metrics.

Metrics:
{json.dumps(payload, indent=2)}
""".strip()


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python src/06_executive_summary.py <scored.csv> <output_dir>")

    rows = read_table(sys.argv[1])
    output_dir = Path(sys.argv[2])
    output_dir.mkdir(parents=True, exist_ok=True)

    payload = build_summary_payload(rows)
    summary = generate_text(build_prompt(payload), max_output_tokens=1800)

    path = output_dir / "executive_summary.md"
    path.write_text(summary.strip() + "\n", encoding="utf-8")
    print(f"Generated LLM executive summary -> {path}")


if __name__ == "__main__":
    main()
