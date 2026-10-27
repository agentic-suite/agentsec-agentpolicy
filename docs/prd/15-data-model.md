# PRD 15 — Data Model & Lifecycle

**BLUF:** The core entities are **Policy → RulePack → Rule → Action → Decision → Ask/Approval → AuditEntry**,
with **SessionState** (budgets/consent), **GoldenDecision** (CI regression), and an **EvidenceArtifact** for
offline verification. Policies are Cedar text under git; decisions are emitted in the **agentwatch schema**;
local state lives under `.agentpolicy/`.

**Status:** Draft — v0.1.0 (2026-10-26) · **Owner:** @deghosal-2026 · **Parent:** agentic-suite #209 · PRD #211

## Entities

| Entity | Definition | Key fields |
|---|---|---|
| **Policy** | A versioned set of Cedar rules (+ optional Rego backend) | `version`, `hash`, `modules[]`, `posture`, `packs[]` |
| **PolicyModule** | A reusable Cedar fragment (e.g., the action taxonomy, the ask class) | `name`, `version`, `cedar` |
| **RulePack** | A versioned, incident-anchored set of rules | `name`, `version`, `description`, `incident_ref`, `min_agentpolicy`, `license`, `hash`, `trust` |
| **Rule** | One Cedar `permit`/`forbid` with metadata | `id`, `effect`, `action_scope`, `conditions`, `reason_code`, `criticality`, `tags` |
| **Action** | The canonical thing being decided | `principal`, `verb`, `resource`, `args`, `environment`, `data_class`, `agent_class` |
| **Principal** | The agent/actor | `agent_id`, `agent_class`, `principal`, `delegation_chain[]` |
| **Resource** | The target | `tool`, `target`, `data_class`, `attributes{}` |
| **Context** | The environment of the decision | `environment`, `session_id`, `time`, `budget_state`, `prior_decisions[]` |
| **Decision** | The outcome | `decision` (`allow`/`deny`/`ask`/`rate-limit`/`redact`), `reason_code`, `criticality`, `policy_version`, `policy_hash`, `ask_id?`, `redactions[]?`, `budget_state?` |
| **Factor** | A contribution to the decision | `dimension`, `value`, `contribution` |
| **Explanation** | The `explain-decision` artifact | `matched_rule`, `context`, `factors[]`, `suggested_change` |
| **Ask** | A pending human gate | `ask_id`, `action_identity` (tool+args hash), `reason`, `expires_at`, `state` |
| **Approval** | A resolved ask | `ask_id`, `action_identity`, `approver`, `decision`, `expires_at` |
| **SessionState** | Cumulative context for a session | `session_id`, `counters{files,requests,spend,calls}`, `consent_scope[]`, `cumulative_risk` |
| **AuditEntry** | One append-only decision record | `seq`, `prev_hash`, `entry_hash`, `decision_ref`, `policy_version`, `timestamp` |
| **GoldenDecision** | Accepted expected outcome for a fixture | `fixture_id`, `expected_decision`, `policy_version` |
| **CoverageTag** | Standards mapping on a rule pack | `owasp_asi[]`, `owasp_llm[]`, `atlas[]`, `nist[]`, `eu_ai_act[]` |
| **EvidenceArtifact** | Offline-verifiable decision record | `action`, `matched_rule`, `policy_version`, `event_ref`, `hash` |

## Example — a Cedar rule pack (fragment)

```cedar
// rule pack: incidents-destructive-commands  (the "Replit rule")
// incident_ref: incident-register#6 (Replit prod-DB deletion)
@id("destructive-command-gate")
@reason_code("irreversible_action")
@criticality("critical")
forbid (
  principal,
  action,
  resource
)
when {
  resource.environment == "production" &&
  action.verb in ["delete", "drop", "force_push", "destroy"] &&
  resource.tool_category in ["db", "shell", "cloud", "git"]
};

// irreversible actions default to a human gate rather than a hard deny
@id("irreversible-ask-gate")
@reason_code("human_gate_required")
permit (
  principal,
  action,
  resource
)
when {
  action.verb in ["send", "deploy", "transfer", "grant"] &&
  resource.environment == "production"
}
advice { human_gate = "required" };
```

## Example — a decision (emitted in the agentwatch schema)

```json
{
  "schema": "agentwatch.security_event.v1",
  "event_type": "policy.decision",
  "event_id": "evt_01J...",
  "decision_id": "dec_01J...",
  "principal": { "agent_id": "release-bot", "agent_class": "ci-bot" },
  "action": { "verb": "delete", "tool": "drop_database", "args_hash": "sha256:..." },
  "resource": { "tool_category": "db", "environment": "production", "data_class": "customer_pii" },
  "decision": "deny",
  "reason_code": "irreversible_action",
  "criticality": "critical",
  "matched_rule": "destructive-command-gate",
  "policy_version": "0.1.0",
  "policy_hash": "sha256:...",
  "session_id": "sess_...",
  "timestamp": "2026-10-26T18:03:00Z"
}
```

## Lifecycle

1. **Author/import** a policy or rule pack → **validate** (`agentpolicy check --strict`, schema + Cedar parse).
2. **Review** (two-party) → **pin** the policy version + hash → load.
3. **Evaluate** an action (normalize → Cedar → decide → explain) → **Decision** (+ **Ask** if `ask`).
4. **Resolve** asks (approve/deny) → **Approval** (action-identity bound).
5. **Emit** a decision event (agentwatch schema) → **Audit** (hash-chained).
6. **Compare** vs **GoldenDecision** in CI → gate the PR.
7. **Report** the outcome (CLI/JSON/CSV) → **EvidenceArtifact** for offline verification.

## Storage layout (`.agentpolicy/`)

```
.agentpolicy/
  policy/            # resolved Cedar modules + rule packs (by name + version)
  decisions/
    <session>/<decision_id>.json   # Decision + Explanation + Evidence refs
  asks/              # pending + resolved asks (action-identity bound)
  sessions/          # SessionState (budgets, consent scope)
  goldens/           # GoldenDecision fixtures per policy version
  audit/             # append-only, hash-chained decision log
  calibration/       # shadow/counterfactual reports
```

## Invariants

- **Determinism:** same action + policy ⇒ same decision; no ML/randomness/network in the path.
- **Fail-closed:** any error ⇒ `deny` with a distinct `reason_code`.
- **No silent allow:** an unknown tool/action normalizes and denies; it never defaults to allow.
- **Explainability:** every `deny`/`ask`/`rate-limit` names a matched rule (or a budget/gate class); no
  "denied with no reason".
- **Action identity:** every ask approval binds `(tool, args_hash)`; a replay with different args fails.
- **Policy provenance:** every decision records `policy_version` + `policy_hash`.
- **Audit integrity:** the log is a hash chain; a broken link is detectable and fail-closed.
- **Path safety:** identifiers used in paths match `^[a-zA-Z0-9_-]+$`.
- **Single source of truth:** the policy that governs a decision is one reviewed artifact; no parallel rule set.
