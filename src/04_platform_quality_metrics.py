import sys
from pathlib import Path

from log_fidelity_utils import group_by, mean, read_table, write_table


REQUIRED_SIGNALS = [
    "Has_Timestamp",
    "Has_Source_System",
    "Has_Service_Name",
    "Has_Impacted_Entity",
    "Has_Error_Code",
    "Has_Threshold",
    "Has_Alert_URL",
    "Has_Correlation_ID",
    "Has_Payload_Context",
    "Has_RCA",
    "Has_Action_Taken",
]


def as_float(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def metric_rows(rows: list[dict[str, str]], key: str) -> list[dict[str, str]]:
    output = []
    for group_name, group_rows in sorted(group_by(rows, key).items()):
        scores = [as_float(row.get("Log_Fidelity_Score")) for row in group_rows]
        mttr = [as_float(row.get("MTTR_Minutes")) for row in group_rows if as_float(row.get("MTTR_Minutes")) > 0]
        poor_count = sum(1 for row in group_rows if row.get("Quality_Bucket") == "Poor")
        needs_improvement = sum(1 for row in group_rows if row.get("Quality_Bucket") == "Needs Improvement")
        output.append(
            {
                key: group_name,
                "Incident_Count": len(group_rows),
                "Average_Log_Fidelity_Score": round(mean(scores), 2),
                "Average_MTTR_Minutes": round(mean(mttr), 2),
                "Poor_Or_Needs_Improvement_Count": poor_count + needs_improvement,
                "Poor_Or_Needs_Improvement_Rate": round((poor_count + needs_improvement) / len(group_rows), 3),
            }
        )
    return output


def missing_field_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    output = []
    total = len(rows) or 1
    for signal in REQUIRED_SIGNALS:
        missing = sum(1 for row in rows if str(row.get(signal, "")).lower() != "true")
        output.append(
            {
                "Signal": signal,
                "Missing_Count": missing,
                "Missing_Rate": round(missing / total, 3),
            }
        )
    return output


def bucket_mttr_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    output = []
    for bucket, bucket_rows in sorted(group_by(rows, "Quality_Bucket").items()):
        mttr = [as_float(row.get("MTTR_Minutes")) for row in bucket_rows if as_float(row.get("MTTR_Minutes")) > 0]
        output.append(
            {
                "Quality_Bucket": bucket,
                "Incident_Count": len(bucket_rows),
                "Average_MTTR_Minutes": round(mean(mttr), 2),
            }
        )
    return output


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python src/04_platform_quality_metrics.py <scored.csv> <output_dir>")

    rows = read_table(sys.argv[1])
    rows = [r for r in rows if r.get("Ticket_Lifecycle") != "Monitoring Blind Spot"]
    output_dir = Path(sys.argv[2])
    output_dir.mkdir(parents=True, exist_ok=True)

    write_table(output_dir / "platform_quality_metrics.csv", metric_rows(rows, "Platform"))
    write_table(output_dir / "assignment_group_quality_metrics.csv", metric_rows(rows, "Assignment_Group"))
    write_table(output_dir / "missing_field_summary.csv", missing_field_rows(rows))
    write_table(output_dir / "mttr_by_quality_bucket.csv", bucket_mttr_rows(rows))
    print(f"Generated platform and missing-field metrics -> {output_dir}")


if __name__ == "__main__":
    main()
