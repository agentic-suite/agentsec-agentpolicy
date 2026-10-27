# PRD 07 — Success Metrics

**BLUF:** agentpolicy succeeds when a **non-security engineer writes a first useful policy in an afternoon**,
when **every deny is explainable and actionable**, and when **a policy PR that un-blocks a known attack is
rejected by CI**. The headline metric is not a "detection rate" — it is **determinism**, **explainability**,
and **adoption of the shadow→enforce funnel**: the decision must be provable and the fix must be obvious.

**Status:** Draft — v0.1.0 (2026-10-26) · **Owner:** @deghosal-2026 · **Parent:** agentic-suite #209 · PRD #211

## Outcome metrics

| Metric | Target | Why it is the right metric |
|---|---|---|
| Time to first correct decision | **< 5 min** from `pip install` (**< 2 min** with `init`) | Adoption friction is the gating concern (R2) |
| Acceptance-matrix correctness | **100%** on tool × env × action × data-class | Deterministic product — no "usually right" |
| Deny explainability | **100%** of denies traceable to a clause + context; actionable-reason test in CI | Black-box denials get bypassed (R5) |
| Decision latency | **p99 < 100 ms** inline; p50/p95 published | The inline budget is a product requirement (R8) |
| Fail-closed coverage | **0** failure modes that silently allow | The safety spine (CUJ-9) |
| Shadow→enforce conversion | % of monitor-mode users who flip after a "would-have-blocked" report | The conviction funnel (with agentdiff) |
| Rule packs block their incident | **zero false positives** per named replay in CI | Shipped rules must stop the incidents that happened (R3) |
| Policy-PR gate | a golden deny→allow flip fails the build deterministically | The CI gate is the regression moat (R22) |
| Ecosystem adoption | every Wave-0 enforcer calls agentpolicy (no bespoke policy) | The brain thesis — one source of truth |
| Community packs contributed | grow per release | Ecosystem health (R29) |
| **Approval quality** (v0.2.0) | rubber-stamp gates (100%-approved asks) surfaced in the tuning report; fewer, better gates | A gate approved 100% of the time is theater, not oversight (R36, ASI09) |
| **Replan usefulness** (v0.2.0) | % of denied calls where the agent adopts a `permitted_alternative` instead of bypassing | Denials that offer a true alternative get adopted; black-box denials get bypassed (R37) |
| **Evidence-reviewed policy PRs** (v0.2.0) | every policy PR ships with a backtest decision-diff attached | Policy changes become reviewable by evidence, not opinion (R43) — the enterprise buying trigger |

## Release gate (v0.1.0)

A release is not "done" unless:

1. All **five** outcomes are demonstrable in automated tests (R1).
2. The three launch rule packs each block their named incident replay (R3).
3. Every deny is explainable and passes the actionability test (R5).
4. Decisions are emitted in the agentwatch schema and join on a common id (R6).
5. Policies load from git and a change without review is flagged (R7).
6. p99 latency < 100 ms is measured in CI; every failure path is fail-closed (R8, CUJ-9).
7. The CI regression suite rejects a golden deny→allow flip (R22).
8. The adversarial sub-matrix passes with zero crafted allows (CUJ-11).
9. The compatibility table (harness × enforcer × version) is published.
10. The security baseline checklist (OWASP ASI/LLM + ATLAS mapping) is published and regenerated per release.
11. A non-security engineer completes CUJ-8 (first useful policy in an afternoon) in a user test.

## Anti-metrics (what we refuse to optimize)

- **"Detection rate" as a marketing number** — agentpolicy is deterministic policy, not a classifier.
- **Approval-rate theater** — a system that asks for everything is useless; measure *useful* gates, not count.
- **Policy volume** — more rules is not better; over-permissive and unused rules are lint findings (R12).
- **Silent allows** — never trade fail-closed for a green result.
- **Proprietary policy** — no closed formats, no opaque scoring.

## Instrumentation of success

- Every published decision links its `policy_version` + policy hash.
- Shadow reports (what *would have* been blocked) are the adoption funnel metric.
- The compatibility table and coverage matrix are regenerated from CI, not hand-edited.
- The explain artifact is the unit of review: if a reviewer cannot act on it, it is a bug.
