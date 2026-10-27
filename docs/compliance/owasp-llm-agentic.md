# OWASP Coverage — Agentic Top 10 (2026) & LLM Top 10 (2025)

agentpolicy is the **policy layer** control. This maps the OWASP frameworks to agentpolicy's controls. The
matrix is **generated from the shipped rule packs**, not hand-edited.

> Sources: [OWASP Top 10 for Agentic Applications 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/) ·
> [OWASP LLM Top-10 2025](https://genai.owasp.org/llm-top-10/)

## OWASP Top 10 for Agentic Applications 2026 (ASI01–ASI10)

| # | Risk | agentpolicy control | Coverage |
|---|---|---|---|
| **ASI01** | Agent Goal Hijack | Policy evaluated **outside** the model — a hijacked goal still hits the same deterministic rule; no prompt can widen scope | ◐ (architectural; not detection) |
| **ASI02** | Tool Misuse & Exploitation | The five-outcome decision on every call; the 13-domain taxonomy; **rate/burst limits**; **blast-radius budgets** (tool-budget exhaustion) | ✅ |
| **ASI03** | Agent Identity & Privilege Abuse | `principal`/`agent_class` dimensions; child-delegation scope ⊆ parent; step-up on scope escalation | ✅ |
| **ASI04** | Agentic Supply Chain Compromise | The **MCP-allowlist** pack (default-deny unknown servers); consumes agentgate's tool-scan verdict | ◐ (policy side) |
| **ASI05** | Unexpected Code Execution | The **destructive-commands (Replit) rule** — shell/db/cloud destructive verbs gated or denied; argument-level validation | ✅ |
| **ASI06** | Memory & Context Poisoning | Session/consent state is policy input; poisoned context cannot widen a rule (deny is default) | ◐ |
| **ASI07** | Insecure Inter-Agent Communication | `delegation_chain` in the principal; child-scope subset rule; **inter-agent requests decided like any action (R39)** | ◐ → strengthened in v0.3.0 |
| **ASI08** | Cascading Agent Failures | Budgets + rate limits bound propagation; exhaustion halts; **delegation-scope proofs bound blast radius across agents (R39)** | ◐ (v0.1.x, deepened v0.3.0) |
| **ASI09** | Human-Agent Trust Exploitation | The **mandatory human-gate class** + the explain-decision contract (no black-box denials); **approval analytics catch rubber-stamp gates (R36)**; dual-control for the irreversible class (R41) | ✅ (+ v0.2.0/v0.3.0 depth) |
| **ASI10** | Rogue Agents | Cumulative budgets + rate limits bound "runaway autonomy"; every action logged; **first-seen agents run in probation until classified (R35); declared freezes tighten posture (R33)** | ✅ (+ v0.2.0 depth) |

**v0.1.0 coverage: ASI02, ASI03, ASI05, ASI09, ASI10 full; ASI01/04/06/07/08 partial (by design — agentpolicy is
the policy layer, not the whole stack).**

## OWASP LLM Top-10 2025

| # | Risk | agentpolicy control | Coverage |
|---|---|---|---|
| **LLM01** | Prompt Injection | Mitigation **by architecture**, not detection — the action is decided outside the model (no detection claim) | ◐ |
| **LLM02** | Sensitive Information Disclosure | The **secret-in-output** pack (`redact`/`deny`) + the **exfil-sink** rule class; redaction receipts | ✅ |
| **LLM03** | Supply Chain | The **MCP-allowlist** pack; tool-trust consumes agentgate | ◐ |
| **LLM05** | Improper Output Handling | `redact` scrubs secrets/PII from tool output before it reaches the model | ✅ |
| **LLM06** | Excessive Agency | The **human-gate class** + **budgets** + rate limits — the direct control | ✅ |
| **LLM07** | System Prompt Leakage | Policy is not in the prompt; a leaked prompt cannot widen scope | ✅ (by construction) |
| **LLM10** | Unbounded Consumption | Blast-radius budgets (spend/requests/calls) | ✅ |

## The honesty rule

- agentpolicy **does not claim** to detect or solve prompt injection (LLM01/ASI01). It claims to make the
  **action** deterministic and reviewable.
- "Covered" means a **shipped rule pack + an agentdrill replay** — not a slide.
- Partial (◐) coverage names the gap and the owning tool (agentgate for scanning, agentwatch for memory
  integrity, agentcomply for evidence).
