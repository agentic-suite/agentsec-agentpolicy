# PRD 17 — Explain-Decision & Evidence

**BLUF:** A decision without an explanation gets bypassed. **Every** decision carries a machine-readable
`reason_code`, a human-readable `explanation`, a `criticality`, and a `factors[]` breakdown; every `deny` names
the **matched rule** and the one change that would flip it. Each decision is emitted in the **agentwatch
security-event schema** and bound to a hash-chained audit entry, so a third party can **re-derive it offline**.

**Status:** Draft — v0.1.0 (2026-10-26) · **Owner:** @deghosal-2026 · **Parent:** agentic-suite #209 · PRD #211

## The explain-decision contract

```json
{
  "decision": "deny",
  "reason_code": "irreversible_action",
  "criticality": "critical",
  "explanation": "Delete on production customer-PII data is blocked by the destructive-command rule.",
  "factors": [
    { "dimension": "action_class", "value": "delete",     "contribution": 10 },
    { "dimension": "environment",  "value": "production", "contribution": 8 },
    { "dimension": "data_class",   "value": "customer_pii","contribution": 10 },
    { "dimension": "agent_class",  "value": "release-bot", "contribution": 1 }
  ],
  "matched_rule": "destructive-command-gate",
  "suggested_change": "Use a read-only alternative, or move the action to a non-production environment.",
  "policy_version": "0.1.0",
  "policy_hash": "sha256:...",
  "event_id": "evt_01J..."
}
```

### Requirements

| Element | Requirement |
|---|---|
| `decision` | one of the five outcomes |
| `reason_code` | machine-readable, stable, SIEM-alertable |
| `criticality` | `none` / `low` / `med` / `high` / `critical` |
| `explanation` | template-generated, one human sentence |
| `factors[]` | `{dimension, value, contribution}` per contributing dimension |
| `matched_rule` | the Cedar rule id that decided the outcome. **From v0.2.0 this is required on every outcome, allows included** (allow-justification, R47 — "who authorized this?" is answerable for allows, not just denies). Until then it is required on `deny`/`ask`/`rate-limit`. |
| `retry_after` | on `rate-limit` decisions: the seconds after which the caller may retry (HTTP-standard semantics the agent can honor, R23) |
| `suggested_change` | the one change that would flip the outcome |
| `permitted_alternatives[]` | **verified-permissible variants** the agent can replan to immediately (evaluated-true against the policy — the PDP never suggests something it would deny); agent-facing text is a curated template with no policy internals, distinct from the full operator explanation (R37, [PRD 22](22-policy-intelligence-and-governance.md)) |
| `policy_version` + `policy_hash` | provenance of the decision |

### Actionability test (CI)

> A human given **only** the explanation text and the original action can name the one change (approve, move to
> staging, lower data class, reduce scope) that would change the outcome — **without** consulting documentation.

This is an automated acceptance test (R5), not a vibe. A `deny` with no matched rule is a bug.

## Reason codes (failure taxonomy)

| `reason_code` | Meaning |
|---|---|
| `policy_match` | an explicit rule decided the outcome |
| `default_deny` | no permit matched (default-deny posture) |
| `unknown_action` | the action could not be canonicalized |
| `irreversible_action` | the mandatory human-gate / destructive class |
| `human_gate_required` | `ask` — pending human decision |
| `human_gate_timeout` | an ask expired / timed out → deny |
| `budget_exhausted` | a session capability ceiling was hit (`rate-limit`) |
| `rate_limited` | burst/op-count limit hit |
| `secret_detected` | output scrubbed (`redact`) |
| `engine_unavailable` | the PDP could not evaluate |
| `policy_unavailable` | policy missing/malformed |
| `opa_backend_unavailable` | the Rego backend was unreachable |
| `evaluation_timeout` | evaluation exceeded its budget |
| `audit_sink_error` | audit write failed (decision still stands) |

## Evidence & offline verification

- **Event binding:** every decision is emitted in the **agentwatch security-event schema** with a shared
  `event_id` + `decision_id`, so a decision joins the ecosystem's telemetry (R6).
- **Audit binding:** every decision appends a **hash-chained** `AuditEntry` (`seq`, `prev_hash`, `entry_hash`,
  `policy_version`).
- **EvidenceArtifact:** a self-contained record — `action` + `matched_rule` + `policy_version` + `policy_hash` +
  `event_ref` — that a third party can verify **offline, on another machine, without installing agentpolicy**
  (CUJ-20): re-evaluate the action against the pinned policy and confirm the same outcome, and confirm the audit
  chain is unbroken.
- **Redaction receipts:** when a decision is `redact`, the receipt records class/count/location of what was
  scrubbed; the raw secret is never persisted.

## Why this is the moat

- **Deterministic** — a decision is reproducible, not a score.
- **Portable** — the explain artifact travels with the policy version.
- **Auditable** — the chain proves the log is unedited.
- **Actionable** — the whole point: a reviewer can fix the policy, not just stare at a deny.

## Relationship to the ecosystem

- **agentwatch** stores the decision events + the audit trail.
- **agentcomply** maps decisions to controls (OWASP ASI/LLM, ATLAS, NIST, EU AI Act) — [PRD 20](20-standards-and-claims.md).
- **agentdrill** verifies that a rule pack still blocks its incident replay.
- **agentdiff** turns the shadow decisions into a "would-have-blocked" conversion report.
