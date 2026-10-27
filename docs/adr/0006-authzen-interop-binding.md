# ADR-0006 — AuthZEN Authorization API 1.0 as the interop binding

**Status:** accepted · **Date:** 2026-10-26 · **Maps to:** DD-10 · **PRD:** [20](../prd/20-standards-and-claims.md), [12](../prd/12-traceability.md) R27

## Context

The PDP needs a wire contract for non-Python callers, gateways, and interop with other PDPs/PEPs. Options: a
bespoke HTTP API (fragmenting, unowned), OPA's REST API (OPA-shaped), or the **OpenID AuthZEN Authorization API
1.0**, which reached **Final on 11 Jan 2026** — a standard `subject/action/resource/context → decision` shape
with decision `context` (reasons, step-up `acr_values`), boxcarring, and search endpoints. The ecosystem research
flagged AuthZEN as the emerging PDP/PDP interop standard (CPEX already orchestrates it).

## Decision

**The HTTP surface is AuthZEN-conformant** (`POST /access/v1/evaluation`, evaluations boxcarring, decision
`context` carrying our reason codes + policy version, step-up via `acr_values`). We do not invent a parallel
protocol. PAP remains git; PEPs are the enforcers; the library/CLI/MCP surfaces are thin bindings over the same
engine.

## Consequences

- Any conformant PEP can point at agentpolicy — including non-Python hosts, service meshes, and enterprise
  gateways — with zero bespoke client code.
- **The swap test holds:** agentpolicy can be replaced by another conformant PDP without breaking the
  ecosystem — which is exactly why conformance is trustworthy rather than a lock-in story.
- AuthZEN's boolean decision is enriched (not extended) by our `context` — conformant first, informative second.
- Search endpoints are a smaller commitment (◐) — implemented where they serve tool-hiding/discovery (R21).
- We inherit the spec's security considerations (transport integrity, sender auth) rather than inventing ours.
