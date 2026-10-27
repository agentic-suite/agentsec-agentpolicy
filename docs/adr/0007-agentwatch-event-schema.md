# ADR-0007 — Decisions emitted in the agentwatch security-event schema

**Status:** accepted · **Date:** 2026-10-26 · **Maps to:** DD-05 · **PRD:** [17](../prd/17-explain-decision-and-evidence.md) R6

## Context

Decisions are only useful if the rest of the ecosystem can consume them: agentwatch stores and correlates,
agentdiff converts shadow decisions into "would-have-blocked" reports, agentcomply maps them to controls, SIEMs
alert on them. Two options: define an agentpolicy-specific event format, or emit into the ecosystem's existing
security-event schema (agentwatch v1, OTel-compatible) — the schema agentwatch, agentdrill evidence, and the
future tools already share.

## Decision

**Every decision is emitted as an `agentwatch.security_event.v1` event** (`event_type: policy.decision`) with a
shared `event_id`/`decision_id` join key, the full decision object (outcome, reason code, matched rule, policy
version/hash), and budget/ask state where present. No parallel event vocabulary.

## Consequences

- Decisions join telemetry one hop away: a deny, the tool call it denied, and the halt it triggered are one query.
- agentdiff/agentcomply/agentwatch consume decisions with zero adapter code.
- The event payload is the machine-readable form of the explain contract — one artifact, two audiences
  (operator: full fidelity; agent: curated alternatives per R37).
- We commit to the schema's versioning discipline: schema changes are versioned events, never silent edits.
- agentpolicy does not store the lake — emission only; storage/analytics stays agentwatch's job (no competing
  registry).
