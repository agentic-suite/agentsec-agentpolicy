# Blast-radius budgets & rate limits — reference (v0.1.0)

WBS M12 · CUJ-12 / CUJ-18 · R9 / R17 / R23. Design: [budgets-rate-limits.md](../design/budgets-rate-limits.md).

Per-session **capability ceilings** (*10 files, 20 requests, $5 — then stop*) plus **rate/burst limits**. Every
decision carries its `budget_state`; exhaustion returns a **`rate-limit`** with a `retry_after`.

## Creating a session with budgets

```python
from agentpolicy.server.session_store import SessionStore

store = SessionStore()
store.get_or_create(
    "sess_1",
    budgets={"files": 10, "requests": 20, "spend": 5, "calls": 50},
    rate_limit=5.0,        # calls/second
    burst_limit=10,        # token bucket size
)
store.record_usage("sess_1", {"files": 3, "spend": 0.75})
store.budget_state("sess_1")   # {"budgets": {...}, "usage": {...}, "over": [...]}
store.exceeds_budgets("sess_1")  # (bool, reason)
store.rate_allow("sess_1")       # (allowed, retry_after)
```

## Enforcement (server)

`ServerCore.evaluate(..., budgets=…, rate_limit=…, burst_limit=…, usage=…)`:

| Situation | `decision` | `reason_code` | extra |
|---|---|---|---|
| within budget | the engine decision | — | `budget_state` |
| any ceiling crossed | `rate-limit` | `budget_exhausted` | `retry_after=60`, `halt` |
| rate/burst hit | `rate-limit` | `rate_limited` | `retry_after` |
| outside consent scope | `escalate` | `scope_boundary` | — |

Calling a `call_budget=N` session maps to `budgets={"calls": N}` (back-compatible).

## agenthalt

Hard exhaustion raises a halt event (evidence = the budget state):

```python
from agentpolicy.agenthalt import HaltController
controller = HaltController(on_halt=lambda e: notify_agentwatch(e.to_dict()))
```

`result["halt"]` is `{"kind": "session_halt", "session_id", "reason", "evidence", "at"}`.

## Guarantees

- **Cumulative** — counting is per session, so splitting a workload cannot evade a cap.
- **Reasoned** — exhaustion is a `rate-limit` with `budget_exhausted` + `retry_after`, never a silent deny.
- **Visible** — `budget_state` is on every decision.
