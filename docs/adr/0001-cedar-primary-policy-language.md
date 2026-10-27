# ADR-0001 — Cedar is the primary policy language

**Status:** accepted · **Date:** 2026-10-26 · **Maps to:** DD-02 · **PRD:** [05](../prd/05-features.md) R2, [20](../prd/20-standards-and-claims.md)

## Context

The policy layer must choose exactly one primary authoring language. Candidates: Cedar, OPA/Rego, YAML
allow-lists (the prempti/harness-native pattern), or a bespoke DSL. The ecosystem research shows: (a) Cedar is
the emerging default for agent sandboxes (Leash, brood-box, cmcp, CPEX all chose it) and is a CNCF Sandbox
project, formally verified with Lean; (b) OPA/Rego is the de-facto PDP standard but has a learning curve and no
agent-native constructs; (c) YAML allow-lists are pattern-matching only — they cannot express "ask a human for
a prod write," rate limits, or taint rules; (d) a bespoke DSL fragments the ecosystem and kills analyzability.

## Decision

**Cedar is the primary policy language.** OPA/Rego is a **peer import backend** for orgs already invested
(never the default authoring path). YAML is not a policy language here — it appears only in pack metadata and
test fixtures. No bespoke DSL, ever.

## Consequences

- Policies are typed, analyzable (lint can prove unused/shadowed/over-permissive rules, R12) and unit-testable
  (golden fixtures, R22).
- One policy is portable across every harness via policyweave compile-out — the "policy portability" gap nobody
  covers.
- We inherit Cedar's formal-verification story and CNCF governance.
- Rego parity must be maintained as a *peer backend* with identical decision semantics (extra surface, worth it).
- A Rego→Cedar migration assistant becomes a roadmap item (R13) rather than a blocker.
