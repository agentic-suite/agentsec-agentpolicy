# agentpolicy — Product Requirements (v0.1.0)

Requirements for **agentpolicy** — the local-first, Cedar-based **policy decision point (PDP)** for AI-agent
actions: **allow / deny / ask / rate-limit / redact**. Part of the
[agentic-suite](https://github.com/agentic-suite).

> **Status: v0.1.0 proposed (draft, 2026-10-26).** This PRD set defines the **entire v0.1.0 (Wave 0)** release:
> a deterministic decision service that answers *"may this agent do this, with these arguments, in this
> context, now?"* for every agent action, with shipped rule packs, an `explain-decision` contract, and
> decisions emitted in the agentwatch security-event schema. It **absorbs the decision model of the shipped
> predecessor policy engine** (#107, now private) and the **enforcement intent of `BehaviorGuard`** (#192) —
> see [PRD 10](10-feature-parity.md). The folder mirrors the `agentdrill` PRD structure.

## Documents

| # | Document | Covers |
|---|---|---|
| 00 | [Press Release / FAQ](00-press-release.md) | Working-backwards PR/FAQ |
| 01 | [Why](01-why.md) | Problem, evidence, supersession of the predecessor policy engine, non-goals |
| 02 | [Architecture](02-architecture.md) | Where it sits, components, the decision pipeline, the PDP contract, standards |
| 03 | [Landscape](03-landscape.md) | Commercial + OSS policy tooling, whitespace, migration from the predecessor |
| 04 | [Users and CUJs](04-users-and-cujs.md) | Personas + critical user journeys (decide, gate, explain, budget, ask, lint) |
| 05 | [What (Features)](05-features.md) | v0.1.0 P0 (R1–R8), P1, P2, feature catalog, non-requirements, compatibility |
| 06 | [Security Baseline](06-security-baseline.md) | Assets, controls, agentpolicy's own attack surface, disclosure |
| 07 | [Success Metrics](07-success-metrics.md) | Outcome metrics, release gate, anti-metrics |
| 08 | [Risks](08-risks.md) | Risk register, hard parts, triggers, open questions |
| 09 | [Roadmap](09-roadmap.md) | Versions, compatibility by version, migration/deprecation |
| 10 | [Feature Parity](10-feature-parity.md) | Every absorbed predecessor capability → delivered / delegated / waived |
| 11 | [Decisions](11-decisions.md) | Accepted decisions (design, scope, technical, governance) |
| 12 | [Traceability](12-traceability.md) | Requirements → CUJ → WBS → test → parity |
| 13 | [Non-Functional Requirements](13-non-functional-requirements.md) | Determinism, latency, fail-closed semantics, portability, security, cost |
| 14 | [Non-Goals](14-non-goals.md) | Consolidated non-goals |
| 15 | [Data Model & Lifecycle](15-data-model.md) | Entities, decision/ask/budget lifecycle, invariants |
| 16 | [Rule Packs](16-rule-packs.md) | The shipped packs (Replit rule, secret-in-output, MCP allowlist, exfil-sink, scope-escalation) + roadmap |
| 17 | [Explain-Decision & Evidence](17-explain-decision-and-evidence.md) | The explain contract, reason codes, and the agentwatch event binding |
| 18 | [Blast-Radius Budgets](18-blast-radius-budgets.md) | Cumulative per-session capability budgets (the novel class) |
| 19 | [Harness Compatibility](19-harness-compatibility.md) | PDP-by-construction + the harness/enforcer compatibility table |
| 20 | [Standards, Claims & Interop](20-standards-and-claims.md) | Cedar, OPA/Rego, AuthZEN, OTel/event schema, OWASP/ATLAS coverage |
| 21 | [Evidence Register & Method](21-evidence-register-and-method.md) | Preserved research: evidence, gap analysis, PRD tensions, method |
| 22 | [Policy Intelligence & Governance](22-policy-intelligence-and-governance.md) | The compelling additions (v0.2.0/v0.3.0): freeze windows, data-class derivation, agent enrollment + probation, approval analytics (rubber-stamp detection), break-glass, dual-control, multi-agent governance depth, nearest-permissible-action, NL drafting, secrets-in-args |
| 23 | [Enterprise Adoption & Governance Hardening](23-enterprise-adoption-and-governance-hardening.md) | The rollout/trust layer (v0.2.0): policy backtest + PR decision-diff, narrow-only layering, action-space coverage report, self-attack pack, allow-justification — **closes the PRD set** |

## Reviewers start here

1. **Scope:** does [PRD 05](05-features.md) define the right v0.1.0 (five outcomes, 3 rule packs, explain, event schema, sub-100ms)?
2. **Journeys:** is [PRD 04](04-users-and-cujs.md) CUJ-1..CUJ-20 the right set?
3. **Composition:** is agentpolicy the **brain** (decide-only, never enforce) in [PRD 02](02-architecture.md) correctly drawn — every enforcer calls it, it calls nothing?
4. **Determinism:** is "no ML in any decision path" enforced end-to-end ([PRD 13](13-non-functional-requirements.md), [PRD 11](11-decisions.md) DD-04)?
5. **Parity:** every absorbed predecessor capability is delivered / delegated / waived in [PRD 10](10-feature-parity.md).
6. **Gaps:** are the industry-gap features (blast-radius budgets, exfil-sink, AuthZEN interop, policy lint, harness-portable Cedar) the right ones, and are the still-open decisions in [PRD 21](21-evidence-register-and-method.md) §PRD tensions answered?

## Sources

- Ecosystem PRD 02 (agentpolicy, #211) — requirements R1–R14, harness-compatibility mandate, non-goals, standards.
- Predecessor **`agent-tooltrust`** (shipped, now private): its decision model — 4-state outcomes, contextual
  risk dimensions, action taxonomy, posture presets, explainability, audit log, escalation round-trip —
  absorbed into this PRD set (see [PRD 10](10-feature-parity.md)).
- `BehaviorGuard` (#192, unbuilt) — its enforcement intent, absorbed into the ask/deny/budget surface.
- The agent-security research base (agentic-suite): coverage map, OSS/commercial matrices, incident register,
  standards & interception-points notes — cited inline.
