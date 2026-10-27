# ADR-0008 — Absorb the predecessor's decision model, replace the engine

**Status:** accepted · **Date:** 2026-10-26 · **Maps to:** PRD [10](../prd/10-feature-parity.md) · **Org:** agent-tooltrust → agentpolicy supersession (org README)

## Context

The shipped predecessor policy engine (`agent-tooltrust`, v0.2.0, archived; now private) proved the decision
model — contextual dimensions, a 13-domain taxonomy, posture presets, explainability, audit, escalation
round-trip, OWASP 10/10 — with field-tested results (Plan A 83/83, Plan B 116/123, engine matrix 2490/2490).
Its engine, however, was a bespoke Python weighted-risk scorer: not analyzable, not portable across harnesses,
and its own scoring language. Cedar now exists as the standard answer, and the ecosystem needs one decision
service, not two products.

## Decision

**Absorb the capability set; replace the engine.** Every predecessor capability is delivered, delegated (to a
named ecosystem tool), or waived with reason — the full disposition is [PRD 10](../prd/10-feature-parity.md)
(P1–P35). The 4-state model becomes the 5-outcome set (ADR-0003); `audit` folds into always-on event emission
(ADR-0007); the scorer becomes Cedar evaluation (ADR-0001). The predecessor repo is archived and private — the
agentpolicy docs are **self-contained** and restate every absorbed capability inline.

## Consequences

- Nothing proven is lost: the taxonomy, postures, explain contract, ask round-trip, audit trail, and
  adversarial normalization all carry over — with requirement-level traceability.
- The parity table (P1–P35) is the contract that no capability is silently dropped; delegated rows name the
  owning tool (no competing registries).
- Known predecessor gaps ship **fixed**, not inherited: dispatcher-bypass and tool-name normalization are P0
  (were P1/P2), tamper-evident audit is P0 (was P2), policy-hash-in-decision is P0.
- The predecessor's deliberate deferrals stay deliberate: fleet sync (R31), marketplace (R14) — waived at
  v0.1.0 with the documented git-based path.
- Honesty rule: agentpolicy does not claim the predecessor's field-test numbers. It earns its own.
