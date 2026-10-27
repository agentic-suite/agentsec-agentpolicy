# PRD 09 — Roadmap

**BLUF:** **v0.1.0** ships the decision foundation — five outcomes from Cedar, three launch rule packs, the
explain contract, decisions in the agentwatch schema, git-reviewed policies, and local-first sub-100 ms
decisions with fail-closed degradation. **v0.1.x/v0.2.0** add budgets, exfil-sink + step-up rules, session
state, argument validation, the adversarial suite, and AuthZEN interop. **v0.3.0+** add OPA→Cedar migration,
the pack marketplace, child delegation, and fleet policy sync — no deferred proof.

**Status:** Draft — v0.1.0 (2026-10-26) · **Owner:** @deghosal-2026 · **Parent:** agentic-suite #209 · PRD #211

## Versions

| Version | Theme | Scope |
|---|---|---|
| **v0.1.0** (Wave 0) | **The decision foundation** | R1–R8 + parity essentials: five outcomes (allow/deny/ask/rate-limit/redact); Cedar authoring + OPA/Rego import; 3 launch rule packs (Replit rule, secret-in-output, MCP allowlist); mandatory human-gate class; `explain-decision`; decisions in the agentwatch schema; git-reviewed policies; local-first sub-100 ms with fail-closed degradation; contextual decision model (5 dimensions + 13-domain taxonomy); posture presets + `init`; ask round-trip; redact-and-allow; adversarial normalization; delivery surfaces (library/CLI/MCP/HTTP); shadow mode; CI regression suite. ≥2 Tier-1 harnesses exercised via enforcers |
| **v0.2.0** | **Budgets, taint, step-up, interop + policy intelligence + enterprise adoption** | R9 blast-radius budgets; R10 exfil-sink rule class; R11 scope-escalation + step-up; R12 rule-pack lint; R17 session state (cumulative risk, consent scope, replay); R19 argument-level validation; R21 discovery-time tool hiding; R26 adversarial suite (replay/flood); R27 AuthZEN Authorization API 1.0 binding; R29 pack catalog + `pack validate`/`test`; R32 compliance-mapped evidence export; **R33 freeze windows; R34 data-class derivation; R35 agent enrollment + probation; R36 approval analytics (rubber-stamp detection); R37 nearest-permissible-action; R38 secrets-in-args** ([PRD 22](22-policy-intelligence-and-governance.md)); **R43 policy backtest + PR decision-diff; R44 narrow-only layering; R45 action-space coverage report; R46 self-attack pack; R47 allow-justification** ([PRD 23](23-enterprise-adoption-and-governance-hardening.md)); ≥3 Tier-2 framework adapters |
| **v0.3.0** | **Migration, marketplace, delegation + high-assurance governance** | R13 OPA→Cedar migration assistant; R14 policy-pack marketplace (verified badges); **R39 multi-agent governance depth** (delegation chains, scope-subset proofs, inter-agent decisions — extends R25); **R40 break-glass with auto-revert; R41 dual-control approvals; R42 NL policy drafting**; deeper taxonomy packs (cloud/IAM/payment); full OWASP ASI coverage |
| **later** | **Fleet coherence** | R31 fleet/distributed policy sync (OPAL or equivalent); cross-PDP interop; enterprise-platform coverage via standards |

## Compatibility targets by version

| Version | Tier-1 coding agents | Tier-2 frameworks |
|---|---|---|
| **v0.1.0** | all 5 day one (PDP behind any enforcer/hook); ≥2 exercised in the field test | library + MCP-server surface |
| v0.2.0 | all 5 via the enforcers | ≥3 adapters (LangGraph, PydanticAI, OpenAI SDK) |
| v0.3.0 | all 5 + documented lower-layer coverage | + CrewAI, AutoGen, LlamaIndex, smolagents |

> agentpolicy is harness-agnostic **by construction** — it is a PDP behind the enforcer, so it works for any
> harness with any enforcement point. "Compatible" means the enforcer that calls it is exercised in the field
> test; the release compatibility table states honest coverage ([PRD 19](19-harness-compatibility.md)).

## Migration & deprecation

- **Predecessor:** the shipped predecessor policy engine (`agent-tooltrust`) is retired and superseded; its
  decision model lives on inside agentpolicy ([PRD 10](10-feature-parity.md)).
- **BehaviorGuard:** unbuilt; its enforcement intent is absorbed into the ask/deny/budget surface.
- **No silent behavior change:** a change to a shipped rule pack or a posture default is a versioned, reviewed
  policy change with a migration note — never a quiet edit.

## Release cadence

Each version ships with: release notes, a **compatibility table** (harness × enforcer × version), a **security
audit** (org governance floor), and a **published standards coverage matrix** ([PRD 20](20-standards-and-claims.md)).
Articles accompany each release per the ecosystem content plan.

## Ecosystem dependency

agentpolicy needs **callers**: it decides for agentgate (MCP proxy), agentseatbelt/agentkernel (confinement),
agentkeys (credential issuance), agenthalt (budget/halt), harness hooks, and any framework adapter. It ships
early in Wave 0 (the thin-slice meta-MVP) and grows as more enforcers land. policyweave compiles its policies
outward; agentdrill tests its rule packs; agentwatch records its decisions.

The Wave-0 meta-installer (`npx @agentic-suite/cli init`, monitor-only by default) wires agentpolicy in as the
decision service behind the installed enforcers; `agentsec init --enforce` turns the policy gates on — the
installer never invents its own enforcement, it flips agentpolicy's documented contract on.
