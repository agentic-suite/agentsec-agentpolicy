# Reason codes — reference (v0.1.0)

The **closed, stable** `reason_code` vocabulary emitted by the decision path. The registry lives in
`src/agentpolicy/reason_codes.py` (the single source of truth); this page is generated from it. A code is never
re-used for a different situation. **Alertable** codes are the ones a SIEM should alert on individually
([PRD 17](../prd/17-explain-decision-and-evidence.md) R5).

| `reason_code` | Outcome | Alertable | Meaning |
|---|---|---|---|
| `allow_low_risk` | allow | no | The action is within the allow band. |
| `policy_match` | — | no | An explicit rule decided the outcome. |
| `default_deny` | deny | **yes** | No permit matched (default-deny posture). |
| `irreversible_action` | deny | **yes** | A destructive/irreversible action. |
| `human_gate_required` | ask | **yes** | A human decision is required. |
| `human_gate_timeout` | deny | **yes** | An ask expired without a decision. |
| `budget_exhausted` | rate-limit | **yes** | The session budget is exhausted. |
| `rate_limited` | rate-limit | no | A burst/op-count limit was hit. |
| `secret_detected` | redact | **yes** | Sensitive content was scrubbed from the result. |
| `unknown_action` | deny | **yes** | The action could not be canonicalized. |
| `engine_unavailable` | deny | **yes** | The PDP could not evaluate the action. |
| `policy_unavailable` | deny | **yes** | The policy is missing or malformed. |
| `opa_backend_unavailable` | deny | **yes** | The Rego peer backend was unreachable. |
| `evaluation_timeout` | deny | **yes** | Evaluation exceeded its time budget. |
| `audit_sink_error` | — | **yes** | The audit write failed. |

## How a code is chosen

| Outcome | Code |
|---|---|
| `allow` | `allow_low_risk` |
| `deny` (Cedar `forbid` matched) | `irreversible_action` (destructive class) or `default_deny` (no permit) |
| `ask` | `human_gate_required` |
| `rate-limit` | `budget_exhausted` |
| `redact` | `secret_detected` |

Every `deny`/`ask`/`rate-limit` carries a **clause** — the matched Cedar rule id, or the reason-code class when
no rule decided the outcome. A decision whose `reason_code` is not in the registry raises loudly
(`reason_codes.require`) rather than emitting an unknown code.

## Using the registry

```python
from agentpolicy import reason_codes

reason_codes.is_known("default_deny")     # True
reason_codes.require("default_deny").meaning
reason_codes.alertable_codes()            # the SIEM alert set
```

See the [explain-decision design](../design/explain-decision.md) and the
[agentwatch event binding](../adr/0007-agentwatch-event-schema.md).
