# Parity / absorption ledger — reference (v0.1.0)

WBS M23 `23.5` · PRD 10. Design: [hardening-and-nfrs.md](../design/hardening-and-nfrs.md).

Every predecessor (the retired, private policy engine) capability the WBS porting map lists is recorded with a
status of **delivered**, **delegated**, or **waived** (with a reason). The gate is **green == no silent drops**.

```python
from agentpolicy.parity import parity_gate, parity_report
parity_gate()    # [] — nothing dropped without delivery or a written waiver
parity_report()  # {total, by_status, entries}
```

| Capability | Status | Where |
|---|---|---|
| Decision engine (allow/audit/escalate/deny + risk) | delivered | `cedar/` (five outcomes), `engine/` |
| Action taxonomy (13 domains) | delivered | `taxonomy/`, `canonical.py` |
| Explainability + reason codes + criticality | delivered | `explain.py`, `reason_codes.py` |
| Audit log (JSONL/SQLite/Postgres) + policy version | delivered | `audit/`, `cedar/policy.policy_hash` |
| Escalation round-trip | delivered | `engine/escalation.py`, `ask.py` |
| Delivery surfaces + adapters | delivered | `api.py`, `adapters/`, `server/`, `cli/` |
| Posture presets + init + diff | delivered | `policy/`, `cli/init.py`, `cli/diff.py` |
| Shadow mode + calibration | delivered | `calibration.py`, `canary.py` |
| Session state (budgets, rate limits) | delivered | `session_store.py`, `engine/` |
| Argument validation + output inspection | delivered | `engine/argument_policy.py`, `redaction.py` |
| Adversarial normalization | delivered | `engine/normalize.py`, `dispatcher.py` |
| OWASP mapping + security baseline | delivered | `compliance.py`, `SECURITY_BASELINE.md` |
| OPA/Rego peer backend | delivered | `policy/opa.py` |
| Legacy policy YAML schema + loader | delivered | `policy/{schema,loader,models}.py` |

The v0.1.0 **deferred-optional** items are tracked separately in
[hardening-and-nfrs.md](hardening-and-nfrs.md) §Deferred-optional: OPA→Cedar migration assistant (R13), pack
marketplace (R14), and fleet sync (R31) are **waived with reasons**.
