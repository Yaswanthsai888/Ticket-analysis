import re
import sys
from pathlib import Path

from log_fidelity_utils import ordered_fieldnames, read_table, write_table


SIGNAL_COLUMNS = [
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
    "Has_Resolver_Owner",
    "Has_Unresolved_Placeholder",
]


PATTERNS = {
    "Has_Timestamp": re.compile(r"\b\d{4}-\d{2}-\d{2}[t\s]\d{2}:\d{2}:\d{2}", re.I),
    "Has_Source_System": re.compile(r"\b(new relic|newrelic|cloud alm|sap cloud alm|servicenow|snow)\b", re.I),
    "Has_Service_Name": re.compile(r"\b(service name|service type|service offering|configuration item)\b", re.I),
    "Has_Impacted_Entity": re.compile(r"\b(impacted entit|host|pod|instance|server|configuration item|ci:)\b", re.I),
    "Has_Error_Code": re.compile(r"\b([A-Z]{2,}\d{3,}|P\d[A-Z]\d{3}|[A-Z0-9]{4,}\d{2,})\b"),
    "Has_Threshold": re.compile(r"(>=|<=|>|<|threshold|exceeded|query result|metric value|critical)", re.I),
    "Has_Alert_URL": re.compile(r"https?://", re.I),
    "Has_Correlation_ID": re.compile(r"\b(issue id|correlation id|request id|trace id|transaction id|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\b", re.I),
    "Has_Payload_Context": re.compile(r"\b(payload|additional attributes|alert policies|alert conditions|trigger|workflow)\b", re.I),
    "Has_RCA": re.compile(r"\b(root cause|cause of service disruption|rca|due to|occurred due to)\b", re.I),
    "Has_Action_Taken": re.compile(r"\b(action taken|workaround|resolved by|provided the analysis|corrective action|closed from)\b", re.I),
    "Has_Resolver_Owner": re.compile(r"\b(assignment group|assigned to|resolved by|closed by|team)\b", re.I),
    "Has_Unresolved_Placeholder": re.compile(r"\$\{[^}]+\}|<[^>]+>", re.I),
}


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python src/02_extract_log_signals.py <normalized.csv> <output.csv>")

    rows = read_table(sys.argv[1])
    enriched = []
    for row in rows:
        raw_text = row.get("Raw_Text", "")
        metadata_text = " ".join(
            [
                row.get("Created_Date", ""),
                row.get("Resolved_Date", ""),
                row.get("Closed_Date", ""),
                row.get("Platform", ""),
                row.get("System_Area", ""),
                row.get("Assignment_Group", ""),
                row.get("Resolved_By", ""),
                row.get("Created_By", ""),
                row.get("Category", ""),
            ]
        )
        full_text = f"{raw_text} {metadata_text}"
        for column, pattern in PATTERNS.items():
            row[column] = bool_text(bool(pattern.search(full_text)))
        row["Has_Timestamp"] = bool_text(bool(row.get("Created_Date") or PATTERNS["Has_Timestamp"].search(full_text)))
        row["Has_Source_System"] = bool_text(bool(row.get("Platform") and row.get("Platform") != "Unknown"))
        row["Has_Service_Name"] = bool_text(
            bool(
                row.get("System_Area")
                and row.get("System_Area") != "Unknown"
                or PATTERNS["Has_Service_Name"].search(full_text)
            )
        )
        row["Has_Resolver_Owner"] = bool_text(bool(row.get("Assignment_Group") or PATTERNS["Has_Resolver_Owner"].search(full_text)))
        enriched.append(row)

    write_table(sys.argv[2], enriched, ordered_fieldnames(enriched))
    print(f"Extracted log fidelity signals for {len(enriched)} incidents -> {Path(sys.argv[2])}")


if __name__ == "__main__":
    main()
