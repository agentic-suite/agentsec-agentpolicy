# PRD 21 — Evidence Register & Method

**BLUF:** This document preserves the research behind agentpolicy so the reasoning is auditable: the **evidence
register** (E1–E15) with primary sources, the **gap analysis** the product closes, the **open PRD tensions**,
and the **method**. It exists so that a reviewer can check that the requirements are grounded, not asserted.

**Status:** Draft — v0.1.0 (2026-10-26) · **Owner:** @deghosal-2026 · **Parent:** agentic-suite #209 · PRD #211

## Evidence register

| # | Evidence | Used for | Source |
|---|---|---|---|
| **E1** | Only ~18% of MCP server deployments implement any tool-permission scoping; ~80% of orgs report agent actions beyond intended scope | Why policy is the gap | State of MCP Server Security 2025 / NHI research |
| **E2** | Replit's agent deleted a production database during a code freeze; the agent then misreported it | The Replit rule (destructive-command gate) | [Fortune, 2025-07-23](https://fortune.com/2025/07/23/ai-coding-tool-replit-wiped-database-called-it-a-catastrophic-failure/) |
| **E3** | MCP tool poisoning, rug-pull, cross-server shadowing | The MCP-allowlist pack | [Invariant Labs](https://invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks) |
| **E4** | OWASP Top 10 for Agentic Applications 2026 (ASI01–ASI10): goal hijack, tool misuse, identity & privilege abuse, supply chain, code execution, memory poisoning, inter-agent comms, cascading failures, trust exploitation, rogue agents | The coverage matrix + control set | [genai.owasp.org](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/) |
| **E5** | Cedar is a CNCF Sandbox project; formally verified (Lean) | Cedar as the primary language | [CNCF](https://www.cncf.io/projects/cedar/), [cedarpolicy.com](https://cedarpolicy.com/) |
| **E6** | AuthZEN Authorization API 1.0 reached **Final** (11 Jan 2026) — a standard PDP↔PEP API | The interop binding | [openid.net](https://openid.net/specs/authorization-api-1_0.html) |
| **E7** | NIST SP 800-162 defines the PDP/PEP + ABAC model | The decision contract | [NIST](https://nvlpubs.nist.gov/nistpubs/specialpublications/nist.sp.800-162.pdf) |
| **E8** | Credible prompt-injection defenses are architectural (dual-LLM, plan-then-execute, capabilities/taint — CaMeL/FIDES), not detection | "No ML in the path" decision | [arXiv 2506.08837](https://arxiv.org/abs/2506.08837); CaMeL |
| **E9** | Policy expressiveness + portability are OSS-led / unowned (coverage-map rows #13/#14) | The whitespace agentpolicy owns | agent-security research coverage map |
| **E10** | A predecessor policy engine proved the contextual decision model (4 outcomes, taxonomy, presets, audit, escalation) at OWASP 10/10 | The absorbed capability set | Predecessor `agent-tooltrust` (shipped; now private) |
| **E11** | Rate/spend limits are OSS-led (LiteLLM) but bound *model* traffic, not agent capability cumulatively | Blast-radius budgets | agent-security research |
| **E12** | MCP Authorization requires OAuth 2.1 + RFC 8707 resource indicators + RFC 9728 PRM | The authn context agentpolicy consumes | [MCP spec](https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization) |
| **E13** | OWASP LLM Top-10 2025 (LLM01/02/05/06) | The LLM-layer mapping | [genai.owasp.org](https://genai.owasp.org/llm-top-10/) |
| **E14** | NIST AI RMF 1.0 (AI 100-1) + GenAI Profile (AI 600-1); ISO/IEC 42001; EU AI Act Art. 12/14 | The governance mapping | [NIST](https://www.nist.gov/itl/ai-risk-management-framework), [ISO](https://www.iso.org/insights/iso-42001-explained) |
| **E15** | SLSA provenance + Sigstore signing + OpenSSF Scorecard are the supply-chain trust baseline | agentpolicy's own posture | [slsa.dev](https://slsa.dev/), [openssf.org](https://openssf.org/projects/slsa/) |
| **E16** | The Replit incident occurred **during an explicit code freeze** — a freeze the agent was told about but the stack did not enforce | Freeze windows (R33) | Incident register #6; [Fortune](https://fortune.com/2025/07/23/ai-coding-tool-replit-wiped-database-called-it-a-catastrophic-failure/) |
| **E17** | Multi-agent governance is weak and commercial-led (coverage row #19); ASI07/ASI08 are new risk classes with no OSS control | Multi-agent governance depth (R39) | Coverage map; [OWASP ASI 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/) |
| **E18** | Permission fatigue → users auto-approve; unmeasured approval quality is a known HITL failure mode | Approval analytics (R36) | PRD 01 problem #2; ASI09 |
| **E19** | AWS AgentCore generates Cedar from natural language — proof the demand exists, but without a proof loop | NL drafting gated on tests + review (R42) | AWS AgentCore Cedar-generation coverage, 2026 |

## Gap analysis (what agentpolicy closes)

| Gap | Evidence | agentpolicy answer |
|---|---|---|
| No product around Cedar (a language, not a decision service) | E5, E9 | A Cedar PDP with rule packs, explain, audit (PRD 02) |
| Policy is not portable across harnesses | E9 | Cedar source of truth + policyweave compile-out (PRD 19) |
| Harness-native rules are pattern-matching only | E9 | Five outcomes: ask/rate-limit/redact/deny/allow (PRD 05) |
| Irreversible actions have no reliable human gate | E2 | The mandatory human-gate class (R4, CUJ-10) |
| No cumulative capability budget | E11 | Blast-radius budgets (PRD 18) |
| Denials are black-box and get bypassed | E8, E10 | The explain-decision + actionability test (PRD 17) |
| Exfil chains need taint rules without ML | E8, E13 | The exfil-sink rule class (R10) |
| PDP↔PEP interop is bespoke | E6 | AuthZEN Authorization API 1.0 binding (R27) |
| Policy changes are unverified | E2, E10 | Golden fixtures + agentdrill incident replays (R22) |
| "I told the agent not to" is not a control (freeze) | E16 | Declared, audited freeze windows the *policy* enforces (R33) |
| Nothing derives data classes → adoption stalls | E9 | Declarative data-class derivation (R34) |
| Unknown agents are either lockout or unmanaged | E17 | Enrollment + probation posture (R35) |
| Approval quality is never measured | E18 | Rubber-stamp detection + the tuning report (R36) |
| Black-box denials get bypassed | E8, E10 | `permitted_alternatives[]` (R37) |
| Cedar learning curve blocks first-policy adoption | E19 | `agentpolicy draft` (tests + human review, advisory only) (R42) |

## PRD tensions (open decisions)

1. **Default posture** — `balanced` is the hypothesis for first-run; validate against real workloads before
   committing (RK-3).
2. **Ask-class boundaries** — which action classes are *always* `ask` vs. `deny` vs. allowed-with-audit? The
   Replit lesson says destructive+prod = gate; where does "external send" fall? (needs design-partner input)
3. **Budget semantics** — reset/inherit/cap across sessions and subagents (PRD 18).
4. **Counting model** — who counts budget dimensions: the PDP from the action stream, or the enforcer? (PDP, for
   one source of truth — but confirm latency).
5. **Cedar vs. Rego default** — Cedar is primary, but how loud is the Rego path in docs so contributors aren't
   confused by two authoring models? (DD-14)
6. **Taxonomy size at v0.1.0** — the full 13-domain set, or a curated core? (PRD 16)
7. **Tool-hiding depth** — how aggressively to hide tools an agent can't call before it breaks legitimate
   discovery? (R21)
8. ~~**Explain vs. leak** — what is the agent-facing vs. operator-facing split?~~ **Resolved by R37**: the agent
   gets `permitted_alternatives[]` in curated templates (evaluated-true, no policy internals); the operator
   explanation stays full-fidelity. The split is a tested contract ([PRD 22](22-policy-intelligence-and-governance.md), RK-19).
9. **Freeze scope** — can a freeze be declared by CLI at runtime, or only via git (a reviewed policy change)?
   Hypothesis: both — runtime declaration for incident response, git declaration for scheduled windows; both
   audited (R33).
10. **Probation duration** — how long before an unclassified agent is surfaced as a finding instead of silently
    running read-only? (R35)

## Method

- **Research base:** the agentic-suite agent-security research (coverage map, OSS/commercial matrices, incident
  register, standards & interception-points notes), ~85 sources.
- **Standards-first:** requirements are anchored to a standard where one exists (Cedar, AuthZEN, NIST 800-162,
  OWASP ASI/LLM, ATLAS, NIST AI RMF, ISO 42001, EU AI Act, SSDF, SLSA) — [PRD 20](20-standards-and-claims.md).
- **Parity-preserving:** every absorbed predecessor capability is disposed of explicitly
  ([PRD 10](10-feature-parity.md)); nothing is silently dropped.
- **Proof-anchored:** every shipped rule pack names the incident it stops and is verified by an agentdrill replay.
- **Deterministic by construction:** no ML in any decision path; every failure path is fail-closed.
- **Honesty rule:** the claims vocabulary ([PRD 20](20-standards-and-claims.md) §G) forbids over-claiming; a
  claims linter enforces it in CI.

## What would falsify this PRD

- If a **non-security engineer cannot write a useful policy in an afternoon**, the language/ergonomics thesis is
  wrong (R2).
- If **sub-100 ms p99** cannot be met locally, the inline-decision thesis is wrong (R8).
- If **callers re-implement policy** instead of calling agentpolicy, the "brain" thesis is wrong (RK-16).
- If **enforcers cannot express their needs** through the five outcomes, the outcome set is wrong (R1).
