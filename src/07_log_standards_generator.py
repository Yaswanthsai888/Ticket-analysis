"""
07_log_standards_generator.py
------------------------------
Objective 1 & 2: Define log fidelity standards for AIOps and self-healing.

Reads incidents_scored.csv, computes per-platform signal coverage rates, then
asks the LLM to generate a prescriptive log standard document per platform.

Outputs:
  data/output/log_standards.md   — human-readable prescriptive standard
  data/output/log_standards.json — machine-readable schema for tooling
"""

import json
import sys
from pathlib import Path

from llm_gateway import generate_text, generate_json
from log_fidelity_utils import group_by, mean, read_table


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
]

SIGNAL_LABELS = {
    "Has_Timestamp":       "Event Timestamp (ISO 8601)",
    "Has_Source_System":   "Source Monitoring System",
    "Has_Service_Name":    "Service / Business Component Name",
    "Has_Impacted_Entity": "Impacted Host / Pod / CI / SAP Component",
    "Has_Error_Code":      "Error Code / Alert Code / Exception ID",
    "Has_Threshold":       "Metric Value & Threshold / Trigger Condition",
    "Has_Alert_URL":       "Direct Alert / Trace / Dashboard URL",
    "Has_Correlation_ID":  "Correlation ID / Trace ID / Issue ID",
    "Has_Payload_Context": "Payload / Alert Policy / Additional Attributes",
    "Has_RCA":             "Root Cause Analysis",
    "Has_Action_Taken":    "Action Taken / Workaround / Permanent Fix",
}

AIOPS_MANDATORY = {
    "Has_Timestamp", "Has_Source_System", "Has_Impacted_Entity",
    "Has_Correlation_ID", "Has_Error_Code", "Has_Threshold",
}


def is_true(row: dict, key: str) -> bool:
    return str(row.get(key, "")).lower() == "true"


def coverage(rows: list[dict], signal: str) -> float:
    if not rows:
        return 0.0
    return round(sum(1 for r in rows if is_true(r, signal)) / len(rows) * 100, 1)


def platform_summary(platform: str, rows: list[dict]) -> dict:
    avg_score = round(mean([float(r.get("Log_Fidelity_Score", 0) or 0) for r in rows]), 2)
    avg_mttr = round(
        mean([float(r.get("MTTR_Minutes", 0) or 0) for r in rows if float(r.get("MTTR_Minutes", 0) or 0) > 0]),
        2,
    )
    signal_coverage = {
        SIGNAL_LABELS[sig]: coverage(rows, sig)
        for sig in SIGNAL_COLUMNS
    }
    missing = [label for sig, label in SIGNAL_LABELS.items() if coverage(rows, sig) < 60]
    aiops_gaps = [
        SIGNAL_LABELS[sig] for sig in AIOPS_MANDATORY if coverage(rows, sig) < 80
    ]
    automation_ready_pct = round(
        sum(1 for r in rows if float(r.get("Automation_Readiness_Score", 0) or 0) >= 8) / len(rows) * 100, 1
    )
    return {
        "platform": platform,
        "incident_count": len(rows),
        "average_log_fidelity_score": avg_score,
        "average_mttr_minutes": avg_mttr,
        "automation_ready_pct": automation_ready_pct,
        "signal_coverage_pct": signal_coverage,
        "fields_below_60pct_coverage": missing,
        "aiops_automation_gaps": aiops_gaps,
    }


def build_standards_prompt(summaries: list[dict]) -> str:
    return f"""
You are an AIOps logging standards architect.

Based on the signal coverage analysis below, generate a complete, prescriptive Log Fidelity Standard document for each monitoring platform.

For each platform produce:
1. **Mandatory Fields** — every alert/ticket MUST have these (use the fields with < 60% coverage as the primary targets to fix)
2. **AIOps Self-Healing Requirements** — fields required for automated remediation (correlation ID, impacted entity, threshold, error code)
3. **Field Format Specifications** — exact format for each mandatory field (e.g. ISO8601 for timestamps, UUID for correlation IDs)
4. **Sample Log Template** — a concrete, realistic example of a well-formed log entry for this platform
5. **Automation Readiness Gate** — minimum criteria an incident log must meet to be eligible for AIOps automated resolution

Then produce a final section:
6. **Universal Self-Healing Readiness Checklist** — applies to all platforms, 10 items a team can use to self-assess

Be specific, concise, and actionable. Use Markdown formatting with headers and tables.

Platform coverage analysis:
{json.dumps(summaries, indent=2)}
""".strip()


def build_schema_prompt(summaries: list[dict]) -> str:
    return f"""
You are generating a machine-readable JSON schema for log standards.

Based on the platform analysis below, return ONLY valid JSON with this structure:
{{
  "version": "1.0",
  "generated_for": "AIOps Log Fidelity Standards",
  "platforms": [
    {{
      "platform": "<name>",
      "mandatory_fields": [
        {{"field": "<name>", "format": "<description>", "example": "<value>", "aiops_required": true/false}}
      ],
      "automation_readiness_gate": {{
        "minimum_log_fidelity_score": <number>,
        "required_fields": ["<field1>", "<field2>"]
      }},
      "sample_log_template": {{}}
    }}
  ],
  "universal_self_healing_checklist": ["<item1>", "<item2>"]
}}

Platform analysis:
{json.dumps(summaries, indent=2)}
""".strip()


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python src/07_log_standards_generator.py <scored.csv> <output_dir>")

    rows = read_table(sys.argv[1])
    rows = [r for r in rows if r.get("Ticket_Lifecycle") != "Monitoring Blind Spot"]
    output_dir = Path(sys.argv[2])
    output_dir.mkdir(parents=True, exist_ok=True)

    platforms = group_by(rows, "Platform")
    summaries = [platform_summary(platform, prows) for platform, prows in sorted(platforms.items())]

    print(f"  Generating log standards for {len(summaries)} platforms ...", flush=True)

    # Generate Markdown standard document
    md_text = generate_text(build_standards_prompt(summaries), max_output_tokens=3000)
    md_path = output_dir / "log_standards.md"
    md_path.write_text(md_text.strip() + "\n", encoding="utf-8")
    print(f"  Log standards (Markdown) -> {md_path}")

    # Generate machine-readable JSON schema
    try:
        schema = generate_json(build_schema_prompt(summaries), max_output_tokens=2500)
    except Exception as exc:
        print(f"  [WARNING] JSON schema generation failed ({exc}). Writing empty schema.")
        schema = {"version": "1.0", "error": str(exc), "summaries": summaries}

    json_path = output_dir / "log_standards.json"
    json_path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
    print(f"  Log standards (JSON schema) -> {json_path}")


if __name__ == "__main__":
    main()
