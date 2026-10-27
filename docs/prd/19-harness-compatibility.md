# PRD 19 — Harness Compatibility

**BLUF:** agentpolicy is **harness-agnostic by construction** — it is a **PDP behind the enforcer**, so it works
for every harness that has *any* enforcement point at all. Compatibility is therefore about the **enforcers and
frameworks that call it**, not about per-harness builds. "Compatible" means the calling enforcer is exercised in
the field test; the release carries an honest compatibility table.

**Status:** Draft — v0.1.0 (2026-10-26) · **Owner:** @deghosal-2026 · **Parent:** agentic-suite #209 · PRD #211

## The compatibility model

| Layer | How agentpolicy reaches it | Effort to support |
|---|---|---|
| **Harness hooks** (Claude Code `PreToolUse`, Cursor, Codex CLI, Gemini CLI) | The harness hook calls agentpolicy before the tool runs | Harness-agnostic — any hook can call the PDP |
| **MCP proxy** (agentgate) | agentgate asks agentpolicy per `tools/call` | Protocol-layer, harness-agnostic |
| **Confinement** (agentseatbelt/agentkernel) | The confinement layer asks before allowing a syscall/file/net action | Below-process, harness-agnostic |
| **Credential issuance** (agentkeys) | Issuance asks whether the scope is allowed | Below-harness, harness-agnostic |
| **Frameworks** (LangGraph, PydanticAI, OpenAI SDK, CrewAI, …) | A library/adapter calls `evaluate()` in-process | Adapter per framework |
| **Generic MCP clients** | Via the MCP-server surface or agentgate | Protocol-layer |

Because agentpolicy is the **decision service**, it does not need a per-harness build — it needs **callers**. The
harness-compatibility mandate is satisfied by construction ([research matrix: 00-harness-compatibility.md]).

## Tier-1 — Coding agents

| Harness | How agentpolicy is reached | v0.1.0 | v0.3.0 |
|---|---|---|---|
| **Claude Code** | `PreToolUse` hook → `agentpolicy evaluate` | ✅ (first adapter) | ✅ |
| **Cursor** | hook / agentgate; `permissions.json` compiled by policyweave | ✅ | ✅ |
| **GitHub Copilot** (agent mode) | weakest hook surface → covered via enterprise/process layer (agentseatbelt) | documented lower-layer | ✅ (documented) |
| **OpenAI Codex CLI** | config/hook surface; agentgate | ✅ | ✅ |
| **Gemini CLI** | config/hook surface; MCP-native via agentgate | ✅ | ✅ |

> **Requirement:** all 5 Tier-1 harnesses are reachable at v0.1.0 through some enforcement point; **≥2 are
> exercised end-to-end** in the field test. Copilot's closed hook surface is covered at a lower layer and
> documented honestly.

## Tier-2 — Agent frameworks

| Framework | Surface | Version |
|---|---|---|
| **LangGraph** | library + tool-node adapter | v0.2.0 |
| **PydanticAI** | library + `@guard` decorator | v0.2.0 |
| **OpenAI Agents SDK** | library + guardrail hook | v0.2.0 |
| **CrewAI** | library + tool wrapper | v0.3.0 |
| **AutoGen / AG2**, **LlamaIndex**, **smolagents** | library adapters | v0.3.0 |

> **Requirement:** ≥3 Tier-2 adapters by v0.3.0, prioritized by community pull.

## Tier-3 — Protocol & enterprise

- **Generic MCP clients** (incl. Claude Desktop) — via the MCP-server surface and agentgate.
- **Enterprise platforms** (Copilot Studio, Agentforce, Bedrock agents) — reached via standards (MCP, OAuth,
  AuthZEN, OTel), not bespoke integrations; v2.x, design-partner driven.

## Verification & governance

- **agentdrill** ships per-harness attack packs; an enforcer's compatibility is verified when its pack passes in
  CI against the deployed stack.
- **Release notes carry a compatibility table** (harness × enforcer × version) — honest coverage, same rule as
  the capability table.
- **New harnesses** enter via community adapters; Tier assignment reviewed quarterly.
- **Drift** — the harness watchlist tracks Tier-1 format changes; **policyweave** drift alerts are the
  early-warning system when a harness changes its config surface.

## The portability angle (agentpolicy × policyweave)

agentpolicy is the **Cedar source of truth**; **policyweave** compiles one policy into each harness's native
format (Claude Code rules, Cursor `permissions.json`, Codex/Gemini config). This closes the "policy portability
across harnesses" whitespace (coverage-map row #14): multi-harness orgs maintain **one** policy, not N rule
files. agentpolicy decides; policyweave distributes; the enforcers enforce.
