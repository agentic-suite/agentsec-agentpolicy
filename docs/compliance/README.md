# agentpolicy — Compliance & Certification

This folder is agentpolicy's **claim surface**: the standards it implements, the frameworks it aligns to, and the
certifications it targets — each with an explicit, checkable mapping. Everything here is **generated from the
rule packs and controls**, not hand-waved; the coverage matrix is regenerated per release.

> **Honesty rule:** agentpolicy claims only what it can prove (see [PRD 20](../prd/20-standards-and-claims.md)
> §G). No "blocks all prompt injection", no "detects malicious agents", no "certified" without the audit letter.

## Documents

| Document | Covers |
|---|---|
| [authorization-standards.md](authorization-standards.md) | Cedar, XACML, **NIST SP 800-162 (ABAC)**, ISO/IEC 29146, **AuthZEN Authorization API 1.0**, OPA/Rego, OpenFGA — the PDP standards agentpolicy implements |
| [owasp-llm-agentic.md](owasp-llm-agentic.md) | **OWASP Top 10 for Agentic Applications 2026 (ASI01–ASI10)** + OWASP LLM Top-10 2025 |
| [atlas-mapping.md](atlas-mapping.md) | **MITRE ATLAS** technique mapping per rule pack |
| [nist-ai-rmf.md](nist-ai-rmf.md) | **NIST AI RMF 1.0 (AI 100-1)** + Generative AI Profile (AI 600-1) |
| [iso-42001.md](iso-42001.md) | **ISO/IEC 42001** AI-management controls mapping |
| [eu-ai-act.md](eu-ai-act.md) | **EU AI Act** — Art. 9 (risk), Art. 12 (logging), Art. 14 (human oversight) |
| [openssf-badge.md](openssf-badge.md) | **OpenSSF** Scorecard / Best Practices, **SLSA** provenance, **Sigstore**, **NIST SSDF** — agentpolicy's own posture |

## Certification ladder (status)

| Rung | Target | Status |
|---|---|---|
| OpenSSF Best Practices badge | Passing → Silver | ☐ targeted v0.1.0 |
| SLSA provenance + Sigstore signing | L2→L3 | ☐ targeted v0.1.0 |
| CVE program + `security.txt` + disclosure SLAs | live | ☐ targeted v0.1.0 |
| **AuthZEN Authorization API 1.0** conformance | passing | ☐ targeted v0.1.0 |
| Published OWASP ASI/LLM + ATLAS coverage matrix | published | ☐ targeted v0.1.0 |
| SOC 2 Type I → Type II | audited | ☐ v1.x |
| ISO/IEC 27001 | certified | ☐ v1.x |
| ISO/IEC 42001 | certified | ☐ later |
| CIS hardened artifacts | published | ☐ v1.x |
| FIPS-mode / Common Criteria | gov buyers only | ☐ later |

> **Status legend:** ☐ not started · ◐ in progress · ☑ achieved. This table is the single status source; it is
> updated with each release.
