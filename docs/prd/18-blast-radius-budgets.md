# PRD 18 — Blast-Radius Budgets

**BLUF:** A **blast-radius budget** is a cumulative, per-session capability ceiling — *"10 files modified, 20
external requests, $5 spent, 200 tool calls, then stop."* Exhaustion returns `rate-limit` (soft) or triggers a
halt (hard, via agenthalt). It is the novel class nobody else ships: enforcement of *how much*, not just *what*,
computed over the session rather than per call.

**Status:** Draft — v0.1.0 (2026-10-26) · **Owner:** @deghosal-2026 · **Parent:** agentic-suite #209 · PRD #211

## Why budgets (the gap)

- Flat allow-lists and per-call rules decide *what* an agent may do, never *how much*. A single allowed tool can
  be called a thousand times — the Replit agent's destructive act was one call, but many incidents are a
  **volume** problem: a runaway loop, a slow exfiltration of one record at a time, a spend blowout.
- Rate limits (LiteLLM) exist for *model* traffic; nothing bounds *agent capability* cumulatively across tools
  and sessions. This is whitespace (coverage-map rows #6 and the "nobody unifies" gap).
- The OWASP Agentic Top-10 calls it out directly: **ASI02** (Tool Misuse — "tool budget exhaustion") and
  **ASI10** (Rogue Agents — "runaway autonomy"). A budget is the control.

## The model

A budget is a **versioned policy object** (reviewable in git), evaluated against the session state:

```cedar
@id("session-capability-budget")
@reason_code("budget_exhausted")
permit (principal, action, resource)
when {
  context.session.files_modified   < 10 &&
  context.session.external_requests < 20 &&
  context.session.spend_usd         < 5 &&
  context.session.tool_calls        < 200
};
```

| Dimension | Example ceiling | Counts |
|---|---|---|
| Files modified | 10 | distinct file writes/deletes |
| External requests | 20 | outbound sends/fetches to non-allowlisted hosts |
| Spend | $5 | cumulative model/tool cost attributed to the session |
| Tool calls | 200 | total tool invocations |
| Custom | org-defined | any counter the policy names |

## Semantics

- **Cumulative, per session** — counters accumulate over the session, not per call. Splitting one action into
  many small ones does not evade the ceiling (closes RK-12).
- **Soft vs hard** — exhaustion returns `rate-limit` (the agent can replan) or, for a hard ceiling, requests a
  **halt** via agenthalt (freeze the run + preserve evidence).
- **Visible in every decision** — the `budget_state` (remaining per dimension) is part of the decision context,
  so the agent (and the operator) can see the budget before hitting it.
- **Consent-scoped** — budgets interact with consent scope ([PRD 16](16-rule-packs.md) scope-escalation): a
  budget may be granted per consented scope, and reset only when the scope is re-granted.
- **Reset policy** — explicit and versioned: a new session resets; a subagent **inherits** the parent's
  remaining budget by default (open question — see below).

## Lifecycle

1. A session starts; the budget policy is loaded (versioned, git-reviewed).
2. Each decision reads the session state, decrements on allow, and returns `budget_state`.
3. On exhaustion → `rate-limit` (soft) or halt trigger (hard), with `reason_code=budget_exhausted`.
4. The session state is replayable (`session_id`) for review (CUJ-6, CUJ-12).

## Integration

| Tool | Role |
|---|---|
| **agenthalt** | receives the hard-exhaustion trigger → freezes the run + snapshots evidence |
| **agentwatch** | stores the budget events (exhaustion, near-miss) |
| **agentkeys** | a spend/request budget can gate credential issuance |
| **agentdiff** | shadow mode shows what *would have* exhausted (tune before enforce) |

## Open questions (see [PRD 08](08-risks.md))

- **Budget semantics across sessions/subagents** — reset? inherit? cap? (needs design-partner input)
- **Default ceilings** — what ships as the `balanced` posture default? (hypothesis: conservative; validate)
- **Counting model** — who counts files/requests — the PDP from the action stream, or the enforcer? (PDP, for
  one source of truth)
- **Attribution** — how is spend attributed to a session across subagents and shared tools?

## Status

Blast-radius budgets are a **v0.1.x commitment** (R9), gated on session state (R17) landing first. The concept
is the product's sharpest differentiator — no competitor ships it — so it is documented here in full even though
it is not in the v0.1.0 critical path.
