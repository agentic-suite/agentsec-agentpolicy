# PRD 02 — Architecture

**BLUF:** agentpolicy is a **Cedar policy decision point (PDP)** — a deterministic function
`(principal, action, resource, context) → decision` — that sits behind every enforcer and returns one of five
outcomes with an explanation. It owns **no enforcement**: harness hooks, the MCP proxy (agentgate), the
confinement layer (agentseatbelt/agentkernel), the credential broker (agentkeys), and the halt path (agenthalt)
call it. It absorbs the decision model of the shipped predecessor policy engine and re-points it at
**Cedar** as the single source of authorization truth, with decisions emitted in the agentwatch schema.

**Status:** Draft — v0.1.0 (2026-10-26) · **Owner:** @deghosal-2026 · **Parent:** agentic-suite #209 · PRD #211

## Where agentpolicy sits

agentpolicy is the ecosystem's **brain** and is deliberately thin: it answers authorization questions and
records the answer. It never becomes an enforcement point.

```
        enforcers (PEPs)                              agentpolicy (PDP)
 ┌───────────────────────────────┐          ┌───────────────────────────────────────────┐
 │ harness hooks (Claude Code…)  │          │  normalize → evaluate (Cedar) → decide →   │
 │ agentgate (MCP proxy)         │  ask ───► │  explain → emit event → audit → budget      │
 │ agentseatbelt / agentkernel   │ ◄─── ─── │                                             │
 │ agentkeys (issuance)          │  decision │  policy (Cedar, git) · rule packs · schema  │
 │ agenthalt (budget trigger)    │          └──────────────┬──────────────────────────────┘
 └───────────────────────────────┘                         │ reads/writes
                                                           ▼
        agentwatch (records + security events) · agentinbox (ask-gate) · agentdrill (replay)
```

- **Callers (PEPs)** ask about a *proposed* action and enforce the answer. agentpolicy never executes anything.
- **Policy** is Cedar text, versioned in git; the same file governs every caller.
- **Evidence** is the agentwatch security-event schema, so decisions join the ecosystem's telemetry on a common
  id (R6).
- **Asks** route to agentinbox; **budget exhaustion** triggers agenthalt; **replays** are verified by agentdrill.

> **Analogy, absorbed from the predecessor:** its insight was that *flat allow-lists are a reachability
> control, not an authorization decision* — the same tool is harmless in staging and dangerous in production.
> agentpolicy keeps the contextual decision model but replaces the bespoke Python risk scorer with **Cedar**, so
> the decision is analyzable, portable, and reviewable like code.

## Components (v0.1.0)

1. **Policy loader + validator** — parses Cedar policies (+ OPA/Rego via adapter), validates schema, entity
   types, and pack structure; strict-fails on malformed policy (never operate with a broken policy).
2. **Action normalizer** — converts any incoming call (MCP `tools/call`, LangGraph tool node, raw Python,
   HTTP, dispatcher/coarse shell) into a **canonical action** `(principal, action, resource, context)`; closes
   the dispatcher-bypass and tool-name-obfuscation gaps (R24, R26).
3. **Cedar evaluator** — the deterministic decision core; no ML, no network in the hot path.
4. **Decision shaper** — maps the Cedar result + rule-pack metadata to one of five outcomes
   (`allow`/`deny`/`ask`/`rate-limit`/`redact`) with a `reason_code` and criticality.
5. **Explain engine** — produces the `explain-decision` artifact (matched clause, context, factors, suggested
   change) — see [PRD 17](17-explain-decision-and-evidence.md).
6. **Budget/session store** — cumulative per-session capability counters (files, requests, spend, calls) and
   consent scope; drives `rate-limit` and budget-exhaustion halts (R9, R23) — see [PRD 18](18-blast-radius-budgets.md).
7. **Ask-gate broker** — issues `ask` decisions with an `ask_id`, action-identity binding, expiry, and
   timeout=deny; integrates with agentinbox (R4, R18).
8. **Event emitter** — emits every decision in the **agentwatch security-event schema** (R6).
9. **Audit log** — append-only, tamper-evident decision log (JSONL/SQLite/Postgres sink) with policy version
   per entry (absorbed from the predecessor's decision log).
10. **Rule packs** — shipped, versioned packs (Replit rule, secret-in-output, MCP allowlist, exfil-sink,
    scope-escalation) with per-pack incident replay references (R3) — see [PRD 16](16-rule-packs.md).
11. **Policy lint** — unused / shadowed / over-permissive rule detection (R12).
12. **Delivery surfaces** — Python library, CLI, MCP server (`evaluate`/`explain` as MCP tools), HTTP PDP
    endpoint, and the **AuthZEN Authorization API 1.0** binding (R27, R28).
13. **Adapter registry** — enforcer/framework adapters (harness hooks, MCP client wrapper, LangGraph,
    PydanticAI, OpenAI Agents SDK, CrewAI) validated at load.
14. **Posture scaffolder** — `agentpolicy init --posture strict|balanced|permissive` generates a commented,
    pre-populated policy (never a blank slate) (R16).
15. **Shadow/calibration** — `dry_run` shadow mode + counterfactual threshold calibration report (R30).
16. **CI regression suite** — golden decision fixtures replayed on every policy PR (deterministic drift
    detection) (R22).

## The decision pipeline

| Stage | What happens | Absorbed from |
|---|---|---|
| **Normalize** | Coarse input → canonical action `(principal, action, resource, context)`; tool-name normalization (case/whitespace/Unicode). | predecessor: normalization + dispatcher safety |
| **Evaluate** | Cedar evaluates the policy set against the action + context; rule packs contribute typed rules. | Cedar (new) |
| **Decide** | Map to `allow`/`deny`/`ask`/`rate-limit`/`redact`; apply mandatory human-gate class; apply budgets. | predecessor 4-state + new 5th |
| **Explain** | Build the explanation artifact: matched clause, factors, criticality, suggested change. | predecessor explainability |
| **Emit** | Emit a decision event in the agentwatch schema (join key). | agentwatch schema |
| **Audit** | Append to the decision log with policy version + action identity. | predecessor audit log |
| **Enforce (elsewhere)** | The caller enforces: block, pause, throttle, or scrub. | — (agentpolicy owns none) |

## The PDP contract

agentpolicy exposes one logical operation with several bindings:

- **Input:** `principal` (agent id/class, principal), `action` (canonical verb + arguments), `resource`
  (tool/target/data class), `context` (environment, session id, prior decisions, budget state, time).
- **Output:** `{ decision, reason_code, criticality, explanation, factors[], policy_version, ask_id?,
  budget_state?, redactions? }`.
- **Bindings:** in-process Python `evaluate(...)`; CLI `agentpolicy evaluate/explain`; MCP tools
  `evaluate`/`explain`; HTTP `POST /access/v1/evaluation` (**AuthZEN Authorization API 1.0**).

## Standards

Cedar (primary policy language, CNCF Sandbox); OPA/Rego (import adapter); **AuthZEN Authorization API 1.0**
(PDP↔PEP interop, Final Jan 2026); OTel/agentwatch security-event schema (decisions as events); OWASP LLM
Top-10 + OWASP Agentic Top-10 (ASI) + MITRE ATLAS tagging on every rule pack. Full detail in
[PRD 20](20-standards-and-claims.md).

## Fail-closed by construction

Every failure path returns `deny` with a distinct `reason_code` — engine unavailable, malformed policy, OPA
backend unreachable, evaluation timeout, unknown tool, audit-sink failure (audit is a side effect, not a
gating dependency). No failure mode silently allows. See [PRD 13](13-non-functional-requirements.md) and the
CUJ-9 table in [PRD 04](04-users-and-cujs.md).

## Extensibility

- **Rule packs** and **policy modules** register via a documented schema; a community pack is one file + one
  test file + one PR (R29, CUJ-5).
- **Adapters** (enforcer/framework) register via decorator + entry points, validated at load
  (`unknown adapter → ConfigError`).
- **Policy modules** compose with Cedar's native `permit`/`forbid` semantics; no custom DSL.
