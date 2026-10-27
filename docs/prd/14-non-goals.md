# PRD 14 — Non-Goals

**BLUF:** agentpolicy **decides; it does not enforce, detect, isolate, or issue identity.** It is the
deterministic policy decision point behind the ecosystem's enforcers. Anything that would make it a PEP, an
injection classifier, a sandbox, or an IdP is out of scope.

**Status:** Draft — v0.1.0 (2026-10-26) · **Owner:** @deghosal-2026 · **Parent:** agentic-suite #209 · PRD #211

## Consolidated non-goals

| Non-goal | Why | Who owns it instead |
|---|---|---|
| **Enforcement** (blocking, killing, sandboxing a call) | A decision service that enforces would test itself, not the user's stack | agentgate (MCP proxy), agentseatbelt/agentkernel (confinement), agenthalt (halt) |
| **Injection detection / classification** | Empirically unsolved and saturated; detection is the wrong layer | Nothing — agentpolicy is architectural and deterministic, not detection |
| **ML/classifier in any decision path** | Determinism is a product requirement, not a style choice | — |
| **Runtime isolation / sandboxing** | agentpolicy governs the decision, not the runtime | agentseatbelt, agentkernel, AgentSandbox |
| **Credential issuance / revocation** | Out of the decision layer | agentkeys |
| **Full IAM / IdP / identity issuance** | agentpolicy consumes identity; it does not issue it | IdP / SPIFFE / enterprise identity |
| **Tool-description scanning (poisoning/typosquat)** | Belongs at the MCP boundary | agentgate |
| **Telemetry storage / analytics** | agentpolicy emits events; it does not store the lake | agentwatch |
| **Compliance certification / evidence automation** | agentpolicy emits evidence; agentcomply maps it to controls | agentcomply |
| **Console/UI beyond CLI** (v1) | Policies are text; review lives in git | — |
| **Self-hosted PDP-service hardening** (v1) | Local-first first | — |
| **A model leaderboard / eval harness** | agentpolicy is policy, not eval | agentdrill |
| **Distributed policy sync** (v1) | git + shared load is the documented path; fleet sync is later | R31 (later) |
| **Cross-session behavioral correlation** | The audit exposes the data; correlation is a later layer | agentwatch analytics |

## What agentpolicy is *not* claiming

- It does **not** "solve prompt injection." It makes the *action* deterministic and reviewable — the model
  cannot argue past a rule it never sees.
- It does **not** guarantee zero-risk autonomy. It makes risk **explicit, bounded, and reviewable**.
- It does **not** replace the underlying authorization systems (OAuth, IAM, ReBAC). It is the decision layer
  that consumes them.
