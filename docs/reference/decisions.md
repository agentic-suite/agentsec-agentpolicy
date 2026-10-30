# Decisions Reference

The five-outcome decision model of the Cedar decision core (WBS M2, PRD 15/17).

## Outcomes

| `decision` | Meaning | Extra fields |
|---|---|---|
| `allow` | execute normally | — |
| `deny` | blocked, with a matched rule/reason | — |
| `ask` | human approval required | — |
| `rate-limit` | throttled by a session budget | `retry_after` |
| `redact` | allowed, but sensitive output is scrubbed | `redactions[]` |

## Criticality

`none` · `low` · `med` · `high` · `critical`

## Reason codes (seed)

| `reason_code` | Outcome | Meaning |
|---|---|---|
| `allow_low_risk` | allow | within the allow band |
| `no_matching_permit` | deny | no Cedar `permit` matched (fail-closed) |
| `irreversible_action` | deny | a destructive verb matched a `forbid` |
| `human_gate_required` | ask | an irreversible action in production needs approval |
| `budget_exhausted` | rate-limit | the session budget is exhausted |
| `sensitive_output` | redact | a sensitive read was allowed but scrubbed |

## JSON shape

```json
{
  "decision": "deny",
  "reason_code": "irreversible_action",
  "criticality": "critical",
  "explanation": "drop_database (delete) in production on customer_pii is blocked: destructive operation.",
  "factors": [
    {"dimension": "action_class", "value": "delete", "contribution": 1.0},
    {"dimension": "environment", "value": "production", "contribution": 0.8},
    {"dimension": "data_class", "value": "customer_pii", "contribution": 1.0}
  ],
  "policy_version": "0.1.0",
  "matched_rule": null
}
```

`rate-limit` decisions also carry `retry_after` (seconds); `redact` decisions carry `redactions` (e.g. `["pii"]`).

## In-process use

```python
from agentpolicy.cedar import CedarEvaluator
from agentpolicy.types import NormalizedCall

call = NormalizedCall(
    tool="deploy_service", tool_category="cloud", action="write", action_class="write",
    environment="production", data_class="restricted", agent_id="release-bot", agent_class="ci-bot",
)
decision = CedarEvaluator().evaluate(call)
print(decision.decision)     # "ask"
print(decision.reason_code)  # "human_gate_required"
```

## Invariants

- **Deterministic** — same call + policy ⇒ same decision.
- **Fail-closed** — no permit ⇒ `deny`; a malformed policy is rejected at construction.
- **Explainable** — every outcome carries a `reason_code`, `criticality`, `explanation`, and `factors[]`.
