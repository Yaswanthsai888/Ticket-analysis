"""
08_business_impact_correlation.py
-----------------------------------
Objective 3: Monitoring-to-business impact correlation model (Lifecycle Analysis).

Calculates exact lifecycle metrics based on the Ticket_Lifecycle categorization:
  - Auto-Resolved Noise     (Bot Created -> Bot Closed)
  - Actionable Alert        (Bot Created -> Human Closed)
  - Monitoring Blind Spot   (Human Created -> Human Closed)

Outputs:
  data/output/business_impact_correlation.csv — grouping counts
  data/output/business_impact_gaps.md         — LLM gap narrative
  data/output/business_impact_stats.json      — dashboard stats
"""

import json
import sys
from collections import Counter
from pathlib import Path

from llm_gateway import generate_text
from log_fidelity_utils import group_by, read_table, write_table


def build_gap_prompt(stats: dict) -> str:
    return f"""
You are an AIOps monitoring quality analyst.

Analyse the following Ticket Lifecycle statistics and produce a markdown report with these sections:

1. **Executive Summary** — 2-3 sentences on overall alert actionable rate and noise
2. **Alert Noise Analysis** — why auto-resolving bot tickets are cluttering the system and how to reduce them
3. **Actionable Alerts** — analysis of the "Bot Created -> Human Closed" tickets. Why couldn't the bot finish the job? What is missing?
4. **Coverage Blind Spots** — analysis of human-created tickets. Why did monitoring miss these completely?
5. **Actionable Recommendations** — top 5 specific changes to shift tickets toward auto-resolution

Be specific and data-driven. Do not invent numbers beyond what is provided.

Statistics:
{json.dumps(stats, indent=2)}
""".strip()


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(
            "Usage: python src/08_business_impact_correlation.py <normalized.csv> <output_dir>"
        )

    rows = read_table(sys.argv[1])
    output_dir = Path(sys.argv[2])
    output_dir.mkdir(parents=True, exist_ok=True)

    total_tickets = len(rows)
    lifecycle_counts = Counter(r.get("Ticket_Lifecycle", "Unknown") for r in rows)

    noise = lifecycle_counts.get("Auto-Resolved Noise", 0)
    actionable = lifecycle_counts.get("Actionable Alert", 0)
    blind_spots = lifecycle_counts.get("Monitoring Blind Spot", 0)

    print(f"  Total Tickets       : {total_tickets}", flush=True)
    print(f"  Auto-Resolved Noise : {noise}", flush=True)
    print(f"  Actionable Alerts   : {actionable}", flush=True)
    print(f"  Blind Spots         : {blind_spots}", flush=True)

    # Group by Platform
    by_platform: dict[str, Counter] = {}
    for r in rows:
        p = r.get("Platform", "Unknown")
        if p not in by_platform:
            by_platform[p] = Counter()
        by_platform[p][r.get("Ticket_Lifecycle", "Unknown")] += 1

    platform_stats = []
    for p, counts in sorted(by_platform.items()):
        total = sum(counts.values())
        platform_stats.append({
            "platform": p,
            "total_incidents": total,
            "auto_resolved_noise": counts.get("Auto-Resolved Noise", 0),
            "actionable_alerts": counts.get("Actionable Alert", 0),
            "blind_spots": counts.get("Monitoring Blind Spot", 0),
            "actionable_rate_pct": round(counts.get("Actionable Alert", 0) / total * 100, 1) if total else 0
        })

    # Top blind-spot groups
    blind_spot_rows = [r for r in rows if r.get("Ticket_Lifecycle") == "Monitoring Blind Spot"]
    blind_groups = Counter(r.get("Assignment_Group", "Unknown") for r in blind_spot_rows)
    top_blind = [{"group": g, "unmonitored_business_tickets": c} for g, c in blind_groups.most_common(10)]

    stats = {
        "total_tickets": total_tickets,
        "auto_resolved_noise_count": noise,
        "actionable_alert_count": actionable,
        "blind_spot_count": blind_spots,
        "noise_rate_pct": round(noise / total_tickets * 100, 1) if total_tickets else 0,
        "actionable_rate_pct": round(actionable / total_tickets * 100, 1) if total_tickets else 0,
        "blind_spot_rate_pct": round(blind_spots / total_tickets * 100, 1) if total_tickets else 0,
        "by_platform": platform_stats,
        "top_blind_spot_groups": top_blind,
    }

    # Write summary CSV
    corr_path = output_dir / "business_impact_correlation.csv"
    write_table(corr_path, platform_stats)
    print(f"  Lifecycle metrics -> {corr_path}")

    # LLM gap narrative
    print("  Generating gap narrative...", flush=True)
    gap_text = generate_text(build_gap_prompt(stats), max_output_tokens=2000)
    gap_path = output_dir / "business_impact_gaps.md"
    gap_path.write_text(gap_text.strip() + "\n", encoding="utf-8")
    print(f"  Lifecycle gap narrative -> {gap_path}")

    # Save stats JSON for dashboard
    stats_path = output_dir / "business_impact_stats.json"
    stats_path.write_text(json.dumps(stats, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
