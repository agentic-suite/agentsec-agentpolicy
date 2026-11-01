# Session State, Blast-Radius Budgets & Rate Limits — Design (M12, v0.1.0)

**BLUF:** M12 adds the novel class nobody else ships: **cumulative, per-session capability ceilings** (*10 files,
20 requests, $5 — then stop*) plus **rate/burst limits** with a `retry_after` the agent can honor. Session state
accumulates across a session (splitting calls cannot evade a cap), every decision carries its **budget state**, and
hard exhaustion raises an **agenthalt** event with evidence. This is the design of record (`12.D0`); it delivers
**CUJ-12**, **CUJ-18** (R9, R17, R23).

> Status: **Done** — branch `feat/0.1.0`. Modules: `server/session_store.py` (usage/budgets/rate),
> `server/server_core.py` (enforcement), `agenthalt.py` (halt trigger).

---

## 1. Session/context state (`12.1`)

`SessionState` already accumulates `risk_score`, `tool_call_count`, `consent_scopes`, and a rolling
`decision_history` (replayable by `session_id` via the audit trail, M6). M12 adds **generic usage counters**
(`usage: dict[str, float]`) and **capability ceilings** (`budgets: dict[str, float]`) keyed by dimension
(`files`, `requests`, `spend`, `calls`). `SessionStore.record_usage(session_id, usage)` accumulates them
thread-safely; `budget_state(session_id)` returns `{budgets, usage, over}`.

## 2. Blast-radius budgets (`12.2`)

`SessionStore.exceeds_budgets(session_id)` names the first dimension whose usage crosses its ceiling. The server
records implicit `requests`/`calls` on every call plus any explicit `usage` the caller supplies, then, on
exhaustion, returns a **`rate-limit`** decision with `reason_code="budget_exhausted"` and `retry_after=60` — an
exhausted capability is *throttled with a reason*, not an opaque deny. **Every** decision (allow included)
carries `budget_state`, so a caller/operator can see where the session stands.

The legacy `call_budget` is folded into the `calls` dimension, so existing callers keep working with the new
semantics.

## 3. Rate/burst limits (`12.3`)

`SessionStore.rate_allow(session_id)` runs a token bucket configured at session creation (`rate_limit` per
second, `burst_limit` tokens) and returns `(allowed, retry_after)` — the whole seconds until the next token.
A throttled call returns a **`rate-limit`** decision with `reason_code="rate_limited"` and the `retry_after`, so
a runaway loop is throttled and the agent can honor the retry (R23).

## 4. agenthalt integration (`12.4`)

`agenthalt.HaltController.maybe_halt(session_id, budget_state)` fires a **`HaltEvent`** when a dimension is over
its hard ceiling, carrying the `budget_state` as **evidence**; the server attaches the event to the decision
(`result["halt"]`) and may notify agentwatch/agenthalt via an `on_halt` callback. The controller is a pure
observer — it never changes the decision, and a failing callback is swallowed.

## 5. Fail-closed / determinism

* A dimension with **no** declared ceiling is never a ceiling (no accidental caps).
* Counting is cumulative per session, so splitting a workload across calls cannot evade a cap.
* The rate bucket is time-based but the *decision* stays deterministic given session state; the halt trigger is a
  pure function of the budget state.

## 6. WBS M12 item mapping

| Item | Where |
|---|---|
| 12.D0 design docs first | this document |
| 12.1 session/context state | `server/session_store.py` (`usage`/`budgets`) |
| 12.2 blast-radius budgets | `session_store.exceeds_budgets` + `server_core` enforcement |
| 12.3 rate/burst limits | `session_store.rate_allow` + `server_core` |
| 12.4 agenthalt integration | `agenthalt.py` + `server_core` |
| 12.T/12.C/12.L/12.CR/12.D | tests · coverage · ruff/mypy · [codereview-log](../wbs/v0.1.0/codereview-log.md) · [budgets reference](../reference/budgets-and-rate-limits.md) |
