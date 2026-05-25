import csv
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


CANONICAL_COLUMNS = [
    "Incident_ID",
    "Created_Date",
    "Resolved_Date",
    "Closed_Date",
    "Created_By",
    "Resolved_By",
    "Closed_By",
    "Assignment_Group",
    "Short_Description",
    "Description_Text",
    "Work_Notes",
    "Close_Notes",
    "Close_Code",
    "Priority",
    "State",
    "Category",
    "Resolve_Time_Seconds",
    "MTTR_Minutes",
    "Platform",
    "System_Area",
    "Created_By_Bot",
    "Closed_By_Bot",
    "Ticket_Lifecycle",
    "Raw_Text",
]


ALIASES = {
    "Incident_ID": ["Number", "Ticket ID", "Incident ID", "ID"],
    "Created_Date": ["Created", "Opened", "Created Date"],
    "Resolved_Date": ["Resolved", "Actual end", "Resolved Date"],
    "Closed_Date": ["Closed", "Closed Date"],
    "Created_By": ["Created by", "Opened by"],
    "Resolved_By": ["Resolved by"],
    "Closed_By": ["Closed by"],
    "Assignment_Group": ["Assignment group", "Resolver Group"],
    "Short_Description": ["Short description", "Title", "Summary"],
    "Description_Text": ["Description"],
    "Work_Notes": ["Work notes", "Additional comments"],
    "Close_Notes": ["Close notes", "Resolution notes"],
    "Close_Code": ["Close code"],
    "Priority": ["Priority", "Severity"],
    "State": ["State", "Status"],
    "Category": ["Category"],
    "Resolve_Time_Seconds": ["Resolve time", "Business resolve time"],
}


DATE_FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S.%fZ",
    "%Y-%m-%dT%H:%M:%SZ",
    "%d-%m-%Y %H:%M:%S",
    "%m/%d/%Y %H:%M:%S",
]


def read_table(path: str | Path) -> list[dict[str, Any]]:
    path = Path(path)
    if path.suffix.lower() in {".xlsx", ".xls"}:
        try:
            import pandas as pd
        except ImportError as exc:
            raise SystemExit("Excel input requires pandas and openpyxl. Install requirements.txt.") from exc
        return pd.read_excel(path).fillna("").astype(str).to_dict(orient="records")

    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_table(path: str | Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = ordered_fieldnames(rows)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def ordered_fieldnames(rows: list[dict[str, Any]]) -> list[str]:
    seen = []
    for row in rows:
        for key in row:
            if key not in seen:
                seen.append(key)
    return seen


def first_present(row: dict[str, Any], aliases: list[str]) -> str:
    lower_map = {k.strip().lower(): k for k in row}
    for alias in aliases:
        key = lower_map.get(alias.lower())
        if key is not None and str(row.get(key, "")).strip():
            return clean_text(row.get(key, ""))
    return ""


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).replace("\xa0", " ")
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_datetime(value: str) -> datetime | None:
    value = clean_text(value)
    if not value:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value[:26].rstrip("Z"), fmt.replace("Z", ""))
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def iso_or_blank(value: datetime | None) -> str:
    return value.isoformat(sep=" ") if value else ""


def infer_platform(text: str, created_by: str) -> str:
    haystack = f"{text} {created_by}".lower()
    if "new relic" in haystack or "newrelic" in haystack or "svcnr" in haystack:
        return "New Relic"
    if "cloud alm" in haystack or "sap cloud alm" in haystack or "svcsapcloudalm" in haystack:
        return "SAP Cloud ALM"
    if "self-service" in haystack or "work notes" in haystack or "root cause" in haystack or "action taken" in haystack:
        return "ServiceNow Manual"
    return "Unknown"


def infer_system_area(text: str, assignment_group: str) -> str:
    group_lower = assignment_group.lower()
    if "btp" in group_lower: return "BTP"
    if "record to report" in group_lower: return "Record To Report"
    if "source to pay" in group_lower: return "Source To Pay"
    if "market to cash" in group_lower: return "Market To Cash"
    if "demand to warehouse" in group_lower: return "Demand To Warehouse"
    if "abap" in group_lower: return "ABAP"
    if "tech & infra" in group_lower: return "Tech & Infra"
    if "fp&a" in group_lower: return "FP&A"

    haystack = f"{text} {assignment_group}".lower()
    if "aif" in haystack:
        return "AIF"
    if "integration" in haystack or "idoc" in haystack:
        return "Integration"
    if "sap core" in haystack or "s/4" in haystack or "p1c" in haystack:
        return "ERP SAP Core"
    return "Unknown"


def priority_score(priority: str) -> float:
    text = priority.lower()
    if "critical" in text or text.startswith("1"):
        return 4.0
    if "high" in text or text.startswith("2"):
        return 3.0
    if "medium" in text or text.startswith("3"):
        return 2.0
    if "low" in text or text.startswith("4"):
        return 1.0
    return 0.0


def bucket(score: float) -> str:
    if score >= 80:
        return "Excellent"
    if score >= 65:
        return "Good"
    if score >= 45:
        return "Needs Improvement"
    return "Poor"


def group_by(rows: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    grouped = defaultdict(list)
    for row in rows:
        grouped[row.get(key, "Unknown") or "Unknown"].append(row)
    return dict(grouped)


def mean(values: list[float]) -> float:
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else 0.0
