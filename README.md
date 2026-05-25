# Log Fidelity Assessment POC

This proof of concept assesses whether monitoring-generated incidents contain enough detail for fast troubleshooting, root cause analysis, and future self-healing automation.

The pipeline accepts ServiceNow-style incident exports from New Relic, SAP Cloud ALM, manual resolver notes, or similar monitoring platforms. It normalizes the data, extracts log-quality signals, scores each incident, aggregates platform-level metrics, and generates recommendations.

## Quick Start

Create a `.env` file first:

```text
OPENAI_API_KEY=your_key_here
OPENAI_BASE_URL=https://servicesessentials.ibm.com/apis/v3
OPENAI_MODEL=global/anthropic.claude-sonnet-4-5-20250929-v1:0
```

```powershell
python run_pipeline.py --input data/input/sample_incidents.csv
```

For large datasets, keep the LLM calls bounded:

```powershell
python run_pipeline.py --input data/input/full_export.csv --max-llm-segments 12 --examples-per-segment 5
```

This scores every incident locally, then sends only segment summaries and representative examples to the LLM.

Outputs are written to:

```text
data/output/
```

Key outputs:

- `incidents_normalized.csv`
- `incidents_signals.csv`
- `incidents_scored.csv`
- `platform_quality_metrics.csv`
- `missing_field_summary.csv`
- `ai_recommendations.csv` generated through bounded segment-level LLM calls
- `executive_summary.md` generated through the configured LLM

## Dashboard

Install optional dashboard dependencies, then run:

```powershell
streamlit run src/dashboard.py
```

## Scoring Dimensions

| Dimension | Weight |
|---|---:|
| Technical Completeness | 25 |
| Granularity | 20 |
| Actionability | 20 |
| RCA Readiness | 15 |
| Trustworthiness | 10 |
| Automation Readiness | 10 |

## Good Log Principle

A production monitoring incident should clearly answer:

- What failed?
- Where did it fail?
- When did it fail?
- How severe is it?
- What metric, threshold, or condition triggered it?
- Which service, host, pod, transaction, or entity was impacted?
- Which correlation or issue ID links it to the source system?
- What should support check first?
- What fixed it?
- Is it specific enough for automation?
