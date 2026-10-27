# ADR-0005 — Fail-closed semantics everywhere

**Status:** accepted · **Date:** 2026-10-26 · **Maps to:** DD-06 · **PRD:** [13](../prd/13-non-functional-requirements.md), [04](../prd/04-users-and-cujs.md) CUJ-9

## Context

A policy engine has exactly one unforgivable failure: silently allowing. The predecessor shipped a fail-closed
contract across every degradation (engine crash, malformed policy, backend unreachable, timeout, audit-sink
failure) and it was the single most-cited property in reviews. The ecosystem's own threat model says the same:
fail-closed on integrity failure; assume the enforcer is compromised.

## Decision

**Every failure path returns `deny` with a distinct `reason_code`:** `engine_unavailable`,
`policy_unavailable`, `opa_backend_unavailable`, `evaluation_timeout`, `unknown_action`. The default may be
tightened to `ask`-on-failure for chosen action classes, but **never loosened to `allow`**. Audit-sink failure
never changes the decision (audit is a side effect, not a gating dependency).

## Consequences

- "No failure mode silently allows" is a CI test over a fuzzed input space — not a claim.
- A wrong-but-loud failure is debuggable in one hop (reason code → runbook); a silent allow is an incident.
- Operators can alert per failure class (SIEM-ready codes).
- The cost: availability. A broken policy takes the gated path down rather than letting agents run — the
  correct trade for a security control, stated plainly in the docs.
