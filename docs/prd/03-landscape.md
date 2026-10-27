# PRD 03 — Landscape

**BLUF:** The policy layer is the **OSS-led** area commercial players skip: commercial platforms ship
proprietary consoles (coverage-map row #13: commercial ●○○), while OSS has strong *languages* (Cedar, OPA,
OpenFGA) but no **product** — no decision service with rule packs, an explain contract, an audit trail, and
harness-portable output. agentpolicy sits exactly there: the productization of the Cedar/OPA decision layer,
harness-agnostic by construction. It migrates the shipped predecessor `agent-tooltrust` from a bespoke Python
risk engine to Cedar.

**Status:** Draft — v0.1.0 (2026-10-26) · **Owner:** @deghosal-2026 · **Parent:** agentic-suite #209 · PRD #211

## The market context

- **MCP standardizes *how* agents discover and invoke tools; it does not define *whether* a call should run.**
  The gap between "the model decided the call" and "the call was verified as permitted" is the policy gap.
- **Tool permissions are rarely scoped** — only an estimated ~18% of MCP server deployments implement any
  access scoping; ~80% of orgs admit agent actions beyond intended scope (State of MCP Server Security 2025).
- **OWASP classifies tool misuse and privilege abuse as first-class agentic risks** — ASI02 (Tool Misuse &
  Exploitation) and ASI03 (Agent Identity & Privilege Abuse) in the OWASP Top 10 for Agentic Applications 2026.
- **Safe autonomy is the enterprise adoption blocker** — "bounded autonomy" and "safe tool use" are named
  repeatedly as the gating concerns.

## Coverage map — where policy lives

From the agent-security research coverage map (Sept 2026; ●●● strong / ●●○ partial / ●○○ weak / ○○○ none):

| # | Capability | Commercial | OSS | Verdict |
|---|---|---|---|---|
| 13 | **Policy language expressiveness** | ●○○ (proprietary consoles) | ●●● (Cedar, OPA, OpenFGA, CPEX) | **OSS-led** |
| 14 | **Policy portability across harnesses** | ○○○ | ○○○ | **Nobody** |
| 4 | Tool-call blocking (MCP-routed) | ●●● | ●●● | Both covered |
| 5 | Tool-call blocking (local shell/fs) | ●○○ | ●●● (Leash, ActPlane, IronScope) | OSS-led |
| 6 | Rate / spend limits | ●●○ | ●●● (LiteLLM) | OSS-led |
| 17 | Compliance evidence | ●●● | ○○○ | Commercial-only |

**agentpolicy owns rows #13 and #14** (expressiveness + portability) — the source-of-truth policy layer that
agentgate/agentseatbelt/agentkernel/agentkeys enforce, and that **policyweave** compiles into each harness's
native format.

## OSS policy tooling (what exists, what's missing)

| Project | Strengths | Gap agentpolicy closes |
|---|---|---|
| [Cedar](https://cedarpolicy.com/) | Typed, analyzable, formally verified; **CNCF Sandbox**; emerging agent-sandbox default (Leash, brood-box, cmcp, CPEX) | Not a product — needs a runtime, rule packs, explain, audit |
| [OPA](https://www.openpolicyagent.org/) | De-facto PDP standard; agent guides exist | Rego learning curve; no agent-native constructs; agentpolicy imports it as a peer backend |
| [OpenFGA](https://openfga.dev/docs/modeling/agents) | Relationship-based agent→tool→resource (Zanzibar ReBAC) | Needs gateway wiring; no per-action decisions |
| [CPEX](https://github.com/contextforge-org/cpex) | Rust reference monitor orchestrating Cedar/CEL/OPA/AuthZEN + taint | Closest to "the product" — young, narrow, Rust-first |
| [prempti](https://github.com/falcosecurity/prempti) | "Falco for AI coding agents"; YAML rules → allow/deny/ask | YAML only (not analyzable/portable); enforcement, not a reusable PDP |
| [Leash](https://github.com/strongdm/leash) | Containers + Cedar policies via eBPF per-cgroup | Linux/containers; enforcement point, not a general PDP |
| Harness-native rules (Claude Code `allow/ask/deny`, Cursor `permissions.json`) | Zero-install, native | Pattern-matching only; not portable; cannot express ask-class/rate-limit/taint |

## Commercial tooling (their turf, our wedge)

| Project | What it does | Decision | Our wedge |
|---|---|---|---|
| **Permit0** | Rust policy engine; 22-domain/159-verb taxonomy; risk seeding; signed audit | allow/deny/human | Heavyweight; requires their taxonomy + Rust runtime; less teachable |
| **Microsoft AGT** | OSS governance between MCP client & servers: Rego/OPA, identity tiers | per-call rules | Opinionated identity layer (SPIFFE) — heavy; not a small self-contained library |
| **Vercel `@ai-sdk/policy-opa`** | OPA-backed `toolApproval` callback | allow/deny/requires-approval | JS-only; couples to one framework's approval API |
| Proprietary consoles (Zenity, Lasso, Pillar) | Enterprise policy consoles | proprietary | Lock-in; no portability; no OSS audit trail |

## What agentpolicy is *not* competing with

- **Injection classifiers** (Llama Guard, llm-guard, LangKit) — empirically weak; agentpolicy is architectural
  and deterministic, not detection ([PRD 14](14-non-goals.md)).
- **Enforcement points** — agentgate (MCP proxy), agentseatbelt/agentkernel (confinement), agentkeys
  (credential issuance), agenthalt (halt). agentpolicy *serves* them; it never enforces.
- **Compliance suites** (agentcomply) — agentpolicy emits evidence; agentcomply maps it to controls.
- **Posture scanners / AI-BOM** (Lasso, agent-scan) — out of scope.

## Whitespace (the build list, mapped to agentpolicy)

1. **#13 Policy expressiveness productized** — Cedar PDP with shipped rule packs, explain, audit.
2. **#14 Policy portability** — agentpolicy is the Cedar source of truth; policyweave compiles it outward
   (Claude Code rules, Cursor `permissions.json`, Codex/Gemini configs).
3. **Blast-radius budgets** — cumulative per-session capability ceilings; exhaustion = halt. No competitor
   ships this ([PRD 18](18-blast-radius-budgets.md)).
4. **Exfil-sink taint-lite rules** — block tool outputs carrying secrets/PII from reaching external-sink tools
   without ML ([PRD 16](16-rule-packs.md)).
5. **Ask-gate as a first-class decision** — `ask` is an outcome, not a bolted-on prompt; bound to action
   identity, time-boxed, timeout=deny ([PRD 04](04-users-and-cujs.md) CUJ-10).
6. **AuthZEN interop** — a standard PDP↔PEP API so non-Python hosts and other PDPs can interop
   ([PRD 20](20-standards-and-claims.md)).

## Migration from the predecessor

The predecessor policy engine (`agent-tooltrust`, shipped, now private) proved the decision model: 4-state outcomes
(allow/audit/escalate/deny), a 13-domain action taxonomy, posture presets, explainability, an audit log,
escalation round-trip, and OWASP 10/10 coverage. agentpolicy **keeps the model, changes the engine** — Cedar
instead of a bespoke Python scorer — and extends 4 outcomes to 5 (adding `rate-limit` and folding `audit` into
always-on event emission, `escalate` into `ask`). The full capability-by-capability disposition is
[PRD 10](10-feature-parity.md).
