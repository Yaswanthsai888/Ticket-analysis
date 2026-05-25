import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "data" / "output"


def run_step(name: str, args: list[str]) -> None:
    print(f"\n=== {name} ===", flush=True)
    subprocess.run([sys.executable, *args], cwd=ROOT, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Log Fidelity Assessment POC pipeline.")
    parser.add_argument("--input", required=True, help="Path to incident export CSV/XLSX.")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR), help="Output directory.")
    parser.add_argument("--max-llm-segments", default="12", help="Maximum segment-level LLM calls.")
    parser.add_argument("--examples-per-segment", default="5", help="Representative incidents per LLM segment.")
    parser.add_argument("--skip-correlation", action="store_true", help="Skip step 08 (business impact correlation).")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(
            f"Input file not found: {args.input}\n\n"
            "Use either a relative path like:\n"
            "  --input data/input/sample_incidents.csv\n\n"
            "or an absolute path wrapped in quotes like:\n"
            '  --input "C:\\Users\\yaswanthsai\\Downloads\\incident_May_25_to_May_26 (1).xlsx"'
        )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    normalized = output_dir / "incidents_normalized.csv"
    signals    = output_dir / "incidents_signals.csv"
    scored     = output_dir / "incidents_scored.csv"

    steps = [
        ("01 Normalize incidents",
         ["src/01_normalize_incidents.py", str(input_path), str(normalized)]),

        ("02 Extract log signals",
         ["src/02_extract_log_signals.py", str(normalized), str(signals)]),

        ("03 Score log fidelity",
         ["src/03_score_log_fidelity.py", str(signals), str(scored)]),

        ("04 Platform quality metrics",
         ["src/04_platform_quality_metrics.py", str(scored), str(output_dir)]),

        ("05 LLM segment assessment",
         ["src/05_llm_log_assessment.py", str(scored),
          str(output_dir / "ai_recommendations.csv"),
          args.max_llm_segments, args.examples_per_segment]),

        ("06 LLM executive summary",
         ["src/06_executive_summary.py", str(scored), str(output_dir)]),

        ("07 Log standards generator",
         ["src/07_log_standards_generator.py", str(scored), str(output_dir)]),

        ("09 Long-running incident analysis",
         ["src/09_long_running_analysis.py", str(scored), str(output_dir)]),

        ("10 QA fidelity report",
         ["src/10_qa_fidelity_report.py", str(scored), str(output_dir)]),
    ]

    # Step 08 uses normalized CSV (needs Created_By for monitoring/business split)
    if not args.skip_correlation:
        steps.insert(7, (
            "08 Business impact correlation",
            ["src/08_business_impact_correlation.py", str(normalized), str(output_dir)],
        ))

    for name, command in steps:
        run_step(name, command)

    print(f"\nPipeline complete. Outputs written to: {output_dir}")
    print("\nKey outputs:")
    for fname in [
        "incidents_scored.csv", "ai_recommendations.csv", "executive_summary.md",
        "log_standards.md", "log_standards.json",
        "business_impact_correlation.csv", "business_impact_gaps.md",
        "long_running_incidents.csv", "long_running_report.md",
        "qa_fidelity_alerts.csv", "qa_fidelity_report.html",
    ]:
        p = output_dir / fname
        status = "[OK]" if p.exists() else "[MISSING]"
        print(f"  {status}  {fname}")


if __name__ == "__main__":
    main()
