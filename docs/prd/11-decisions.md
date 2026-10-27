# PRD 11 — Decisions

**BLUF:** Accepted decisions for v0.1.0: **Apache-2.0**, Python core with a CLI wrapper, **Cedar** as the
primary policy language (OPA/Rego as a peer backend), **five outcomes**, **no ML in any decision path**, the
**agentwatch security-event schema** as the machine-readable decision surface, **AuthZEN Authorization API 1.0**
for PDP↔PEP interop, git-reviewed policies, and the hard architectural rule that **agentpolicy decides and
never enforces**.

**Status:** Draft — v0.1.0 (2026-10-26) · **Owner:** @deghosal-2026 · **Parent:** agentic-suite #209 · PRD #211

## Design & architecture

| # | Decision | Rationale |
|---|---|---|
| **DD-01** | **agentpolicy owns no enforcement** — it decides; callers enforce | A decision service that enforces would test itself, not the user's stack (PRD 02) |
| **DD-02** | **Cedar is the primary policy language** | Typed, analyzable, formally verified, CNCF Sandbox, the emerging agent-sandbox default (PRD 03) |
| **DD-03** | **Five outcomes** — allow/deny/ask/rate-limit/redact | Richer than allow/deny; the ask-gate and budget are first-class (R1) |
| **DD-04** | **No ML/classifier in any decision path** | Determinism is a product requirement; the LLM at most is a non-authoritative advisor that can narrow, never widen |
| **DD-05** | **Reuse the agentwatch security-event schema** for decisions | Single source of truth across the ecosystem; decisions flow into analytics/compliance (R6) |
| **DD-06** | **Fail-closed everywhere** — any failure → `deny` with a distinct reason | The safety spine (R8, CUJ-9) |
| **DD-07** | **The LLM advisor is non-authoritative** and can only narrow/escalate | Prevents a steered explanation from widening scope |
| **DD-08** | **Harness-agnostic by construction** (a PDP behind the enforcer) | Ecosystem non-negotiable; works for any harness with any enforcement point |
| **DD-09** | **Canonical action shape** shared by normalizer and evaluator | Closes dispatcher-bypass and tool-name-obfuscation gaps (R24) |
| **DD-10** | **AuthZEN Authorization API 1.0** as the interop binding | A standard PDP↔PEP API (Final Jan 2026); avoids a bespoke protocol (R27) |

## Scope

| # | Decision | Rationale |
|---|---|---|
| **DD-11** | **v0.1.0 = Wave 0**: five outcomes + 3 rule packs + explain + event schema + sub-100 ms | Matches the release-roadmap meta-MVP |
| **DD-12** | **Ask is reserved for irreversible actions** | Avoid ask-fatigue, which users defeat by auto-granting (RK-9) |
| **DD-13** | **Blast-radius budgets are a v0.1.x commitment, not v0.1.0** | Novel class; needs session state to land first (R9, R17) |
| **DD-14** | **OPA/Rego is an import/peer backend, not the default** | Cedar is primary; OPA serves orgs already invested (R2, DD-02) |
| **DD-15** | **No console/UI beyond CLI in v1** | Policies are text; review lives in git |
| **DD-16** | **No self-hosted PDP-service hardening in v1** | Local-first first (R8) |

## Technical

| # | Decision | Rationale |
|---|---|---|
| **DD-17** | **Python core** (library + CLI + MCP server), shared evaluate/explain engine | Parity with the predecessor; one engine, several surfaces |
| **DD-18** | **Cedar text policies** (+ OPA/Rego), versioned in git | Authoring ergonomics; analyzability; portability |
| **DD-19** | **`pip install agentsec-agentpolicy`**, CLI `agentpolicy`, package `agentpolicy` | Ecosystem naming convention |
| **DD-20** | **Local JSON artifacts under `.agentpolicy/`** (decisions, goldens, packs, audit) | Local-first; sibling to the predecessor store |
| **DD-21** | **Sub-100 ms p99** inline budget; no network in the hot path | The PDP must not slow the agent loop (R8) |
| **DD-22** | **Action-identity binding** on every ask approval | Prevents replay (R18, RK-11) |
| **DD-23** | **Tamper-evident audit from v0.1.0** (hash chain) | The decision log is forensic evidence (F17) |
| **DD-24** | **Policy hash + version in every decision** | "Which policy governed this decision?" is always answerable (R7) |
| **DD-25** | **Apache-2.0 license** | Ecosystem standard; matches repo LICENSE |

## Governance

| # | Decision | Rationale |
|---|---|---|
| **DD-26** | **Policies reviewed like code** (two-party review) | A policy change is a security change (R7) |
| **DD-27** | **Rule packs are reviewed + signed** | Community packs are executable security claims (R29) |
| **DD-28** | **Public standards coverage matrix** (OWASP ASI/LLM, ATLAS, NIST, EU AI Act, ISO 42001) | Trust posture; regenerated per release (R32, [PRD 20](20-standards-and-claims.md)) |
| **DD-29** | **Signed releases + provenance** (Sigstore/SLSA) | Supply-chain trust; the ecosystem's own supply chain must be clean |
| **DD-30** | Each release ships **notes + compatibility table + security audit + standards coverage** | Org governance floor |
| **DD-31** | **Flag, never silently change** — a rule-pack or posture change is versioned with a migration note | Trust posture; no quiet edits |
| **DD-32** | **agentpolicy is the single source of authorization truth** | Enforcers call it; nobody ships a parallel rule registry (RK-16) |
