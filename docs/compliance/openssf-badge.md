# OpenSSF, SLSA & Supply-Chain Posture

agentpolicy is a **security product**, so its own supply chain must be demonstrably clean — especially because
the 2026 **Plugin4Shell** class of incidents was a *supply-chain attack on coding agents*. This document tracks
agentpolicy's own security posture (distinct from the controls it ships).

> Sources: [OpenSSF Best Practices](https://www.bestpractices.dev/) · [OpenSSF Scorecard](https://scorecard.dev/) ·
> [SLSA](https://slsa.dev/) · [Sigstore](https://www.sigstore.dev/) · [NIST SSDF SP 800-218](https://csrc.nist.gov/pubs/sp/800/218/final)

## Targets

| Baseline | Target | Notes |
|---|---|---|
| **OpenSSF Best Practices badge** | Passing → **Silver** | Basic OSS hygiene; Silver adds dynamic analysis, branch protection, signed releases |
| **OpenSSF Scorecard** | ≥ A grade | Branch protection, pinned deps, code review, SAST, fuzzing |
| **SLSA** | L2 → **L3** | Build provenance attestations on every release |
| **Sigstore** | keyless signing | Packs, releases, and attestations signed; verifiable |
| **SPDX / CycloneDX SBOM** | per release | Machine-readable bill of materials |
| **NIST SSDF (SP 800-218)** | aligned | Secure development practices (PO/PS/PW/RV practices) |
| **OWASP ASVS L2** | target | agentpolicy's own application security |
| **CVE / coordinated disclosure** | live | `security.txt` + a disclosure process with SLAs |

## Checklist (targeted v0.1.0)

| Item | Requirement | Status |
|---|---|---|
| Branch protection on `main` | PR review required; no direct push | ☐ |
| Signed releases | Sigstore / PyPI trusted publishing | ☐ |
| SLSA provenance | build attestation attached to the release | ☐ |
| Pinned dependencies | lockfile verified in CI | ☐ |
| Fuzzed inputs | `hypothesis` property tests over the evaluate() input space + the policy parser | ☐ |
| `security.txt` + disclosure SLA | public URL; 48h ack / 90d fix | ☐ |
| SAST + dependency scanning | CodeQL + `pip-audit` in CI | ☐ |
| SBOM | SPDX/CycloneDX per release | ☐ |
| Reproducible build | `uv` lockfile; CI verifies hash match | ☐ |

## Why it matters for the product

- A **control plane** that ships unsigned artifacts is a supply-chain risk to every caller — the Plugin4Shell
  lesson applied to ourselves.
- Signed **rule packs** let a consumer verify a pack is the reviewed one (not tampered) before it governs their
  agents.
- The **audit chain** (hash-chained decisions) is only trustworthy if the *engine* that produced it is verifiably
  built — hence provenance on the binary/package.

## Relationship to the shipped controls

This file is agentpolicy's **own** posture (OpenSSF/SLSA/Sigstore). The controls agentpolicy *ships* (the rule
packs, the decision model) are mapped in [owasp-llm-agentic.md](owasp-llm-agentic.md),
[atlas-mapping.md](atlas-mapping.md), and the other files in this folder.
