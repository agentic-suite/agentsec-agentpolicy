# Enrollment, probation & approval analytics — reference (v0.1.0)

WBS M16 · CUJ-22 / CUJ-23 · R35 / R36. Design: [enrollment-approvals.md](../design/enrollment-approvals.md).

## Enrollment & probation (`16.1`)

A **first-seen unknown agent** lands in **probation**: reads proceed, a **gated write escalates** with reason
`agent_probation` until a human classifies it.

```python
from agentpolicy.enrollment import EnrollmentLedger, EnrollmentStatus
from agentpolicy.engine.engine import Engine
from agentpolicy.policy.models import default_policy

ledger = EnrollmentLedger()
engine = Engine(default_policy("balanced"), enrollment=ledger)

engine.evaluate(tool_name="deploy_service", action="write", environment="production",
                data_class="internal", agent_id="new-agent").reason_code   # "agent_probation"
ledger.classify("new-agent", EnrollmentStatus.ENROLLED, by="alice")        # logged event
engine.evaluate(tool_name="deploy_service", action="write", environment="production",
                data_class="internal", agent_id="new-agent").reason_code   # no longer probation
```

The `packs/enrollment-probation` pack carries the posture as a Cedar rule class.

## agentwatch inventory link (`16.4`)

```python
from agentpolicy.agentwatch import classification_event
classification_event("new-agent", "enrolled", agent_class="ci-bot")
# {"event_type": "agent.classification", "schema": "agentwatch.security_event.v1", …}
```

## Approval analytics (`16.3`)

```sh
agentpolicy report approvals
agentpolicy report approvals --json
```

| Field | Meaning |
|---|---|
| `approved` / `denied` / `expired` / `pending` | gate outcomes |
| `approval_rate` | approved / (approved + denied) |
| `mean_latency_seconds` | mean `created_at`→`resolved_at` (M16 adds `resolved_at` to both gate records) |
| `shadow_delta` | blocked-rate in shadow minus blocked-rate enforced |
| `rubber_stamp_gates` | gates approved ≥ `rubber_stamp_threshold` with ≥ `min_approvals` — **flagged** |

```python
from agentpolicy.approvals import analyze_approvals
report = analyze_approvals(escalations, asks, audit_entries=entries)
report.rubber_stamp_gates    # a gate that is (almost) always approved
```
