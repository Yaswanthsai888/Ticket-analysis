import sys
from pathlib import Path

from log_fidelity_utils import bucket, ordered_fieldnames, priority_score, read_table, write_table


def is_true(row: dict[str, str], key: str) -> bool:
    return str(row.get(key, "")).lower() == "true"


def ratio(row: dict[str, str], keys: list[str]) -> float:
    return sum(1 for key in keys if is_true(row, key)) / len(keys)


def score_row(row: dict[str, str]) -> dict[str, str]:
    technical = ratio(
        row,
        [
            "Has_Source_System",
            "Has_Service_Name",
            "Has_Impacted_Entity",
            "Has_Error_Code",
            "Has_Correlation_ID",
            "Has_Payload_Context",
        ],
    ) * 25

    granularity = ratio(
        row,
        [
            "Has_Service_Name",
            "Has_Impacted_Entity",
            "Has_Error_Code",
            "Has_Threshold",
            "Has_Payload_Context",
        ],
    ) * 20

    actionability = ratio(
        row,
        [
            "Has_Threshold",
            "Has_Action_Taken",
            "Has_Resolver_Owner",
            "Has_Alert_URL",
        ],
    ) * 20

    rca = ratio(row, ["Has_RCA", "Has_Action_Taken"]) * 15
    trust = ratio(row, ["Has_Timestamp", "Has_Source_System", "Has_Resolver_Owner"]) * 10
    automation = ratio(row, ["Has_Correlation_ID", "Has_Impacted_Entity", "Has_Threshold", "Has_Action_Taken"]) * 10

    penalty = 5 if is_true(row, "Has_Unresolved_Placeholder") else 0
    total = max(round(technical + granularity + actionability + rca + trust + automation - penalty, 2), 0)

    row.update(
        {
            "Technical_Completeness_Score": round(technical, 2),
            "Granularity_Score": round(granularity, 2),
            "Actionability_Score": round(actionability, 2),
            "RCA_Readiness_Score": round(rca, 2),
            "Trustworthiness_Score": round(trust, 2),
            "Automation_Readiness_Score": round(automation, 2),
            "Placeholder_Penalty": penalty,
            "Log_Fidelity_Score": total,
            "Quality_Bucket": bucket(total),
            "Priority_Weight": priority_score(row.get("Priority", "")),
        }
    )
    return row


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python src/03_score_log_fidelity.py <signals.csv> <output.csv>")

    rows = [score_row(row) for row in read_table(sys.argv[1])]
    write_table(sys.argv[2], rows, ordered_fieldnames(rows))
    print(f"Scored {len(rows)} incidents -> {Path(sys.argv[2])}")


if __name__ == "__main__":
    main()
