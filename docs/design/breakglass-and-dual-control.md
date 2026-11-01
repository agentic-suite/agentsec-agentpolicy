# Break-Glass & Dual-Control — Design (M18, v0.1.0)

**BLUF:** M18 ships a **time-boxed, fully audited break-glass elevation that reverts automatically at expiry**,
and **dual-control (quorum) approvals** for the irreversible / mandatory human-gate class. The load-bearing
invariant is that **elevation widens scope *ceilings* only — it never bypasses the human gate**; a dual-control
ask still needs its quorum inside an active window. This is the design of record (`18.D0`); it delivers
**CUJ-25** (R40) and **CUJ-26** (R41).

> Status: **Done** — branch `feat-0.1.0`. Modules: `agentpolicy/breakglass.py`, `agentpolicy/dualcontrol.py`,
> `cli/breakglass.py`, `engine/engine.py`, `types.py`.

---

## 1. Break-glass elevation (`18.1`)

`agentpolicy/breakglass.py`:

* `BreakGlassWindow(break_glass_id, agent_id, environments, starts_at, ends_at, reason)` — a **declared,
  time-boxed elevation** for one agent over one or more environments. `is_active(at, env, agent_id)` answers
  whether the window currently elevates the agent in that environment.
* `BreakGlassLedger` — `elevate(agent_id, environments, ends_at, reason=…)` mints a `bg_`-prefixed id and
  records an audited **`elevate`** event; `revert(break_glass_id, at=…)` records an audited **`revert`**
  event; `active_window(agent_id, environment, at=…)` returns the governing window; `events` is the audited
  on/off trail. The ledger persists via `save`/`load` (atomic replace), like the freeze ledger.

**Elevation requires a logged reason** (RK-17): `elevate` rejects a blank reason, so an elevation is never
silent. The default TTL is short and explicit.

**Every decision in the window carries `break_glass_id`.** The engine stamps
`Decision.break_glass_id` on *every* decision evaluated while a window elevates the agent — allow, deny,
escalate alike — so an audit can attribute any action to the elevation that was in force.

## 2. Auto-revert (`18.2`)

Reversion is **automatic, without a manual action**. `BreakGlassLedger.sweep(at=…)` reverts every window whose
`ends_at` has passed and appends a **`revert`** audit event per expiry; `active_window(...)` calls `sweep`
first, so the first evaluation after expiry observes the window as closed and the revert is already logged.
A manual `revert` is also available for the operator (audited the same way). Auto-revert is deterministic: it
is a pure function of `ends_at` and the clock.

## 3. Engine composition & the scope-ceiling guard (`18.4`)

The engine carries an optional `break_glass_ledger`. On `evaluate`, if a window elevates the calling agent in
the call's environment **and the call is *not* in the mandatory human-gate class**, the two *scope* denials are
waived:

* `DENY_OUT_OF_SCOPE` — the identity's environment scope (M2 scoping), and
* `DENY_DELEGATION_EXCEEDS_SCOPE` — the delegation chain's scope-subset proof (M17).

The guard uses `cedar.gates.is_human_gate` — the **single source of truth** for the human-gate class — so a
break-glass window **cannot** widen the human-gate class: a production write still escalates, and (per §5) a
dual-control ask still needs its quorum inside the window. Elevation widens *where an agent may act*, never
*what the human gate covers*.

## 4. Dual-control approvals (`18.3`)

`agentpolicy/dualcontrol.py`:

* `DualControlRecord(dual_control_id, action_identity, quorum, approvers, status, created_at, expires_at)` —
  one quorum-gated approval bound to a call's **action identity** (the M3/M7 `action_identity` hash — one
  canonical identity, no drift).
* `DualControlGate(quorum=2, ttl_seconds=300)` — `request(call)` opens a pending record (audited `request`);
  `approve(record_id, approver)` adds a **distinct** approver and, once the distinct count reaches `quorum`,
  marks the record **released** and records an audited `released` event. A **repeat approval by the same
  principal is rejected** (`ValueError`) — one human cannot make quorum. `resolve(record_id, call)` is the
  engine-facing re-submission check returning `allow` only when the record is released **and** the action
  identity matches; otherwise `deny` with a distinct reason code. Quorum state (the approver set) is audited.

The engine opens a dual-control record when a decision escalates **and the call is in the irreversible /
human-gate class** (`is_human_gate`), keyed to the escalation it creates, and stamps
`Decision.dual_control_id`. The escalation's approval path is therefore quorum-gated for exactly the
irreversible class; a single approval does not release it and two **distinct** approvers do.

## 5. Composition guard (`18.4`)

Break-glass and dual-control **compose**: §3 never waives an escalation, and §4 triggers on the human-gate
class independently of any window. Therefore **inside an active break-glass window a dual-control ask still
applies** — an irreversible action still escalates and still needs two distinct approvers. This is the tested
composition invariant (the WBS acceptance for `18.4`).

## 6. Reason codes & decision shape

Two additive reason codes back dual-control (§ the closed registry in `reason_codes.py`): a pending/partial
quorum resolves to a deny (`dual_control_not_released`) and a released quorum resolves to an allow
(`allow_dual_control_approved`). `types.Decision` gains two additive, optional fields — `break_glass_id` and
`dual_control_id` — so provenance travels with the decision, mirroring `freeze_id`.

## 7. WBS M18 item mapping

| Item | Where |
|---|---|
| 18.D0 design docs first | this document |
| 18.1 break-glass elevation | `agentpolicy/breakglass.py`, `cli/breakglass.py`, `engine/engine.py`, `types.py` |
| 18.2 auto-revert | `BreakGlassLedger.sweep` / `active_window` (audited `revert` events) |
| 18.3 dual-control approvals | `agentpolicy/dualcontrol.py`, `engine/engine.py` |
| 18.4 composition guard | `engine/engine.py` (scope-ceiling waiver gated on `is_human_gate`) |
| 18.T/18.C/18.L/18.CR/18.D | tests · coverage · ruff/mypy · [codereview-log](../wbs/v0.1.0/codereview-log.md) · [break-glass reference](../reference/break-glass-and-dual-control.md) |
