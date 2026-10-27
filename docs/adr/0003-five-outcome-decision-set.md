# ADR-0003 — The five-outcome decision set

**Status:** accepted · **Date:** 2026-10-26 · **Maps to:** DD-03 · **PRD:** [05](../prd/05-features.md) R1

## Context

The predecessor proved a 4-state model (allow/audit/escalate/deny). Real incidents demand more nuance: Replit
needed a human gate on an irreversible action; runaway loops need throttling, not denial; secrets in tool output
need scrubbing, not blocking. Binary allow/deny forces over-blocking (false positives → bypass) or
under-blocking (incidents).

## Decision

**Five outcomes:** `allow` · `deny` · `ask` (human gate) · `rate-limit` (throttle/budget) · `redact`
(allow + scrub output/args).

The predecessor's `audit` is **folded away**: every decision is always emitted as an event (agentwatch schema)
and audited — auditing is a property of all five outcomes, not an outcome.

## Consequences

- `ask` is reserved for irreversible classes (R4); ask-fatigue is the known failure mode, so budgets and
  rate-limits absorb the volume cases (RK-9).
- `rate-limit` makes volume a policy concern — the capability-budget class nobody else ships (R9/R23).
- `redact` makes data-flow a decision — the exfil-sink/secret-in-output packs can allow-with-scrub instead of
  blocking legitimate work.
- Every outcome must be explainable and carry the same reason-code contract — five outcomes, one explain surface.
- Enforcers must implement all five semantics (a deny-only PEP degrades the contract — documented honestly in the
  compatibility table).
