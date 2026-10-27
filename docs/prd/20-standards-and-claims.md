# PRD 20 — Standards, Claims & Interop

**BLUF:** agentpolicy is built **on** the authorization standards (Cedar, XACML/ABAC, AuthZEN, OPA) and
**certifies against** the security & AI-governance frameworks (OWASP ASI/LLM, MITRE ATLAS, NIST AI RMF, ISO/IEC
42001, EU AI Act, NIST SSDF, OpenSSF/SLSA). This document is the **claim surface**: what agentpolicy implements,
what it aligns to, what it is certified against, and — critically — a **claims vocabulary** that forbids
over-claiming. The coverage matrix is regenerated per release.

**Status:** Draft — v0.1.0 (2026-10-26) · **Owner:** @deghosal-2026 · **Parent:** agentic-suite #209 · PRD #211

## A. Authorization & policy standards (agentpolicy implements these)

| Standard | Status | What agentpolicy implements |
|---|---|---|
| **Cedar policy language** ([cedarpolicy.com](https://cedarpolicy.com/), **CNCF Sandbox**, Lean-verified) | Mature | Cedar is the primary policy language; typed, analyzable, formally verified; the emerging agent-sandbox default (Leash, brood-box, cmcp, CPEX) |
| **NIST SP 800-162 — Guide to ABAC** ([nvlpubs](https://nvlpubs.nist.gov/nistpubs/specialpublications/nist.sp.800-162.pdf)) | Published (2014) | The PDP/PEP split and the attribute model: `principal` (subject), `action`, `resource`, `context` — agentpolicy is the PDP, the enforcers are PEPs |
| **XACML (OASIS)** | Mature | The origin of the PDP/PEP pattern; agentpolicy adopts the model (decision, obligations/advice) without the XML |
| **ISO/IEC 29146 — access control framework** | Published | Terminology alignment: policy decision vs. policy enforcement vs. policy administration |
| **AuthZEN Authorization API 1.0** ([openid.net](https://openid.net/specs/authorization-api-1_0.html), **Final, 11 Jan 2026**) | Final | The PDP↔PEP interop binding: `POST /access/v1/evaluation` with `subject`/`action`/`resource`/`context` → `decision` + `context` (step-up `acr_values`, reasons); search endpoints (which subjects/resources/actions are permitted) |
| **OPA / Rego** ([openpolicyagent.org](https://www.openpolicyagent.org/)) | CNCF graduated | A **peer backend**: an org's existing Rego policy evaluates with the same decision contract (import, not replace) |
| **OpenFGA** (ReBAC) | CNCF | Relationship-based agent→tool→resource modeling consumed as context where an org uses it |

> **Conformance:** agentpolicy's HTTP surface is **AuthZEN-conformant** — the same `subject/action/resource/context`
> → `decision` shape, with a `context` that can carry the reason, the matched rule, and a step-up request
> (`acr_values`). A conformant AuthZEN PEP can point at agentpolicy; agentpolicy can be swapped for another
> conformant PDP and the ecosystem keeps working (R27).

## B. Identity & authorization-adjacent standards (agentpolicy consumes these)

| Standard | Status | Use |
|---|---|---|
| **OAuth 2.1** + **RFC 9700** (Security BCP) | Published | The agent's authorization context; PKCE, exact redirects |
| **RFC 8693** (Token Exchange) | Published | Downscoped, tool-scoped tokens — expiry *is* revocation (issued by agentkeys) |
| **RFC 8707** (Resource Indicators) | Published | Audience binding — kills confused-deputy token replay (enforced at agentgate) |
| **RFC 9728** (Protected Resource Metadata) | Published (MUST in MCP) | Authz-endpoint discovery |
| **MCP Authorization chapter** | Latest 2026 | The wire standard for tool access; agentpolicy decides per `tools/call` behind agentgate |
| **SPIFFE/SPIRE** | CNCF graduated | Workload identity for agent principals (consumed, not issued) |

## C. Telemetry & event standards

| Standard | Use |
|---|---|
| **OpenTelemetry GenAI semantic conventions** | The telemetry substrate; agentpolicy's decisions ride the agentwatch event stream |
| **agentwatch security-event schema v1** | agentpolicy's machine-readable decision surface (R6) — the ecosystem's single event vocabulary |
| **OCSF** | SIEM interop for the event stream (via agentwatch) |

## D. AI security & governance frameworks (agentpolicy aligns to — and publishes coverage for)

| Framework | Status | Agentpolicy alignment |
|---|---|---|
| **OWASP Top 10 for Agentic Applications 2026 (ASI)** ([genai.owasp.org](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/)) | Published | Primary mapping. **ASI02** Tool Misuse, **ASI03** Identity & Privilege Abuse, **ASI05** Unexpected Code Execution, **ASI09** Human-Agent Trust Exploitation, **ASI10** Rogue Agents — the policy layer is the direct control. Full mapping: [docs/compliance/owasp-llm-agentic.md](../compliance/owasp-llm-agentic.md) |
| **OWASP Top 10 for LLM Applications 2025** | Published | **LLM01** prompt injection (mitigation by architecture, not detection claims), **LLM02** sensitive-info disclosure (redaction + egress), **LLM06** excessive agency (gates + budgets) |
| **MITRE ATLAS** ([atlas.mitre.org](https://atlas.mitre.org/)) | Active | Every rule pack tagged to ATLAS techniques; mapping in [docs/compliance/atlas-mapping.md](../compliance/atlas-mapping.md) |
| **NIST AI RMF 1.0 (AI 100-1) + Generative AI Profile (AI 600-1)** | Published | Governance overlay — the **Manage**/**Measure** functions; mapping in [docs/compliance/nist-ai-rmf.md](../compliance/nist-ai-rmf.md) |
| **ISO/IEC 42001** (AI management systems) | Published | Controls-mapping appendix for enterprise buyers — [docs/compliance/iso-42001.md](../compliance/iso-42001.md) |
| **EU AI Act** (Art. 9 risk, Art. 12 logging, Art. 14 human oversight) | In force | The audit log + human gate map directly to logging & oversight obligations — [docs/compliance/eu-ai-act.md](../compliance/eu-ai-act.md) |
| **CSA Agentic AI / NHI guidance** | Early | Contribute; distribution to security buyers |

## E. Product security & supply chain (agentpolicy's *own* posture)

| Standard | Use |
|---|---|
| **NIST SSDF (SP 800-218)** | Secure development practices for agentpolicy itself |
| **OWASP ASVS L2** | Target for agentpolicy's own application security |
| **OpenSSF Scorecard / Best Practices badge** | Signed releases (Sigstore), provenance (SLSA), pinned deps — [docs/compliance/openssf-badge.md](../compliance/openssf-badge.md) |
| **SLSA** (build provenance) | Provenance attestation on released artifacts |
| **Sigstore** | Keyless signing of packs, releases, and attestations |
| **SPDX / CycloneDX SBOM** | Software bill of materials per release |
| **CVE / coordinated disclosure** | `security.txt`, a disclosure process with SLAs (a security product without one is DOA) |
| **CIS Benchmarks / hardened manifests** | Hardened deployment posture where a service mode is used |

## F. The certification ladder (ordered by cost/timeline)

A credible security product follows this sequence — agentpolicy targets the early rungs in v0.1.0 and tracks the
later ones:

| Rung | Target | When | Evidence |
|---|---|---|---|
| **OpenSSF Best Practices badge** | Passing → Silver | v0.1.0 | Badge + `docs/compliance/openssf-badge.md` |
| **SLSA build provenance + Sigstore signing** | L2→L3 | v0.1.0 | Attestations on every release |
| **CVE program + `security.txt` + disclosure SLAs** | Live | v0.1.0 | Public URL |
| **AuthZEN conformance** | Passing | v0.1.0 | Conformance report |
| **Published OWASP ASI/LLM + ATLAS coverage matrix** | Published | v0.1.0 | Regenerated per release |
| **SOC 2 Type I → Type II** | Audited | v1.x | Audit letter (Type II needs 6–12 months of evidence — start the pipeline now) |
| **ISO/IEC 27001** | Certified | v1.x | Certificate |
| **ISO/IEC 42001** (AI management) | Certified | later | Certificate |
| **CIS hardened artifacts** | Published | v1.x | Helm/manifests |
| **FIPS-mode / Common Criteria** | only if government buyers | later | (OS-native crypto mode, not a module cert) |

## G. Claims vocabulary (the honesty rule)

agentpolicy may claim only what it can prove. The following are **forbidden** or **restricted**:

| Claim | Status |
|---|---|
| "Blocks all prompt injection" | **Forbidden** — injection is unsolved; agentpolicy is architectural, not detection |
| "Detects malicious agents" | **Forbidden** — agentpolicy is deterministic policy, not a classifier |
| "SOC 2 / ISO certified" | **Only** with the audit letter in hand |
| "AuthZEN-conformant" | **Allowed** with the conformance report |
| "Blocks the Replit incident pattern" | **Allowed** only with the agentdrill replay in CI |
| "Sub-100 ms p99" | **Allowed** only with the CI measurement published |
| "OWASP ASI02/ASI03 covered" | **Allowed** with the published coverage matrix |

A machine-readable **claims linter** checks published docs/marketing against this vocabulary in CI (the
agentdrill `claims-ledger` pattern).

## H. Coverage matrix (published per release)

Every rule pack and control carries machine-readable tags; the matrix is **generated from the packs**, not
hand-edited:

| Rule pack | OWASP ASI | OWASP LLM | MITRE ATLAS | NIST AI RMF |
|---|---|---|---|---|
| destructive-commands (Replit rule) | ASI02, ASI05 | LLM06 | AML.T0049 (destructive) | MANAGE-1.3, MANAGE-2.2 |
| secret-in-output | ASI02 | LLM02, LLM05 | AML.T0057 (exfil) | MANAGE-2.1 |
| mcp-allowlist | ASI04 | LLM03 | AML.T0010 (supply chain) | MAP-4.1, MANAGE-2.2 |
| exfil-sink | ASI02 | LLM02 | AML.T0057 | MANAGE-2.1 |
| scope-escalation | ASI03 | LLM06 | AML.T0055 (priv. esc.) | MANAGE-2.2 |
| rate-budget | ASI02, ASI10 | LLM06 | AML.T0049 | MANAGE-2.2 |
| code-freeze (R33) | ASI02, ASI10 | LLM06 | AML.T0049 | EU AI Act Art. 14 (intensified oversight) |
| secrets-in-args (R38) | ASI02 | LLM02, LLM05 | AML.T0057 | MANAGE-2.1 |
| enrollment-probation (R35) | ASI03, ASI10 | LLM06 | AML.T0043 (discovery) | MAP-4.1 |
| multi-agent-delegation (R39) | ASI03, ASI07, ASI08 | LLM06 | AML.T0055 | MANAGE-2.2 |
| dual-control / break-glass (R40/R41) | ASI09 | — | — | EU AI Act Art. 14 |

> The full per-control mapping lives in [`docs/compliance/`](../compliance/). The matrix is part of every
> release artifact and is regenerated by CI.
