# NIST AI RMF Mapping

agentpolicy maps to the **NIST AI Risk Management Framework 1.0 (NIST AI 100-1)** and its **Generative AI
Profile (NIST AI 600-1)** as the governance overlay enterprise buyers use. The AI RMF's four functions —
**Govern, Map, Measure, Manage** — each get a concrete agentpolicy contribution.

> Sources: [NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework) · [NIST AI 600-1](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf)

## Function mapping

| Function | agentpolicy contribution | Evidence |
|---|---|---|
| **GOVERN** | Policy-as-code reviewed like code (two-party review); a documented decision process; a claims vocabulary that forbids over-claiming | git policy repo; [PRD 20](../prd/20-standards-and-claims.md) §G |
| **MAP** | The canonical action taxonomy + contextual dimensions make the agent's action space explicit and bounded | [PRD 16](../prd/16-rule-packs.md) taxonomy |
| **MEASURE** | Deterministic decisions + a hash-chained audit log; shadow mode + calibration report (false-block/miss rates) | [PRD 17](../prd/17-explain-decision-and-evidence.md); R30 |
| **MANAGE** | The five outcomes (allow/deny/ask/rate-limit/redact) + blast-radius budgets actively bound risk; fail-closed everywhere | [PRD 18](../prd/18-blast-radius-budgets.md); R8 |

## Generative AI Profile (AI 600-1) risks agentpolicy addresses

| GAI risk (AI 600-1) | agentpolicy control |
|---|---|
| **Data Privacy** | The `redact` outcome + the secret-in-output pack (LLM02) |
| **Information Integrity** | Policy is not in the prompt; decisions are deterministic and reviewable |
| **Information Security** | The five-outcome decision + budgets + the audit chain |
| **Human-AI Configuration** | The mandatory human-gate class + the explain contract (LLM06 / ASI09) |
| **Value Chain / Component Integration** | The MCP-allowlist pack + tool-trust consumption |

## Control-to-requirement traceability

| AI RMF action (representative) | agentpolicy requirement |
|---|---|
| MANAGE-1.3 — risk treatments are documented and applied | R1, R3 (packs with incident anchors) |
| MANAGE-2.2 — mechanisms to supersede/override are in place | R4 (human-gate class), R18 (ask round-trip) |
| MEASURE-2.x — risks are measured and tracked | R30 (shadow/calibration), R32 (evidence export) |
| GOVERN-1.x — policies and procedures are defined | R7 (git-reviewed policy), [PRD 11](../prd/11-decisions.md) |

## Note on the honesty rule

The AI RMF is a **governance overlay**, not a certification. agentpolicy **aligns** to it (a controls mapping for
enterprise buyers); it does not claim AI RMF "certification" (there is none). See
[PRD 20](../prd/20-standards-and-claims.md) §G.
