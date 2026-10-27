# PRD 00 — Press Release / FAQ

**BLUF:** agentpolicy is a **local-first Cedar policy decision point** that answers one question for every
agent action — *"may this agent do this, with these arguments, in this context, now?"* — and returns one of
**five outcomes: allow, deny, ask (human gate), rate-limit, or redact**. It ships the rule packs that stop the
incidents that actually happened (the Replit rule, secret-in-output, MCP allowlist, exfil-sink), explains every
denial to a clause, and emits each decision in the open agentwatch security-event schema. It is the
ecosystem's **brain**: every enforcer (agentgate, agentseatbelt/agentkernel, agentkeys, agenthalt) calls it.

**Status:** Draft — v0.1.0 (2026-10-26) · **Owner:** @deghosal-2026 · **Parent:** agentic-suite #209 · PRD #211

## Press release

### agentpolicy — firewall rules for agents, in a language you can test

*Open-sourced today, agentpolicy turns "what is this agent allowed to do?" into a git-reviewed Cedar policy
file that returns allow / deny / ask / rate-limit / redact for every tool call — with a signed, explainable
audit record for each one.*

Every vendor ships a proprietary policy console; every open-source enforcer invents its own YAML. Teams
connecting agents to real systems (shell, filesystem, cloud, databases, payment rails) are stuck between two
bad options: **over-privileged agents** (dangerous) and **"approve everything"** (permission fatigue, which
users defeat by auto-granting durable approvals). Flat allow-lists are a *reachability* control, not an
*authorization decision* — the same tool is harmless in staging and dangerous in production; the same read is
fine on public docs and risky on customer data.

agentpolicy makes the decision explicit and testable. Policies are written in **Cedar** — a typed, analyzable
language — so a platform engineer can *prove* why an action was blocked, unit-test the policy in CI, and review
changes like code. It is the emerging default for agent sandboxes (Leash, brood-box, cmcp, CPEX all chose
Cedar); agentpolicy is the missing runtime: a general, harness-agnostic decision service with **usable rule
packs** and an **explain-decision** contract.

> *"Your agent isn't safe because it's allowed to do things. It's safe because you can prove what it isn't."*

**How it works**

1. An enforcer — a harness hook, the MCP proxy, the credential broker, the confinement layer — asks agentpolicy
   about a proposed action.
2. agentpolicy evaluates the **Cedar policy** against the action + context and returns one of five outcomes
   with an explanation, in **sub-100 ms** (p99), locally.
3. `ask` routes to a human gate (agentinbox); `rate-limit` throttles; `redact` allows the call but scrubs the
   output. Every decision is emitted in the agentwatch schema and audited.
4. A `deny` names the matched policy clause; a CI gate rejects a policy PR that un-blocks a known incident
   replay (agentdrill).

**Availability:** installable via `pip install agentsec-agentpolicy`, source under Apache-2.0 on GitHub.
v0.1.0 targets **≥2 Tier-1 coding-agent harnesses** through the enforcers that call it, per the ecosystem
harness-compatibility matrix ([PRD 19](19-harness-compatibility.md)).

## FAQ

**Is agentpolicy another prompt-injection detector?**
No. It is the opposite of a classifier: **deterministic, no ML in any decision path.** It evaluates the
*proposed action* against policy — the model cannot argue its way past a rule it never sees
([PRD 14](14-non-goals.md)).

**Does it enforce, or just decide?**
It **decides only.** Enforcement lives in the enforcers that call it (agentgate, agentseatbelt/agentkernel,
agentkeys, agenthalt, harness hooks). A decision service that also enforced would be two products
([PRD 02](02-architecture.md)).

**Why Cedar, not YAML?**
Cedar is typed and analyzable: you can reason about whether a policy set is over-permissive, unit-test it, and
carry it across harnesses. YAML allow-lists cannot express "ask a human for a prod write" or "rate-limit per
session." agentpolicy also **imports OPA/Rego** for orgs already invested ([PRD 20](20-standards-and-claims.md)).

**What are the five outcomes?**
`allow`, `deny`, `ask` (human gate — the default for irreversible actions), `rate-limit` (per session/agent
budgets), and `redact` (allow, but scrub secrets/PII from the output). See [PRD 05](05-features.md).

**What is a "blast-radius budget"?**
A cumulative, per-session capability ceiling — *"10 files modified, 20 requests sent, $5 spent, then stop."*
Exhaustion triggers a halt. No competitor ships this ([PRD 18](18-blast-radius-budgets.md)).

**Is it honest about failure?**
Yes. Every decision path is **fail-closed**: unknown tool, malformed policy, unreachable engine, or timeout
returns `deny` with a distinct `reason_code` — never a silent allow ([PRD 13](13-non-functional-requirements.md)).

**How is it built?**
It absorbs the **decision model of the shipped predecessor policy engine** (now private) — its contextual risk
model, taxonomy, posture presets, audit, and escalation round-trip — and the **enforcement intent of
BehaviorGuard** (#192), re-pointed from a Python risk engine to a **Cedar PDP that is the ecosystem's single
source of authorization truth** ([PRD 10](10-feature-parity.md)).

**Who is it for?**
Platform/security engineers (**P1 Maya**, **P2 Ravi**) who must give agents real access without dangerous
over-permission, and ecosystem builders (**P5 Alex**) who need a decision service to call.
