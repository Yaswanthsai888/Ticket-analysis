# AIOps Log Fidelity Standards

## Platform: New Relic

### 1. Mandatory Fields

Every New Relic incident log **MUST** contain the following fields:

| Field Name | Current Coverage | Target Coverage | Priority |
|------------|------------------|-----------------|----------|
| Event Timestamp (ISO 8601) | 100% | 100% | ✓ Met |
| Source Monitoring System | 100% | 100% | ✓ Met |
| Service / Business Component Name | 100% | 100% | ✓ Met |
| Correlation ID / Trace ID / Issue ID | 100% | 100% | ✓ Met |
| Metric Value & Threshold / Trigger Condition | 100% | 100% | ✓ Met |
| Payload / Alert Policy / Additional Attributes | 100% | 100% | ✓ Met |
| **Impacted Host / Pod / CI / SAP Component** | **30.3%** | **100%** | **🔴 CRITICAL** |
| **Error Code / Alert Code / Exception ID** | **13.9%** | **100%** | **🔴 CRITICAL** |
| **Direct Alert / Trace / Dashboard URL** | **9.6%** | **100%** | **🔴 CRITICAL** |
| **Root Cause Analysis** | **14.9%** | **90%** | **🔴 CRITICAL** |
| **Action Taken / Workaround / Permanent Fix** | **37.7%** | **90%** | **🔴 CRITICAL** |

### 2. AIOps Self-Healing Requirements

For automated remediation eligibility, incidents **MUST** include:

| Field | Purpose | Format | Automation Impact |
|-------|---------|--------|-------------------|
| **Correlation ID** | Link related events across services | UUID v4 | Enables event correlation & deduplication |
| **Impacted Host / Pod / CI** | Target for remediation actions | `<env>:<cluster>:<namespace>:<pod-name>` or `<hostname>` | Identifies where to execute runbooks |
| **Error Code** | Map to known failure patterns | Alphanumeric, 6-12 chars (e.g., `NR-APM-5001`) | Triggers specific remediation playbooks |
| **Metric Value & Threshold** | Validate severity & recovery | `<metric>=<value> (threshold: <operator><limit>)` | Determines urgency & success criteria |
| **Direct Alert URL** | Enable one-click investigation | Valid HTTPS URL | Accelerates human-in-the-loop validation |

### 3. Field Format Specifications

```yaml
event_timestamp:
  format: ISO 8601 with timezone
  example: "2024-01-15T14:32:18.456Z"
  regex: '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$'

source_monitoring_system:
  format: Static identifier
  example: "New Relic"
  allowed_values: ["New Relic"]

service_name:
  format: Kebab-case, alphanumeric + hyphens
  example: "payment-gateway-api"
  regex: '^[a-z0-9]+(-[a-z0-9]+)*$'
  max_length: 64

impacted_entity:
  format: Hierarchical path notation
  examples:
    - "prod:us-east-1:payments:payment-gateway-api-7d4f9c8b-xk2p9"
    - "prod-app-server-03.example.com"
  pattern: '<env>:<region/cluster>:<namespace>:<resource>' OR '<fqdn>'

error_code:
  format: Platform prefix + category + sequence
  example: "NR-APM-5001"
  pattern: 'NR-<CATEGORY>-<CODE>'
  categories: ["APM", "INFRA", "SYNTH", "BROWSER", "MOBILE"]
  regex: '^NR-[A-Z]+-\d{4,5}$'

metric_threshold:
  format: Structured key-value with comparison
  example: "response_time_ms=2847 (threshold: >2000)"
  pattern: '<metric_name>=<value> (threshold: <operator><limit>)'

direct_url:
  format: Fully qualified HTTPS URL
  example: "https://one.newrelic.com/launcher/nr1-core.explorer?pane=eyJuZXJkbGV0SWQiOiJhbGVydGluZy11aS1jbGFzc2ljLmlzc3VlLWRldGFpbHMiLCJpc3N1ZUlkIjoiMTIzNDU2In0"
  validation: Must return HTTP 200-399

correlation_id:
  format: UUID v4
  example: "550e8400-e29b-41d4-a716-446655440000"
  regex: '^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'

payload_attributes:
  format: JSON object
  required_keys: ["policy_name", "condition_name", "severity"]
  example: '{"policy_name":"Production API SLA","condition_name":"Response Time P95","severity":"critical","account_id":"1234567"}'

root_cause_analysis:
  format: Structured text with category
  example: "[CAPACITY] CPU throttling due to pod resource limits (200m request, 500m spike observed)"
  pattern: '[<CATEGORY>] <description>'
  categories: ["CAPACITY", "DEPENDENCY", "CODE", "CONFIG", "EXTERNAL"]
  min_length: 20

action_taken:
  format: Structured action log
  example: "[AUTO] Scaled deployment from 3 to 5 replicas | [MANUAL] Increased CPU limit to 1000m"
  pattern: '[<TYPE>] <action_description>'
  types: ["AUTO", "MANUAL", "WORKAROUND", "PERMANENT_FIX"]
```

### 4. Sample Log Template

```json
{
  "event_timestamp": "2024-01-15T14:32:18.456Z",
  "source_monitoring_system": "New Relic",
  "service_name": "payment-gateway-api",
  "impacted_entity": "prod:us-east-1:payments:payment-gateway-api-7d4f9c8b-xk2p9",
  "error_code": "NR-APM-5001",
  "metric_threshold": "response_time_p95_ms=2847 (threshold: >2000)",
  "direct_url": "https://one.newrelic.com/launcher/nr1-core.explorer?pane=eyJuZXJkbGV0SWQiOiJhbGVydGluZy11aS1jbGFzc2ljLmlzc3VlLWRldGFpbHMiLCJpc3N1ZUlkIjoiMTIzNDU2In0",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "payload": {
    "policy_name": "Production API SLA",
    "condition_name": "Response Time P95 > 2s",
    "severity": "critical",
    "account_id": "1234567",
    "entity_guid": "MTIzNDU2fEFQTXxBUFBMSUNBVElPTnw4OTAxMjM0",
    "duration_seconds": 420,
    "violation_chart_url": "https://chart.apis.newrelic.com/v2/..."
  },
  "root_cause_analysis": "[CAPACITY] CPU throttling detected - pod resource limit (200m) exceeded by sustained load. P95 latency correlated with CPU usage >95%.",
  "action_taken": "[AUTO] Horizontal pod autoscaler triggered - scaled from 3 to 5 replicas at 14:33:45Z | [MANUAL] Increased CPU limit from 200m to 500m in deployment manifest at 14:45:12Z"
}
```

### 5. Automation Readiness Gate

An incident is **eligible for AIOps automated resolution** when it meets ALL criteria:

| # | Criterion | Validation Method | Pass/Fail |
|---|-----------|-------------------|-----------|
| 1 | Contains valid `correlation_id` (UUID v4) | Regex match | Required |
| 2 | `impacted_entity` resolves to active infrastructure | Query CMDB/K8s API | Required |
| 3 | `error_code` exists in remediation playbook registry | Lookup in automation catalog | Required |
| 4 | `metric_threshold` parseable with numeric values | Parse & type check | Required |
| 5 | `direct_url` returns HTTP 200-399 | HTTP GET request | Required |
| 6 | Event age < 15 minutes | Compare `event_timestamp` to current time | Required |
| 7 | `severity` in payload is "critical" or "high" | JSON path validation | Recommended |
| 8 | No conflicting automation in progress for same `impacted_entity` | Check automation lock table | Required |

**Automation Eligibility Formula:**
```
automation_ready = (mandatory_fields_present == 8/8) AND 
                   (format_validation_passed == TRUE) AND
                   (entity_exists == TRUE) AND
                   (playbook_mapped == TRUE)
```

---

## Platform: SAP Cloud ALM

### 1. Mandatory Fields

Every SAP Cloud ALM incident log **MUST** contain the following fields:

| Field Name | Current Coverage | Target Coverage | Priority |
|------------|------------------|-----------------|----------|
| Event Timestamp (ISO 8601) | 100% | 100% | ✓ Met |
| Source Monitoring System | 100% | 100% | ✓ Met |
| Service / Business Component Name | 100% | 100% | ✓ Met |
| Error Code / Alert Code / Exception ID | 100% | 100% | ✓ Met |
| Action Taken / Workaround / Permanent Fix | 99.5% | 100% | ⚠️ Near Target |
| **Impacted Host / Pod / CI / SAP Component** | **0.0%** | **100%** | **🔴 CRITICAL** |
| **Metric Value & Threshold / Trigger Condition** | **0.0%** | **100%** | **🔴 CRITICAL** |
| **Correlation ID / Trace ID / Issue ID** | **0.0%** | **100%** | **🔴 CRITICAL** |
| **Payload / Alert Policy / Additional Attributes** | **0.0%** | **100%** | **🔴 CRITICAL** |
| **Direct Alert / Trace / Dashboard URL** | **2.5%** | **100%** | **🔴 CRITICAL** |
| **Root Cause Analysis** | **5.8%** | **90%** | **🔴 CRITICAL** |

### 2. AIOps Self-Healing Requirements

For automated remediation eligibility, incidents **MUST** include:

| Field | Purpose | Format | Automation Impact |
|-------|---------|--------|-------------------|
| **Correlation ID** | Link SAP transactions & BTP events | GUID (32 hex chars) | Enables cross-system trace correlation |
| **Impacted SAP Component** | Target for remediation | `<SID>:<client>:<component>:<instance>` | Identifies SAP system/work process |
| **Error Code** | Map to SAP Note / OSS message | SAP format (e.g., `SAPSQL-008`) |
