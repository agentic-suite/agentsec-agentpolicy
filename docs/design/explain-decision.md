# Explain-Decision, Reason Codes & Event Schema — Design (M5, v0.1.0)

**BLUF:** M5 makes every Cedar decision **explainable** and **emitted**. Every decision carries a
machine-readable `reason_code` from a **closed, stable registry**, a human `explanation`, a `criticality`, the
`factors[]`, the `matched_rule`, and the **one change that flips it** (`suggested_change`). Every decision is
emitted in the **agentwatch security-event schema** (`agentwatch.security_event.v1`, `policy.decision`) with a
shared `event_id`/`decision_id` join key. This is the design of record (`5.D0`); it delivers **CUJ-3** and
**R5/R6** ([PRD 17](../../prd/17-explain-decision-and-evidence.md)).

> Status: **Done** — branch `feat-0.1.0`. Modules: `src/agentpolicy/reason_codes.py`,
> `src/agentpolicy/explain.py`, `src/agentpolicy/agentwatch.py`; the Cedar core
> (`src/agentpolicy/cedar/`) is the decision path. No ML and no network in the path.

---

## 1. The explain contract (`5.1`)

The artifact is the machine-readable form of the decision — one artifact, two audiences (operator: full
fidelity; agent: curated, no policy internals). It is built from a finished Cedar `Decision` plus the canonical
call:

```json
{
  "decision": "deny",
  "reason_code": "irreversible_action",
  "criticality": "critical",
  "explanation": "Delete on production customer-PII data is blocked by the destructive-command rule.",
  "factors": [
    { "dimension": "action_class", "value": "delete",     "contribution": 1.0 },
    { "dimension": "environment",  "value": "production", "contribution": 0.8 },
    { "dimension": "data_class",   "value": "customer_pii","contribution": 1.0 },
    { "dimension": "tool_category","value": "db",         "contribution": 0.4 }
  ],
  "matched_rule": "forbid-destructive-production",
  "clause": "forbid-destructive-production",
  "suggested_change": "Use a read-only alternative, or move the action to a non-production environment.",
  "policy_version": "0.1.0",
  "policy_hash": "sha256:...",
  "event_id": "evt_..."
}
```

**Every deny names a clause.** `clause` is `matched_rule` when a Cedar rule decided the outcome, else the
`reason_code` (the *class* — e.g. `default_deny` for a no-permit default-deny, which by definition has no
matched rule). Invariant (PRD 15): a `deny`/`ask`/`rate-limit` always carries a non-empty `clause`.

`matched_rule` is the Cedar `@id` annotation of the deciding policy (`forbid-*` for a deny, `permit-*` for an
`ask`/`rate-limit`/`redact`); it is populated on `deny`/`ask`/`rate-limit`/`redact`. On a plain `allow` it is
left `null` in v0.1.0 — allow-justification (R47, "who authorized this?") is a **v0.2.0** requirement
([PRD 17](../../prd/17-explain-decision-and-evidence.md) §Requirements).

## 2. Reason-code registry (`5.2`)

`src/agentpolicy/reason_codes.py` is the **single source of truth** for the reason-code vocabulary. A code is
`(code, meaning, alertable)`; `alertable` marks codes a SIEM should alert on individually. The Cedar shaper
**imports** these constants — no inline string literals — so a code cannot drift between the decision path and
the docs.

| `reason_code` | Emitted by | Alertable |
|---|---|---|
| `allow_low_risk` | shaper `allow` (within the allow band) | no |
| `policy_match` | shaper (an explicit rule decided the outcome) | no |
| `default_deny` | shaper `deny` (no permit matched — default-deny posture) | **yes** |
| `irreversible_action` | shaper `deny` (destructive/irreversible class) | **yes** |
| `human_gate_required` | shaper `ask` (mandatory human gate) | **yes** |
| `human_gate_timeout` | the ask broker, on expiry → deny (M7) | **yes** |
| `budget_exhausted` | shaper `rate-limit` (session budget) | **yes** |
| `rate_limited` | burst/op-count limiter (M12) | no |
| `secret_detected` | shaper `redact` (secret/PII scrubbed from output) | **yes** |
| `unknown_action` | canonicalizer (action could not be canonicalized) | **yes** |
| `engine_unavailable` | engine (PDP could not evaluate) | **yes** |
| `policy_unavailable` | loader (policy missing/malformed) | **yes** |
| `opa_backend_unavailable` | OPA peer backend unreachable | **yes** |
| `evaluation_timeout` | evaluator exceeded its budget | **yes** |
| `audit_sink_error` | audit write failed (decision still stands) | **yes** |

> **Re-point note.** M2 emitted the legacy codes `no_matching_permit` and `sensitive_output`; M5 replaces them
> with the PRD-canonical `default_deny` and `secret_detected`. The two dependents' assertions
> (`tests/test_cedar_core.py`) move with the work. `rate_limited`/`human_gate_timeout`/`policy_unavailable`/
> `engine_unavailable` are reserved here and wired by their owning milestones (M7/M12), so the vocabulary is
> closed from day one.

## 3. Actionability (`5.3`)

The **actionability test** is an automated acceptance test (R5), not a vibe:

> A human given **only** the explanation text and the original action can name the one change (approve, move to
> staging, lower data class, reduce scope) that would change the outcome — without consulting documentation.

`explain.suggested_change(decision, call, evaluator)` computes the single flip deterministically: it evaluates a
**fixed, ordered** list of candidate modifications of the call (production→staging, destructive→read-only
sibling, drop the irreversible verb, lower the data class) and returns the first one whose Cedar outcome
changes. The order is frozen so the suggestion is stable across installs. When no candidate flips the outcome
(a hard class deny), it returns a safe generic alternative. `explain.flip_variant(...)` exposes the winning
candidate (used by CI and by the `permitted_alternatives` work in a later milestone).

The **CI actionability test** (`tests/test_m5_explain.py::TestActionability`) drives every deny/ask/rate-limit in
the acceptance matrix and asserts that (a) the `clause` is non-empty, (b) the `suggested_change` names a
concrete lever from a closed vocabulary, and (c) for a representatively flip-able call, applying the suggested
change really does change the outcome.

## 4. `agentpolicy explain` (`5.4`)

`agentpolicy explain --tool ... --action ... --env ... --data ... --agent ...` evaluates the call **offline**
through the canonicalizer + Cedar evaluator (no server, no network) and prints the full factor breakdown, the
matched rule/clause, the reason code, and the suggested change. `--json` prints the explain artifact verbatim
so a script can consume it. This re-points the command from the ported engine to the v0.1.0 Cedar path.

## 5. Event emitter — agentwatch (`5.5`, R6)

`src/agentpolicy/agentwatch.py` renders every decision as an `agentwatch.security_event.v1` event
(`event_type: policy.decision`) per [ADR-0007](../../adr/0007-agentwatch-event-schema.md) / PRD 15:

```json
{
  "schema": "agentwatch.security_event.v1",
  "event_type": "policy.decision",
  "event_id": "evt_...",
  "decision_id": "dec_...",
  "principal": { "agent_id": "release-bot", "agent_class": "ci-bot" },
  "action": { "verb": "delete", "tool": "drop_database", "args_hash": "sha256:..." },
  "resource": { "tool_category": "db", "environment": "production", "data_class": "customer_pii" },
  "decision": "deny",
  "reason_code": "irreversible_action",
  "criticality": "critical",
  "matched_rule": "forbid-destructive-production",
  "policy_version": "0.1.0",
  "policy_hash": "sha256:...",
  "session_id": "sess_...",
  "timestamp": "2026-10-26T18:03:00Z"
}
```

**Join key.** `event_id` and `decision_id` are the same stable id on the emitted event and on the audit entry
(M6) — a decision, its event, and its audit record join one hop away. `event.decision_id == decision.decision_id`
is the invariant the M5 test asserts. Emission is **pure** (no I/O): the caller decides the sink; agentpolicy
does not store the lake (ADR-0007). `agentwatch.to_event(...)` returns the dict; `agentwatch.decision_event(...)`
returns a `DecisionEvent` with `.to_dict()`.

**Determinism / no leakage.** The emitter is a pure renderer: no clock or network is consulted, and the payload
carries only the machine-readable decision + provenance — never policy internals beyond the matched rule id
(the agent-facing `permitted_alternatives` are curated in R37/M17).

## 6. Fail-closed

* A decision whose `reason_code` is not in the registry is a programmer error: `reason_codes.require(code)`
  raises `KeyError` (surfaced loudly, never silently).
* `explain.build_artifact` requires a canonical `NormalizedCall` and a finished `Decision`; unknown outcomes are
  rejected by the Cedar model itself.
* The emitter validates its required fields and raises `ValueError` on a blank id — a decision without a join
  key is a bug, not a silent `null`.

## 7. WBS M5 item mapping

| Item | Where |
|---|---|
| 5.D0 design docs first | this document |
| 5.1 explain artifact | `agentpolicy/explain.py`, `cedar/models.py` (`Explanation.clause`) |
| 5.2 reason-code registry | `agentpolicy/reason_codes.py`; wired in `cedar/shaper.py` |
| 5.3 actionability | `agentpolicy/explain.py` (`suggested_change`/`flip_variant`) + `tests/test_m5_explain.py` |
| 5.4 `agentpolicy explain` | `agentpolicy/cli/explain.py` |
| 5.5 event emitter | `agentpolicy/agentwatch.py` |
| 5.T/5.C/5.L/5.CR/5.D | tests · coverage · ruff/mypy · [codereview-log](../wbs/v0.1.0/codereview-log.md) · [reason-codes reference](../reference/reason-codes.md) |
