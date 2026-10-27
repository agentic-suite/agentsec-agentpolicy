# ADR-0004 — No ML in any decision path

**Status:** accepted · **Date:** 2026-10-26 · **Maps to:** DD-04, DD-07 · **PRD:** [13](../prd/13-non-functional-requirements.md), [22](../prd/22-policy-intelligence-and-governance.md) R42

## Context

The evidence is unambiguous: injection detection is empirically weak (AgentDojo ~46% ASR against best-known
defenses; InjecAgent doubles it with one prompt), and the credible defenses are **architectural** (policy,
separation, least privilege — the design-patterns paper, CaMeL's deterministic interpreter). A policy engine
that uses a classifier anywhere in its decision path inherits that weakness *and* loses determinism — the one
property that makes decisions reproducible, testable, and defensible in review.

## Decision

**No ML/classifier/LLM in any decision path.** Decisions are Cedar evaluation over a canonical action —
deterministic, offline, replayable. The optional **LLM advisor is non-authoritative and can only narrow scope or
escalate, never widen** (and is off by default). The NL drafting feature (R42, `agentpolicy draft`) is
**authoring-time only**: it generates a candidate rule that must compile, pass generated tests + lint, and get
human review — it is structurally incapable of touching the runtime path.

## Consequences

- Same input + policy ⇒ same decision, always — reproducibility is the product (offline evidence artifacts, CUJ-20).
- No API cost, no network, no drift in the hot path (sub-100 ms p99 is achievable, R8).
- We forgo "smart" risk scoring the predecessor did with weighted risk dimensions — replaced by explicit Cedar
  conditions; more verbose, but analyzable and defensible.
- The sales story is honest: we never claim to detect anything (the claims vocabulary forbids it).
- Deterministic secret/PII detection for redaction uses regex/entropy rules — declared, reviewable, versioned.
