# PRD 22 — Policy Intelligence & Governance (the compelling additions)

**BLUF:** Ten additions that close the PRD's in-lane gaps and make agentpolicy the product the industry is
missing: **change-freeze windows** (the exact condition the Replit incident happened under), **data-class
derivation** (who computes the inputs), **agent enrollment + probation** (the policy side of shadow-agent
discovery), **approval analytics** (rubber-stamp detection), **break-glass**, **dual-control approvals**,
**multi-agent governance depth**, **nearest-permissible-action** (denials that replan), **NL policy drafting**
(authoring-time, never decision-path), and **secrets-in-arguments**. Researched against the incident register,
the coverage map, and OWASP ASI 2026.

**Status:** Draft — v0.2.0/v0.3.0 scope (2026-10-26) · **Owner:** @deghosal-2026 · **Parent:** agentic-suite #209 · PRD #211

> The **v0.1.0 release gate is unchanged** — these are P1 (v0.2.0) and P2 (v0.3.0) commitments. All ten stay
> inside the hard boundaries: **decide-only, deterministic, no ML in any decision path, fail-closed.**

## Why these ten (the gap audit)

| Addition | The gap it closes | Evidence |
|---|---|---|
| Freeze windows | The Replit agent destroyed the DB **during an explicit code freeze** — our namesake rule can't express the freeze | Incident register #6 |
| Data-class derivation | `data_class` is a decision dimension, but nothing derives it; hand-tagging stalls adoption | PRD 05 R15 |
| Enrollment + probation | An unknown `agent_id` gets a bare default-deny — no first-seen posture; the policy side of shadow-agent discovery (coverage row #1) | Coverage map row #1; ASI03/ASI10 |
| Approval analytics | Human gates approved 100% of the time are theater; nobody measures approval quality | ASI09; the permission-fatigue evidence (PRD 01) |
| Break-glass | No time-boxed, auto-reverting elevation for agents — a standard enterprise pattern | Entra/enterprise IdP practice |
| Dual-control | Quorum approvals for the truly irreversible class (payments, regulated-data destruction) — absent for agents | High-security pattern; ASI09 |
| Multi-agent depth | ASI07/ASI08 (inter-agent comms, cascading failures) are commercial-led and weak; the PDP is the natural home | Coverage row #19; OWASP ASI |
| Nearest-permissible-action | Black-box denials get bypassed; denials that offer an alternative get adopted | PRD 01 problem #5 |
| NL drafting | Cedar's learning curve is the adoption bar; AWS AgentCore generates Cedar — but without proof | E2 metric (< 1 afternoon) |
| Secrets-in-args | We redact *outputs*; agents also *paste secrets into arguments* | CSA credential-theft research note |

## The requirements

| # | Requirement | Pri | Acceptance criterion |
|---|---|---|---|
| **R33** | **Change-freeze / maintenance-mode windows** — a policy condition on time/freeze context that tightens posture (e.g., every write in prod → `ask` during a freeze) | P1 | A declared freeze flips the posture for its window, decisions record `freeze_id`, and the freeze is audited on/off |
| **R34** | **Declarative data-class derivation** — path globs, resource tags, and schema hints derive `data_class` deterministically (no ML) | P1 | An untagged resource resolves to a class from the derivation table; a conflict fails loudly, never silently |
| **R35** | **Agent enrollment + probation** — a first-seen unknown `agent_id` lands in a probation posture (read-only + audit + `ask` on writes) until a human classifies it | P1 | An unknown agent's first write returns `ask` with `reason_code=agent_probation`; classification is a logged event |
| **R36** | **Approval analytics** — a tuning report over decision/ask history: top deny reasons, shadow→enforce delta, approval latency, and **rubber-stamp gates** (100%-approved asks) | P1 | The report flags a synthetic always-approved gate in a test corpus |
| **R37** | **Nearest-permissible-action** — `deny`/`ask` decisions carry `permitted_alternatives[]` (what *would* be allowed), agent-facing, distinct from the operator explanation | P1 | A denied call returns a verified-permissible alternative; the agent-facing text never leaks policy internals |
| **R38** | **Secrets-in-arguments** — detect secrets/PII in tool-call *arguments*; redact or deny before the call leaves | P1 | A key pasted into an arg is scrubbed/blocked with a receipt; the raw value is never persisted |
| **R39** | **Multi-agent governance depth** — delegation-chain evaluation, scope-subset proofs (child ⊆ parent), inter-agent action decisions (extends R25) | P2 | A child's out-of-parent-scope action is denied naming the chain link; an inter-agent request is decided like any action |
| **R40** | **Break-glass elevation with auto-revert** — a time-boxed posture elevation, fully audited, reverting automatically at expiry | P2 | Elevation expires without manual action; every decision in the window carries `break_glass_id`; revert is a logged event |
| **R41** | **Dual-control approvals** — a quorum (default 2) of distinct approvers for the irreversible class | P2 | A single approval does not release a dual-control ask; two distinct approvers do; the quorum is audited |
| **R42** | **NL policy drafting** (`agentpolicy draft`) — generate a candidate Cedar rule from a sentence; **advisory only** — must pass `pack test` + lint + human review, never auto-applied | P2 | A one-sentence intent yields a candidate rule that compiles, passes its generated tests, and waits for review; no ML in the decision path |

## Feature catalog additions

| # | Feature | Req | Notes |
|---|---|---|---|
| F30 | Freeze-window condition + `freeze` context flag + freeze-aware posture switching | R33 | Cedar time/context conditions; a freeze is a versioned, audited artifact |
| F31 | Declarative data-class derivation table (globs/tags/schema) with conflict resolution | R34 | Deterministic; shipped defaults for common paths (`.env` → secret-class) |
| F32 | Enrollment ledger + probation posture + classification flow | R35 | The first-seen gate; ties into agentwatch inventory |
| F33 | Approval-analytics report (`agentpolicy report approvals`) | R36 | Computed over the ask/approval records; ships to agentwatch events |
| F34 | Break-glass elevation + auto-revert timer + audit | R40 | Elevation requires a logged reason; reversion is automatic |
| F35 | Quorum approvals on the irreversible class | R41 | Distinct-approver enforcement; expiry still applies |
| F36 | Delegation-chain evaluation + scope-subset proof + inter-agent decisions | R39 | The PDP decides agent→agent requests like agent→tool |
| F37 | `permitted_alternatives[]` in the decision + agent-facing replan text | R37 | Generated from the policy (a verified-permissible variant), not a guess |
| F38 | `agentpolicy draft` — NL → candidate Cedar + generated tests | R42 | Authoring-time only; blocked from any runtime path by design |
| F39 | Argument-side secret/PII detection + redaction receipts (args) | R38 | Sibling of the output-side redaction |

## Semantics that matter

- **Freeze ≠ posture preset.** A freeze is a *context condition* any policy can reference (`context.freeze_id != null` → tighten). Multiple freezes can overlap; the strictest applies. Freezes are declared, versioned, and audited on/off — the Replit lesson is that "I told the agent not to" is not a control; a declared freeze the *policy* enforces is.
- **Probation is a posture, not a deny.** The goal is adoption safety, not lockout: read + audit + `ask` on writes until a human classifies the agent (and the classification event feeds agentwatch's inventory).
- **Rubber-stamp detection is the honesty layer for HITL.** A gate approved 100% of the time is auto-flagged; the report recommends demoting it to `allow`+audit (fewer, better gates) or tightening the ask — the decision stays human.
- **`permitted_alternatives[]` must be true.** Candidates are evaluated against the policy before being returned — the PDP never suggests an alternative it would deny. The agent-facing message is a curated template (no policy internals); the operator explanation stays full-fidelity.
- **NL drafting is locked out of runtime.** `draft` output is a *review artifact*: it must compile, pass generated tests + lint, and get human review before it can be pinned. The deterministic evaluator never calls a model. (The predecessor's rule holds: ML can narrow, never widen — and here it never even decides.)
- **Break-glass and dual-control compose.** A break-glass window does not bypass dual-control; irreversible actions still need the quorum. Elevation widens *scope ceilings*, not the human-gate class.
- **Multi-agent decisions are just decisions.** An inter-agent request is a normal evaluation where `principal` is the calling agent and `resource` is the callee/capability — plus the delegation-chain check. No new engine path (same determinism).

## Coverage deltas (see [PRD 20](20-standards-and-claims.md))

| Addition | ASI/LLM/ATLAS effect |
|---|---|
| Freeze windows | ASI02/ASI10 posture control; EU AI Act Art. 14 (intensified oversight) |
| Enrollment + probation | ASI03 (identity & privilege abuse), ASI10 (rogue agents) — strengthens row #1's OSS side |
| Approval analytics | ASI09 (trust exploitation) — the direct control on rubber-stamping |
| Multi-agent depth | ASI07 (inter-agent comms), ASI08 (cascading failures) — from ◐ toward covered |
| Secrets-in-args | LLM02/LLM05, ATLAS AML.T0057 — closes the input side |
| Dual-control / break-glass | ASI09 / enterprise oversight patterns |

## Traceability

| Req | CUJ | Test |
|---|---|---|
| R33 | CUJ-21 | `tests/test_m13_freeze.py` — a declared freeze flips the posture for the window and is audited |
| R34 | CUJ-21 (setup), CUJ-1 | `tests/test_m13_dataclass.py` — untagged resource resolves; conflict fails loudly |
| R35 | CUJ-22 | `tests/test_m13_enrollment.py` — first-seen write → `ask` + `agent_probation` |
| R36 | CUJ-23 | `tests/test_m13_approvals.py` — always-approved gate flagged in a corpus |
| R37 | CUJ-24 | `tests/test_m13_alternatives.py` — alternative is verified permissible; no internals leak |
| R38 | CUJ-15 (extended) | `tests/test_m13_args_secrets.py` — arg secret scrubbed with receipt |
| R39 | CUJ-28 | `tests/test_m14_delegation.py` — child out-of-scope denied, chain link named |
| R40 | CUJ-25 | `tests/test_m14_breakglass.py` — expiry reverts without manual action |
| R41 | CUJ-26 | `tests/test_m14_dualcontrol.py` — one approval ≠ release; two distinct approvers = release |
| R42 | CUJ-27 | `tests/test_m14_draft.py` — draft compiles, tests pass, waits for review; runtime path untouched |

## New risks (see [PRD 08](08-risks.md))

| # | Risk | Mitigation |
|---|---|---|
| **RK-17** | Break-glass becomes the default path (permanent elevation by habit) | Requires a logged reason; short default TTL; the analytics report flags heavy break-glass users |
| **RK-18** | An NL draft is plausible but wrong (passes tests, over-permissive in the field) | Drafts are advisory + human-reviewed + linted + agentdrill-replayed; never auto-pinned |
| **RK-19** | `permitted_alternatives[]` leaks policy shape to a hostile agent | Curated templates only; alternatives are evaluated-true; an operator-facing/operator-only split is tested |
| **RK-20** | Enrollment ledger becomes a shadow IdP | agentpolicy classifies; it does not issue identity (IdP/SPIFFE stays the issuer) |
