# Enrollment / Probation & Approval Analytics — Design (M16, v0.1.0)

**BLUF:** M16 makes first-seen agents **safe by default**. A previously unknown agent lands in **probation**
(reads + audit; **ask-on-write**) until a human **classifies** it — a logged event that feeds the fleet
inventory. It also ships **approval analytics**: an approval-rate / latency / shadow→enforce report that
**flags rubber-stamp gates**. This is the design of record (`16.D0`); it delivers **CUJ-22**, **CUJ-23**
(R35, R36).

> Status: **Done** — branch `feat/0.1.0`. Modules: `agentpolicy/enrollment.py`, `agentpolicy/approvals.py`,
> `agentwatch.classification_event`, `cli/report.py` (`report approvals`), `packs/enrollment-probation/`.

---

## 1. Enrollment ledger + probation (`16.1`)

`agentpolicy/enrollment.py`:

* `Enrollment(agent_id, status, agent_class, first_seen, classified_by, classified_at)`.
* `EnrollmentLedger.observe(agent_id)` — a **first-seen** agent is recorded as `PROBATION` and a `probation`
  **event** is logged (idempotent).
* `EnrollmentLedger.classify(agent_id, status, by=…)` — sets `ENROLLED`/`BLOCKED` and logs a `classification`
  event; unknown agent / blank classifier / re-classifying to `PROBATION` are rejected loudly.

The engine carries an optional ledger. On `evaluate`, a probationary agent's **gated action** (the write set) is
**escalated** with reason code `agent_probation`, so a human must classify it before the first write; **reads
proceed** (and are audited). No shadow IdP — the ledger is the source of truth.

## 2. Probation policy pack (`16.2`)

`packs/enrollment-probation` ships the posture as a Cedar rule class
(`@id("enrollment-probation-gate")`, keyed on `context.agent_class == "probation"`), proven by its `tests.yaml`
replay (probation write gated; an enrolled read allowed).

## 3. Approval analytics (`16.3`)

`agentpolicy/approvals.py` — `analyze_approvals(escalations, asks, audit_entries=…)`:
**approval rate**, **mean latency** (from `created_at`→`resolved_at`, which M16 adds to both gate records), the
**shadow→enforce delta** (blocked-rate in shadow minus enforced), and the **rubber-stamp gates** — a gate
approved (almost) every time is flagged (`rubber_stamp_threshold`, `min_approvals`). `agentpolicy report
approvals [--json]` exposes it, while `agentpolicy report` keeps its existing behaviour.

## 4. agentwatch inventory link (`16.4`)

`agentwatch.classification_event(agent_id, status, …)` emits an `agentwatch.security_event.v1` event with
`event_type="agent.classification"`, so a first-seen/probation and a later classification are visible to
agentwatch/agentcomply as the agent's state changes.

## 5. WBS M16 item mapping

| Item | Where |
|---|---|
| 16.D0 design docs first | this document |
| 16.1 enrollment ledger + probation | `agentpolicy/enrollment.py`, `engine/engine.py` |
| 16.2 `enrollment-probation` pack | `packs/enrollment-probation/` |
| 16.3 approval analytics | `agentpolicy/approvals.py`, `cli/report.py` |
| 16.4 agentwatch inventory link | `agentwatch.py` (`classification_event`) |
| 16.T/16.C/16.L/16.CR/16.D | tests · coverage · ruff/mypy · [codereview-log](../wbs/v0.1.0/codereview-log.md) · [enrollment/approvals reference](../reference/enrollment-and-approvals.md) |
