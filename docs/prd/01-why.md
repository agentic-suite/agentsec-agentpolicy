# PRD 01 — Why

**BLUF:** Policy expressiveness is the OSS-led area commercial players skip — every vendor ships a proprietary
console, every OSS enforcer invents its own config. Harness-native rules are pattern-matching only and cannot
express *"ask a human for prod infra," "rate-limit per session,"* or *"block secrets in tool output from
reaching external tools."* Cedar is the emerging default for agent sandboxes, but **nothing ships it as a
general, harness-agnostic decision service with usable rule packs.** agentpolicy is that missing layer — the
ecosystem's brain. It **absorbs the decision model of the shipped predecessor policy engine** and the
enforcement intent of **BehaviorGuard**.

**Status:** Draft — v0.1.0 (2026-10-26) · **Owner:** @deghosal-2026 · **Parent:** agentic-suite #209 · PRD #211

## The problem

1. **Policy is the commercial blind spot.** Commercial platforms all have a proprietary policy console
   (coverage-map row #13: commercial ●○○, OSS ●●●). Every OSS enforcer invents its own YAML/config — prempti,
   Leash, LiteLLM, Claude Code rules, Cursor `permissions.json` all differ.
2. **Harness-native rules are too weak.** Claude Code `allow`/`ask`/`deny` rules and Cursor `permissions.json`
   are pattern-matching on tool names/arguments. They cannot reliably express *"ask a human for production
   infrastructure changes,"* *"rate-limit per session,"* or *"block tool outputs carrying secrets from reaching
   external-sink tools."* Real incidents demand richer decisions than allow/deny.
3. **Real incidents demand ask-gates, taint rules, and step-up.** The Replit agent deleted a production
   database during a code freeze — an *irreversible* action with no human gate. Exfiltration chains need
   taint-style rules. Scope escalation needs step-up handling.
4. **Cedar has no product around it.** Cedar is the emerging default policy language for agent sandboxes
   (Leash, brood-box, cmcp, CPEX), is now a **CNCF Sandbox** project, and is formally verified — but it is a
   language + engine, not a decision service with rule packs, an explain contract, and an audit trail.
5. **The ecosystem's own claims depend on this.** agentgate, agentseatbelt/agentkernel, agentkeys issuance,
   and agenthalt all need one place to ask *"is this allowed?"* Without it, each re-implements policy.

## Evidence from the landscape

| Evidence | Source |
|---|---|
| Tool permissions are rarely scoped; ~80% of orgs report agent actions beyond intended scope | State of MCP Server Security 2025 / NHI research |
| Tool misuse is a first-class agentic risk | [OWASP Top 10 for Agentic Applications 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/) — ASI02 (Tool Misuse), ASI03 (Identity & Privilege Abuse) |
| Replit agent deleted a production database during a code freeze | [Fortune, 2025-07-23](https://fortune.com/2025/07/23/ai-coding-tool-replit-wiped-database-called-it-a-catastrophic-failure/) |
| MCP tool poisoning / rug-pull / cross-server shadowing | [Invariant Labs](https://invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks) |
| Cedar is the emerging agent-sandbox default; CNCF Sandbox | [cedarpolicy.com](https://cedarpolicy.com/), CNCF |
| A standard PDP↔PEP API now exists (AuthZEN Authorization API 1.0, Final Jan 2026) | [OpenID AuthZEN](https://openid.net/specs/authorization-api-1_0.html) |
| Detection is empirically weak; credible defenses are architectural (policy, separation, least privilege) | [arXiv 2506.08837](https://arxiv.org/abs/2506.08837), CaMeL (capabilities + deterministic interpreter) |

The incident register (agent-security research base) supplies the rule packs: Replit destructive-command,
secret/PII-in-output exfiltration, MCP-server allowlist, exfil-sink taint, and scope-escalation.

## What agentpolicy is

> **"Firewall rules for agents — one Cedar policy file decides what any agent may do, and every decision is
> explainable."**

The **brain**: a deterministic, local-first Cedar PDP that returns allow/deny/ask/rate-limit/redact for every
agent action, with shipped rule packs, an `explain-decision` contract, blast-radius budgets, and every decision
emitted to the agentwatch event schema. Harness-agnostic by construction (it sits *behind* every enforcer);
local-first, CI-second.

## What this supersedes / absorbs

| Absorbed | What it was | What agentpolicy takes from it |
|---|---|---|
| **predecessor policy engine** (`agent-tooltrust`, shipped, now private) | Contextual risk + permission engine for tool-using agents (allow/audit/escalate/deny) | The contextual decision model (5 risk dimensions, 13-domain action taxonomy), posture presets, explainability contract, audit log + export, escalation round-trip, argument validation, policy packs, session state, baselines — re-pointed from a Python risk engine to a **Cedar PDP** ([PRD 10](10-feature-parity.md)) |
| **`BehaviorGuard`** (#192, unbuilt) | Behavioral enforcement intent | The enforcement intent folded into the ask/deny/budget surface; nothing shipped to port |

The ecosystem thesis is **unification**: one install, one record format, one policy source of truth.

## Why now

The ecosystem is at **Wave 0**: agentwatch, agentpolicy, agentkeys, agenthalt, and agentdrill ship together as
the thin-slice meta-MVP. agentpolicy is the decision service the other four call. The policy row
(OSS "tooling for researchers") is converting into a **shippable decision product** that is currently unowned:
Cedar is standard, AuthZEN is final, and the incident register is fresh.

## What success looks like

A **non-security engineer writes their first useful Cedar policy in an afternoon** and can prove — via
`explain-decision` — why an action was blocked; a policy PR that un-blocks a known attack is rejected by CI
(agentdrill); and every enforcer in the ecosystem asks agentpolicy instead of inventing its own config. See
[PRD 04](04-users-and-cujs.md) and [PRD 07](07-success-metrics.md).

## Non-goals

agentpolicy **decides and does not enforce** — it never becomes a PEP. No ML/classifier in any decision path;
no console/UI beyond CLI in v1; no self-hosted PDP-service hardening story in v1 (local-first first). Full list
in [PRD 14](14-non-goals.md).
