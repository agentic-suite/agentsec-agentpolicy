# ADR-0002 — agentpolicy is a PDP; it never enforces

**Status:** accepted · **Date:** 2026-10-26 · **Maps to:** DD-01 · **PRD:** [02](../prd/02-architecture.md), [14](../prd/14-non-goals.md)

## Context

Every enforcer in the ecosystem (agentgate, agentseatbelt/agentkernel, agentkeys, agenthalt, harness hooks)
needs an answer to *"is this allowed?"* Without a shared decision service, each re-implements policy — the exact
fragmentation the ecosystem exists to end. The temptation is to make the decision service also block calls
"since it's right there" — it sees the action, why not stop it?

## Decision

**agentpolicy decides; callers enforce.** It exposes evaluate/explain surfaces (library, CLI, MCP server,
HTTP/AuthZEN) and emits decision events. It executes nothing, blocks nothing, kills nothing. Enforcement lives
exclusively in the enforcers.

## Consequences

- agentpolicy can be wrong without being dangerous: a bad decision is advisory data until an enforcer acts.
- Testing is clean: drill the decision without standing up enforcement (agentdrill drives the *deployed* stack,
  and agentpolicy's rule packs are its test subjects).
- The decision contract is the only stable public surface — enforcers can be replaced/swapped (AuthZEN conformant
  PEPs) without touching policy.
- Separation of duties holds: what holds secrets (agentkeys), what decides (agentpolicy), and what observes
  (agentwatch) are different components — an attacker must defeat all three.
- The hard rule for contributors: any PR that adds enforcement "to make the decision stick" is out of scope by
  definition (RK-8).
