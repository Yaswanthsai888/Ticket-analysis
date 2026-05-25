import json
import sys
from collections import Counter
from pathlib import Path

from llm_gateway import generate_json
from log_fidelity_utils import group_by, mean, read_table, write_table


SIGNAL_LABELS = {
    "Has_Timestamp": "event timestamp",
    "Has_Source_System": "monitoring source system",
    "Has_Service_Name": "service or business component",
    "Has_Impacted_Entity": "impacted host, pod, instance, CI, or SAP component",
    "Has_Error_Code": "error code, alert code, exception, or failed transaction identifier",
    "Has_Threshold": "metric value, threshold, or trigger condition",
    "Has_Alert_URL": "direct alert, trace, issue, or dashboard URL",
    "Has_Correlation_ID": "correlation ID, issue ID, trace ID, or request ID",
    "Has_Payload_Context": "payload, alert policy, workflow, trigger, or additional attributes",
    "Has_RCA": "root cause analysis in close notes",
    "Has_Action_Taken": "action taken, workaround, validation result, or permanent fix",
}

DEFAULT_MAX_SEGMENTS = 12
DEFAULT_EXAMPLES_PER_SEGMENT = 5


def as_float(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def missing_signals(row: dict[str, str]) -> list[str]:
    return [label for signal, label in SIGNAL_LABELS.items() if str(row.get(signal, "")).lower() != "true"]


def segment_key(row: dict[str, str]) -> str:
    return " | ".join(
        [
            row.get("Platform", "Unknown") or "Unknown",
            row.get("System_Area", "Unknown") or "Unknown",
            row.get("Quality_Bucket", "Unknown") or "Unknown",
        ]
    )


def compact_incident(row: dict[str, str]) -> dict[str, object]:
    return {
        "incident_id": row.get("Incident_ID", ""),
        "priority": row.get("Priority", ""),
        "score": row.get("Log_Fidelity_Score", ""),
        "mttr_minutes": row.get("MTTR_Minutes", ""),
        "missing_signals": missing_signals(row),
        "short_description": row.get("Short_Description", "")[:500],
        "description_excerpt": row.get("Description_Text", "")[:900],
        "work_notes_excerpt": row.get("Work_Notes", "")[:500],
        "close_notes_excerpt": row.get("Close_Notes", "")[:700],
    }


def build_segments(rows: list[dict[str, str]], max_segments: int) -> list[tuple[str, list[dict[str, str]]]]:
    grouped = group_by([{**row, "Segment_Key": segment_key(row)} for row in rows], "Segment_Key")

    def segment_priority(item: tuple[str, list[dict[str, str]]]) -> tuple[int, float, int]:
        _, segment_rows = item
        weak_count = sum(1 for row in segment_rows if row.get("Quality_Bucket") in {"Poor", "Needs Improvement"})
        avg_score = mean([as_float(row.get("Log_Fidelity_Score")) for row in segment_rows])
        return (-weak_count, avg_score, -len(segment_rows))

    weak_segments = [
        item
        for item in grouped.items()
        if any(row.get("Quality_Bucket") in {"Poor", "Needs Improvement"} for row in item[1])
    ]
    selected = sorted(weak_segments or list(grouped.items()), key=segment_priority)
    return selected[:max_segments]


def representative_examples(segment_rows: list[dict[str, str]], limit: int) -> list[dict[str, object]]:
    sorted_rows = sorted(
        segment_rows,
        key=lambda row: (
            as_float(row.get("Log_Fidelity_Score")),
            -as_float(row.get("Priority_Weight")),
            -as_float(row.get("MTTR_Minutes")),
        ),
    )
    return [compact_incident(row) for row in sorted_rows[:limit]]


def build_segment_payload(segment_id: str, segment_rows: list[dict[str, str]], examples_per_segment: int) -> dict[str, object]:
    first = segment_rows[0]
    missing_counter = Counter()
    for row in segment_rows:
        missing_counter.update(missing_signals(row))

    scores = [as_float(row.get("Log_Fidelity_Score")) for row in segment_rows]
    mttr = [as_float(row.get("MTTR_Minutes")) for row in segment_rows if as_float(row.get("MTTR_Minutes")) > 0]
    return {
        "segment_id": segment_id,
        "platform": first.get("Platform", ""),
        "system_area": first.get("System_Area", ""),
        "quality_bucket": first.get("Quality_Bucket", ""),
        "incident_count": len(segment_rows),
        "average_score": round(mean(scores), 2),
        "minimum_score": round(min(scores), 2) if scores else 0,
        "average_mttr_minutes": round(mean(mttr), 2),
        "top_missing_signals": missing_counter.most_common(8),
        "representative_examples": representative_examples(segment_rows, examples_per_segment),
    }


def build_prompt(payload: dict[str, object]) -> str:
    return f"""
You are assessing a segment of production monitoring incidents for log fidelity.

This segment represents many incidents, not one incident. Use the metrics and representative examples to recommend scalable logging standard changes.

Return only valid JSON with these exact keys:
- Segment_Assessment: concise paragraph explaining the pattern.
- RCA_Gaps: list of recurring root-cause-analysis gaps.
- Automation_Gaps: list of recurring self-healing readiness gaps.
- Logging_Standard_Changes: list of concrete template/schema changes.
- Improved_Log_Template: one improved reusable log template for this segment.
- Expected_MTTR_Impact: short statement on how these changes can reduce investigation time.

Segment payload:
{json.dumps(payload, indent=2)}
""".strip()


def assess_segment(segment_id: str, segment_rows: list[dict[str, str]], examples_per_segment: int) -> dict[str, str]:
    payload = build_segment_payload(segment_id, segment_rows, examples_per_segment)
    result = generate_json(build_prompt(payload), max_output_tokens=2200)

    example_ids = [
        str(example["incident_id"])
        for example in payload["representative_examples"]
        if example.get("incident_id")
    ]

    return {
        "Segment_ID": segment_id,
        "Platform": str(payload["platform"]),
        "System_Area": str(payload["system_area"]),
        "Quality_Bucket": str(payload["quality_bucket"]),
        "Incident_Count": str(payload["incident_count"]),
        "Average_Log_Fidelity_Score": str(payload["average_score"]),
        "Average_MTTR_Minutes": str(payload["average_mttr_minutes"]),
        "Representative_Incident_IDs": ", ".join(example_ids),
        "Top_Missing_Signals": " | ".join(f"{name}: {count}" for name, count in payload["top_missing_signals"]),
        "Segment_Assessment": str(result.get("Segment_Assessment", "")).strip(),
        "RCA_Gaps": " | ".join(map(str, result.get("RCA_Gaps", []))),
        "Automation_Gaps": " | ".join(map(str, result.get("Automation_Gaps", []))),
        "Logging_Standard_Changes": " | ".join(map(str, result.get("Logging_Standard_Changes", []))),
        "Improved_Log_Template": str(result.get("Improved_Log_Template", "")).strip(),
        "Expected_MTTR_Impact": str(result.get("Expected_MTTR_Impact", "")).strip(),
    }


def main() -> None:
    if len(sys.argv) not in {3, 5}:
        raise SystemExit(
            "Usage: python src/05_llm_log_assessment.py <scored.csv> <output.csv> "
            "[<max_segments> <examples_per_segment>]"
        )

    max_segments = int(sys.argv[3]) if len(sys.argv) == 5 else DEFAULT_MAX_SEGMENTS
    examples_per_segment = int(sys.argv[4]) if len(sys.argv) == 5 else DEFAULT_EXAMPLES_PER_SEGMENT

    rows = read_table(sys.argv[1])
    rows = [r for r in rows if r.get("Ticket_Lifecycle") != "Monitoring Blind Spot"]
    segments = build_segments(rows, max_segments)
    assessments = []
    failed_segments = []
    for index, (segment_id, segment_rows) in enumerate(segments, start=1):
        print(
            f"LLM assessing segment {index}/{len(segments)}: {segment_id} "
            f"({len(segment_rows)} incidents)",
            flush=True,
        )
        try:
            assessments.append(assess_segment(segment_id, segment_rows, examples_per_segment))
        except Exception as exc:
            print(
                f"[WARNING] Segment {index}/{len(segments)} failed after all retries "
                f"({type(exc).__name__}: {exc}). Skipping.",
                flush=True,
            )
            failed_segments.append(segment_id)

    if failed_segments:
        print(
            f"[WARNING] {len(failed_segments)} segment(s) could not be assessed: "
            + ", ".join(failed_segments),
            flush=True,
        )

    write_table(sys.argv[2], assessments)
    print(
        f"Generated {len(assessments)} segment-level LLM assessments for {len(rows)} incidents -> {Path(sys.argv[2])}"
    )


if __name__ == "__main__":
    main()
