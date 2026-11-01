# AgentPolicy v0.1.0 - Compliance & Standards Matrix

> **Computed**, not asserted: every row is derived from the shipped rule packs'
> policy domains by `agentpolicy compliance export` (schema
> `agentcomply.coverage.v1`). The published claims are linted against this
> matrix by `agentpolicy compliance claims` (a CI gate). M25 25.4 (issue #271).

**Covered policy domains:** `approval`, `cloud`, `db`, `email`, `fs`, `git`, `http`, `iam`, `mcp`, `notify`, `payment`, `secrets`, `shell`.

**Explicit gaps (uncovered controls):** none - every mapped control's domains
are covered by the shipped packs. Regimes deliberately **out of scope for
v0.1.0** are named in section "Out of scope" below (never silently dropped).

## At a glance

| Framework | Covered |
|---|---|
| OWASP Agentic Security (ASI) (`OWASP-ASI`) | 5/5 |
| OWASP LLM Top 10 (`OWASP-LLM`) | 4/4 |
| MITRE ATLAS (`ATLAS`) | 3/3 |
| NIST AI RMF (`NIST-AI-RMF`) | 4/4 |
| ISO/IEC 42001 (`ISO-42001`) | 4/4 |
| EU AI Act (high-risk) (`EU-AI-Act`) | 4/4 |

## OWASP Agentic Security (ASI) (`OWASP-ASI`)

| Control | Title | Domains | Covered |
|---|---|---|---|
| `ASI01` | Agent goal hijack | shell, http, mcp | yes |
| `ASI02` | Tool misuse | db, shell, cloud, git | yes |
| `ASI03` | Privilege compromise | cloud, secrets | yes |
| `ASI04` | Supply-chain tampering | mcp, git | yes |
| `ASI05` | Unexpected code execution | shell, db | yes |

## OWASP LLM Top 10 (`OWASP-LLM`)

| Control | Title | Domains | Covered |
|---|---|---|---|
| `LLM01` | Prompt injection | http, secrets | yes |
| `LLM02` | Insecure output handling | secrets, db | yes |
| `LLM06` | Sensitive information disclosure | secrets, db | yes |
| `LLM07` | Insecure plugin design | mcp | yes |

## MITRE ATLAS (`ATLAS`)

| Control | Title | Domains | Covered |
|---|---|---|---|
| `AML.T0051` | LLM prompt injection | http, secrets | yes |
| `AML.T0054` | LLM jailbreak | shell, mcp | yes |
| `AML.T0012` | Exfiltration via tool | secrets, http, db | yes |

## NIST AI RMF (`NIST-AI-RMF`)

| Control | Title | Domains | Covered |
|---|---|---|---|
| `GOVERN 1.1` | Policies/accountability defined | git, approval | yes |
| `MAP 1.5` | Impacts characterized | db, http | yes |
| `MEASURE 2.7` | Security & resilience evaluated | secrets, shell | yes |
| `MANAGE 2.4` | Residual risk managed | cloud | yes |

## ISO/IEC 42001 (`ISO-42001`)

| Control | Title | Domains | Covered |
|---|---|---|---|
| `A.6.2.6` | AI system security | secrets, shell | yes |
| `A.7.4` | Data management | db | yes |
| `A.9.2` | Monitoring & logging | http, notify | yes |
| `A.10.3` | Third-party & supply chain | mcp, git | yes |

## EU AI Act (high-risk) (`EU-AI-Act`)

| Control | Title | Domains | Covered |
|---|---|---|---|
| `Art.9` | Risk management system | cloud, db | yes |
| `Art.12` | Record-keeping / logging | git, notify | yes |
| `Art.14` | Human oversight | approval | yes |
| `Art.15` | Accuracy, robustness, cybersecurity | secrets, shell | yes |

## How coverage is computed

For each control a **domain set** is declared (e.g. *Exfiltration via tool* ->
secrets, http, db). The control is **covered** when the union of the shipped
packs' domains intersects that set. The matrix carries a **gaps** list of every
uncovered control - a control is *named*, never hidden. The canonical framework
ids are OWASP-ASI, OWASP-LLM, ATLAS, NIST-AI-RMF, ISO-42001 and EU-AI-Act.

## Out of scope (named, not claimed)

- Domains not shipped in v0.1.0 (e.g. browser automation, mobile) - a control
  mapping only to those appears in `gaps`.
- Full certification audits (ISO 42001 certification, SOC 2) - this matrix maps
  *technical controls* to regimes; it is not an audit opinion.
- Regimes beyond the six above - a new framework is added as a code change to
  `agentpolicy/compliance.py` CONTROLS plus a doc, never a hand-edited number.

## Reproduction

```sh
agentpolicy compliance export          # the full computed matrix (JSON)
agentpolicy compliance claims          # lint published claims against it
```
