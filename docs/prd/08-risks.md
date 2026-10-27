# PRD 08 — Risks

**BLUF:** agentpolicy's credibility *is* the product, so its top risks are the ones that would make a decision
wrong or unusable: **fail-open** (a decision path that silently allows), **policy drift** (a rule edit that
un-blocks an attack), **explanation theater** (denials nobody can act on), and **over-permissive defaults**
(false positives that drive users to bypass). Second tier: policy sprawl, latency, harness/config churn, and
scope creep into enforcement. Each has a trigger and a mitigation.

**Status:** Draft — v0.1.0 (2026-10-26) · **Owner:** @deghosal-2026 · **Parent:** agentic-suite #209 · PRD #211

## Risk register

| # | Risk | Likelihood | Impact | Trigger | Mitigation |
|---|---|---|---|---|---|
| **RK-1** | **Fail-open** — some path silently allows | Medium | High | A new code path returns `allow` on error | Fail-closed contract is a CI test; every failure has a distinct `reason_code` (CUJ-9); fuzz the input space |
| **RK-2** | **Policy drift** — a rule edit un-blocks a known attack | High | High | A policy PR relaxes a rule | Golden decision fixtures + agentdrill incident replays gate every PR (R22); change without review is flagged (R7) |
| **RK-3** | **Over-permissive defaults** → false positives/negatives | High | High | A posture preset is wrong for an org | Posture presets + `init` scaffold; shadow mode before enforce (R30); calibration report; `diff` shows gaps |
| **RK-4** | **Explanation theater** — denials nobody can act on | Medium | High | A deny has no actionable "what to change" | Actionability test in CI (R5); explain artifact is the unit of review |
| **RK-5** | **Latency blowout** — the PDP slows the agent loop | Medium | Medium | Complex policy or a cold start | Sub-100 ms p99 budget (R8); local-first; no network in the hot path; budget in CI |
| **RK-6** | **Policy sprawl** — unreadable, conflicting rules | Medium | Medium | Rules accumulate without review | Rule-pack structure; lint (unused/shadowed/over-permissive, R12); `diff`/report |
| **RK-7** | **Harness/config churn** — targets move under us | Medium | Medium | Claude Code/Cursor/MCP config surfaces change | Harness-agnostic by construction; policyweave drift alerts; harness watchlist |
| **RK-8** | **Scope creep into enforcement** | Medium | Medium | A PR adds enforcement "to make the decision stick" | Architecture rule: agentpolicy owns no enforcement (PRD 02); non-goals (PRD 14) |
| **RK-9** | **Ask fatigue** — asking for everything defeats the product | Medium | High | Too many `ask` classes | `ask` reserved for irreversible classes (R4); budget/rate-limit absorb the rest; measure useful gates |
| **RK-10** | **Untrusted rule packs** execute malicious code | Low | High | A community pack is hostile | Trust levels + schema validation + sandbox + audit (PRD 06) |
| **RK-11** | **Ask replay / confused deputy** — a stale approval authorizes a new action | Medium | High | An approval token is reused | Action-identity binding + expiry + timeout=deny (R18); delegation scope subset (R25) |
| **RK-12** | **Budget evasion** — split actions to slip past a ceiling | Medium | Medium | An agent breaks one big action into many small ones | Cumulative counters on the session, not per call (R9); burst limits (R23) |
| **RK-13** | **Normalization gap** — the enforcer and the PDP disagree on what the action is | Medium | High | Dispatcher smuggling / Unicode / case variants | One canonical action shape for both; adversarial normalization suite (CUJ-11) |
| **RK-14** | **Audit tamper** — a decision log is edited | Low | High | An operator "fixes" the log | Hash chain + verification command (F17); policy hash in every decision |
| **RK-15** | **Standards drift** — Cedar/AuthZEN/OWASP move under us | Medium | Medium | A spec version changes | Pin versions; a standards watchlist; coverage matrix regenerated per release ([PRD 20](20-standards-and-claims.md)) |
| **RK-16** | **Ecosystem divergence** — an enforcer re-implements policy | Medium | High | A tool ships its own YAML rules | agentpolicy is the single source of authorization truth; enforcers call it (PRD 02); agentdrill gates compliance |
| **RK-17** | **Break-glass becomes the default path** — permanent elevation by habit | Medium | Medium | Teams live in an elevated window | Requires a logged reason; short default TTL; approval analytics flags heavy break-glass users (R40, [PRD 22](22-policy-intelligence-and-governance.md)) |
| **RK-18** | **An NL draft is plausible but wrong** — passes tests, over-permissive in the field | Medium | High | A drafted rule misses a context | Drafts are advisory + human-reviewed + linted + agentdrill-replayed; never auto-pinned (R42) |
| **RK-19** | **`permitted_alternatives[]` leaks policy shape** to a hostile agent | Medium | Medium | Alternatives reveal rule internals | Curated templates only; alternatives are evaluated-true; the agent/operator split is tested (R37) |
| **RK-20** | **The enrollment ledger becomes a shadow IdP** | Low | Medium | agentpolicy starts issuing identity | It classifies; it never issues identity (IdP/SPIFFE stays the issuer) (R35) |
| **RK-21** | **Backtest false confidence** — "the diff was empty, ship it" on a thin window | Medium | Medium | A policy PR merges on an empty backtest over 1 day of history | Coverage % + window stated on every report; backtest is advisory, never auto-merge; the golden gate (R22) remains the hard gate ([PRD 23](23-enterprise-adoption-and-governance-hardening.md)) |
| **RK-22** | **Layering complexity** — three layers + packs + consent becomes unreadable | Medium | Medium | Overlay stacks conflict and teams fork their policies | The narrow-only invariant is one rule enforced at load; the coverage report (R45) and lint (R12) are the readability guardrails |
| **RK-23** | **Self-attack pack rots** — stops tracking the real decision surface | Medium | High | A new feature (R33–R47) ships without a self-attack case | Every new decision-surface feature must add or update a self-attack case; the pack's own coverage is reported (R45 discipline) |

## Hard parts

1. **Choosing the right conservative defaults.** Too strict → false positives → bypass; too loose → dangerous.
   Solved with posture presets + shadow mode + calibration, not with cleverness.
2. **Expressiveness without a policy maze.** Cedar is analyzable, but a bad policy set is still a maze; the lint
   and the `diff` report are the guardrails.
3. **Explaining a decision in one paragraph.** The explanation is the adoption surface — hard to get right, easy
   to fake.
4. **Determinism across a live stack.** Session state, budgets, and time make the same call behave differently;
   the session model must be explicit and replayable.
5. **Staying the single source of truth.** The temptation for every enforcer to "just add one rule" is the
   ecosystem's biggest structural risk.

## Triggers to revisit

- A fail-open path is found → RK-1 escalation to a release-blocking bug.
- A published rule pack misses its incident replay → RK-2 review.
- A posture preset causes a false-positive storm in a design-partner → RK-3 calibration cycle.
- A harness changes its config surface → RK-7 watchlist update + policyweave drift alert.
- A Cedar/AuthZEN/OWASP version lands → RK-15 standards review.

## Open questions

- **Budget semantics across sessions/subagents** — reset? inherit? cap? Needs design-partner input.
- **Ask-gate UX contract** — who answers, in what window, what happens on timeout (deny is the safe default —
  confirm with design partners).
- **Default posture for first run** — `balanced` is the hypothesis; validate against real workloads.
- **How much of the taxonomy ships in v0.1.0** — the full 13-domain set, or a smaller curated core?
- **Child-agent delegation** — how deep does scope inheritance go before it is unmanageable?
