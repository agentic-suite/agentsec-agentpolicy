# PRD 10 — Feature Parity

**BLUF:** agentpolicy absorbs the decision model of the shipped predecessor policy engine (`agent-tooltrust`,
now private) and the enforcement intent of **BehaviorGuard** (#192, unbuilt). This document disposes of **every**
absorbed capability — **delivered**, **delegated** (to another ecosystem tool), or **waived** (with reason) —
so no capability is silently dropped. The engine changes (a bespoke Python risk scorer → **Cedar**); the
capability set is preserved and extended (4 outcomes → 5).

**Status:** Draft — v0.1.0 (2026-10-26) · **Owner:** @deghosal-2026 · **Parent:** agentic-suite #209 · PRD #211

## Source of the absorbed capabilities

- **`agent-tooltrust`** — a contextual risk and permission engine for tool-using agents (shipped v0.2.0, MIT,
  archived; now private). It proved the decision model: contextual risk scoring, a 13-domain action taxonomy,
  posture presets, explainability, an audit log, and an escalation round-trip, with OWASP 10/10 coverage.
- **`BehaviorGuard`** (#192) — an unbuilt behavioral-enforcement idea; only its intent is absorbed (nothing to
  port).

## Capability disposition

| # | Absorbed capability | What it did | Disposition | Where |
|---|---|---|---|---|
| P1 | **4-state decision** (allow/audit/escalate/deny) | Per-call outcome | **Delivered, extended** → 5 outcomes: `allow`, `deny`, `ask` (was escalate), `rate-limit` (new), `redact` (new); `audit` folded into always-on event emission | R1, [PRD 05](05-features.md) |
| P2 | **Contextual risk dimensions** (tool category, action class, environment, data sensitivity, agent class) | Weighted risk score | **Delivered** — same dimensions as Cedar context entities | R15 |
| P3 | **13-domain action taxonomy** (60+ verbs) | Canonical vocabulary | **Delivered** — shipped as a policy module + rule packs | R15, [PRD 16](16-rule-packs.md) |
| P4 | **3-tier customization** (default taxonomy / org overrides / community packs) | Policy layering | **Delivered** — Cedar modules + rule packs + org overlay | R2, R16, R29 |
| P5 | **Policy versioning + migration check** | Semver'd policy + breaking-change report | **Delivered** — `policy_version` in every decision; `agentpolicy check --migrate` | R7 |
| P6 | **Posture presets** (strict/balanced/permissive) | Pre-populated policies | **Delivered** — `agentpolicy init --posture` | R16 |
| P7 | **`init` scaffold** (commented policy + adapter + quickstart) | Zero-blank-slate start | **Delivered** | R16 |
| P8 | **Delivery modes** (library, MCP client wrapper, MCP server, HTTP PDP, CLI, framework adapters) | Multi-surface | **Delivered** — plus an **AuthZEN** binding | R28, R27 |
| P9 | **OPAL distributed policy sync** | Fleet policy propagation | **Waived at v0.1.0** — documented path is git + shared load; R31 later | R31 |
| P10 | **Explainability** (explanation, reason_code, criticality, factors) | Readable decisions | **Delivered** — the `explain-decision` contract | R5, [PRD 17](17-explain-decision-and-evidence.md) |
| P11 | **Audit log** (JSONL/SQLite/Postgres, export/query, policy version) | Decision record | **Delivered** — plus agentwatch event emission | R6, R7 |
| P12 | **Tamper-evident hash chain** | Uneditable history | **Delivered, promoted to P0** (was P2 in the predecessor) | R7 |
| P13 | **Session state** (cumulative risk, consent scope, budgets, replay) | Context-aware decisions | **Delivered** — budgets are the novel blast-radius class | R17, R9, [PRD 18](18-blast-radius-budgets.md) |
| P14 | **Escalation round-trip** (approval bound to action identity, expiry) | Human gate | **Delivered** as `ask` — action-identity binding, expiry, timeout=deny | R18 |
| P15 | **Argument-level semantic validation** (regex/range/enum/path/URL) | Per-argument checks | **Delivered** | R19 |
| P16 | **Output inspection** (redact secrets/PII) | Scrub tool results | **Delivered** as `redact` + receipts | R20 |
| P17 | **Discovery-time tool hiding** | Don't expose uncallable tools | **Delivered** | R21 |
| P18 | **CI policy regression suite** (golden fixtures) | Deterministic drift detection | **Delivered** | R22 |
| P19 | **Rate/burst limits** | Throttle runaway agents | **Delivered** as the `rate-limit` outcome | R23 |
| P20 | **Dispatcher-bypass safety** | Canonicalize coarse input | **Delivered** + tool-name normalization | R24 |
| P21 | **Child-agent delegation scope** (subset of parent) | Confused-deputy protection | **Delivered** (v0.3.0) | R25 |
| P22 | **Adversarial resilience suite** (normalization, replay, flood) | Can't be tricked | **Delivered** | R26 |
| P23 | **Demo reference agent** | All outcomes in one narrative | **Delivered** | R1, [PRD 05](05-features.md) F29 |
| P24 | **Score calibration / shadow mode** | Trust before enforce | **Delivered** as `dry_run` + calibration report | R30 |
| P25 | **Policy packs catalog + `pack validate`/`test`** | Reusable packs | **Delivered** | R29 |
| P26 | **Security baselines** (OWASP 10/10, OpenSSF, a product baseline) | Published posture | **Delivered** — OWASP **ASI** 2026 mapping + OpenSSF + an agentpolicy baseline | R32, [PRD 20](20-standards-and-claims.md) |
| P27 | **OPA/Rego parity** | Dual authoring | **Delivered** — OPA/Rego as a peer backend | R2 |
| P28 | **HTTP `/authorize` PDP endpoint** | Language-agnostic caller | **Delivered, superseded** by the AuthZEN Authorization API 1.0 binding | R27 |
| P29 | **Framework adapters** (raw, MCP client, LangGraph, PydanticAI, OpenAI SDK, CrewAI) | Framework-native | **Delivered** (≥3 by v0.3.0) | R28 |
| P30 | **SWE-bench integration** | Govern coding agents | **Delegated** → agentdrill (drives deployed stacks); agentpolicy serves its decisions | — |
| P31 | **Tool-definition scanning** (poisoning/typosquat) | Scan tool descriptions | **Delegated** → agentgate (MCP proxy scans on connect); agentpolicy consumes the verdict | — |
| P32 | **Stale-credential classification** | Tag credential-rejected calls | **Delegated** → agentkeys (credential issuance/revocation) | — |
| P33 | **Session analytics / deny→allow transitions** | Cross-session insight | **Delegated** → agentwatch (analytics over the event stream) | — |
| P34 | **Fleet deployment guide** | Multi-node PDP | **Waived** — folded into R31 (fleet sync) | R31 |
| P35 | **External verification sink** | Third-party verification | **Delegated** → agentwatch (verifier pattern) | — |

## BehaviorGuard (#192) disposition

| Absorbed intent | Disposition | Where |
|---|---|---|
| Behavioral enforcement (block on behavior) | **Delivered** — as `deny`/`ask`/budget-exhaustion over the event stream | R1, R9, R18 |
| Nothing shipped to port | **Waived** (unbuilt predecessor) | — |

## Parity guarantees

- **No capability silently dropped** — every row above is delivered, delegated (with the owning tool named), or
  waived (with reason).
- **No competing registry** — agentpolicy is the ecosystem's single source of authorization truth; delegated
  capabilities live in exactly one tool.
- **Extension, not regression** — the 4-state model becomes 5; `audit` becomes always-on; the engine moves to
  Cedar for analyzability and portability.
