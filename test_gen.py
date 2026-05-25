#!/usr/bin/env python3
import sys
import json
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional
import html as html_module

ROOT = Path(__file__).resolve().parents[0]
OUTPUT = ROOT / "data" / "output"

def load_csv_as_json(filename: str) -> Optional[List[Dict[str, Any]]]:
    path = OUTPUT / filename
    if not path.exists():
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return None

def load_json_file(filename: str) -> Optional[Dict[str, Any]]:
    path = OUTPUT / filename
    if not path.exists():
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return None

def load_markdown(filename: str) -> Optional[str]:
    path = OUTPUT / filename
    if not path.exists():
        return None
    try:
        return path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return None

print("Loading data files...")
incidents_scored = load_csv_as_json("incidents_scored.csv")
platform_quality = load_csv_as_json("platform_quality_metrics.csv")
missing_fields = load_csv_as_json("missing_field_summary.csv")
ai_recommendations = load_csv_as_json("ai_recommendations.csv")
qa_alerts = load_csv_as_json("qa_fidelity_alerts.csv")

business_impact_stats = load_json_file("business_impact_stats.json")
long_running_stats = load_json_file("long_running_stats.json")
log_standards_json = load_json_file("log_standards.json")

print(f"Incidents loaded: {len(incidents_scored) if incidents_scored else 0}")
print(f"Platform data loaded: {len(platform_quality) if platform_quality else 0}")
print(f"Missing fields loaded: {len(missing_fields) if missing_fields else 0}")
print(f"AI recommendations loaded: {len(ai_recommendations) if ai_recommendations else 0}")
print(f"QA alerts loaded: {len(qa_alerts) if qa_alerts else 0}")
print(f"Business impact stats: {bool(business_impact_stats)}")
print(f"Long running stats: {bool(long_running_stats)}")
print(f"Log standards JSON: {bool(log_standards_json)}")

print("\n✓ All data loaded successfully!")
