import sys
from pathlib import Path

from log_fidelity_utils import (
    ALIASES,
    CANONICAL_COLUMNS,
    clean_text,
    first_present,
    infer_platform,
    infer_system_area,
    iso_or_blank,
    parse_datetime,
    read_table,
    write_table,
)


BOT_IDENTIFIERS = {"system", "svc", "bot", "newrelic", "svcsapcloudalm01@heiway.net", "cloud alm"}


def is_bot(actor_name: str) -> bool:
    actor = (actor_name or "").lower().strip()
    return any(ident in actor for ident in BOT_IDENTIFIERS)


def normalize_row(row: dict[str, str]) -> dict[str, str]:
    normalized = {field: first_present(row, ALIASES.get(field, [field])) for field in CANONICAL_COLUMNS}

    created = parse_datetime(normalized.get("Created_Date", ""))
    resolved = parse_datetime(normalized.get("Resolved_Date", ""))
    closed = parse_datetime(normalized.get("Closed_Date", ""))
    end_time = resolved or closed

    mttr_minutes = ""
    if created and end_time:
        mttr_minutes = round(max((end_time - created).total_seconds() / 60.0, 0), 2)
    elif normalized.get("Resolve_Time_Seconds"):
        try:
            mttr_minutes = round(float(normalized["Resolve_Time_Seconds"]) / 60.0, 2)
        except ValueError:
            mttr_minutes = ""

    raw_text = clean_text(
        " ".join(
            [
                f"[{normalized.get('Category', '')}]",
                f"[{normalized.get('Assignment_Group', '')}]",
                normalized.get("Short_Description", ""),
                normalized.get("Description_Text", ""),
                normalized.get("Work_Notes", ""),
                normalized.get("Close_Notes", ""),
                f"Close Code: {normalized.get('Close_Code', '')}",
            ]
        )
    )

    created_by_bot = is_bot(normalized.get("Created_By", ""))
    closed_by_bot = is_bot(normalized.get("Closed_By", ""))

    if created_by_bot and closed_by_bot:
        lifecycle = "Auto-Resolved Noise"
    elif created_by_bot and not closed_by_bot:
        lifecycle = "Actionable Alert"
    else:
        lifecycle = "Monitoring Blind Spot"

    normalized.update(
        {
            "Created_Date": iso_or_blank(created),
            "Resolved_Date": iso_or_blank(resolved),
            "Closed_Date": iso_or_blank(closed),
            "MTTR_Minutes": str(mttr_minutes),
            "Created_By_Bot": "true" if created_by_bot else "false",
            "Closed_By_Bot": "true" if closed_by_bot else "false",
            "Ticket_Lifecycle": lifecycle,
            "Raw_Text": raw_text,
            "Platform": infer_platform(raw_text, normalized.get("Created_By", "")),
            "System_Area": infer_system_area(raw_text, normalized.get("Assignment_Group", "")),
        }
    )
    return normalized


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python src/01_normalize_incidents.py <input.csv|xlsx> <output.csv>")

    rows = read_table(sys.argv[1])
    normalized = [normalize_row(row) for row in rows]
    write_table(sys.argv[2], normalized, CANONICAL_COLUMNS)
    print(f"Normalized {len(normalized)} incidents -> {Path(sys.argv[2])}")


if __name__ == "__main__":
    main()
