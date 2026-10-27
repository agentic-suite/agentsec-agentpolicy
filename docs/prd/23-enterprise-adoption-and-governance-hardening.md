# PRD 23 — Enterprise Adoption & Governance Hardening

**BLUF:** The PRD is strong on *capability*; this document closes the *rollout and trust* gaps an enterprise
buyer actually hits: **policy backtest + PR decision-diff** (prove what a policy change would have done to real
history before merging), **narrow-only policy layering** (org floor → project overlay → session consent, where
children can only restrict — the AWS SCP pattern), **action-space coverage report** (which verbs the fleet
exercises that no rule covers), **self-attack pack** (agentpolicy's own decision surface drilled every
release), and **allow-justification** (allows are as traceable as denies). With these, the PRD set is
**declared complete** — further specification waits for field feedback.

**Status:** Draft — v0.2.0 scope (2026-10-26) · **Owner:** @deghosal-2026 · **Parent:** agentic-suite #209 · PRD #211

> Priority: **P1 (v0.2.0)**. All five stay inside the hard boundaries: decide-only, deterministic, no ML in any
> decision path, fail-closed. The v0.1.0 release gate is unchanged.

## Why these five (the enterprise-buyer audit)

| Addition | The gap it closes |
|---|---|
| Policy backtest + decision-diff | Policy changes are the scariest moment of adoption; goldens (R22) are synthetic, but enterprises change policy against **real workloads** — nothing today shows what a rule edit would have done to last week's actual actions |
| Narrow-only layering | A central team must guarantee a **floor** while teams tighten locally; without a provable can-only-restrict invariant, central policy and team policy fight and fleets fork |
| Action-space coverage | "What is my policy silent about?" — no tool reports the verbs the fleet exercises that **no rule mentions**; that silent quadrant is where incidents live |
| Self-attack pack | A decision service that never drills its own surface is asking to be trusted on faith; the ecosystem's proof discipline (agentdrill's evasion pack) turned on ourselves |
| Allow-justification | We explain denies but not allows — an auditor's first question is "who authorized this production write?", and `allow` must be as traceable as `deny` |

## The requirements

| # | Requirement | Pri | Acceptance criterion |
|---|---|---|---|
| **R43** | **Policy backtest & PR decision-diff** — replay a window of recorded agentwatch history against a candidate policy; emit the diff (newly-denied / newly-asked / newly-allowed / unchanged) and attach it to the policy PR | P1 | A backtest over a fixture history produces the exact flip set, runs **read-only** (no re-execution, no fleet events), is watermarked `backtest`, and states its coverage window + limits |
| **R44** | **Narrow-only policy layering** — org baseline → project overlay → session consent; an effective policy is the **intersection**, and a child layer may only restrict | P1 | A widening overlay **fails `agentpolicy check` at PR time** (load-time invariant, not a runtime surprise); the floor holds in a fuzz test over layer combinations |
| **R45** | **Action-space coverage report** — cross the canonical taxonomy with (a) rules referencing each verb/tool and (b) the fleet's actual invocations (agentwatch inventory) | P1 | The report names **exercised-but-uncovered** verbs (the dangerous quadrant) and dead rules (covered-but-never-exercised); every uncovered verb is covered or **declared out-of-scope** — `gap:unexplained` is zero, same discipline as agentwatch |
| **R46** | **Self-attack pack** — a shipped pack attacking agentpolicy's own decision surface (policy tamper, normalization bypass, ask replay, budget splitting, audit truncation, event forgery), run in CI every release | P1 | The pack runs against the deployed PDP; **a miss blocks the release**; anyone can run it against their own agentpolicy (dogfoodable) |
| **R47** | **Allow-justification** — every decision names its matched rule, **allows included** (from v0.2.0) | P1 | Given an allowed prod write, the decision + audit entry name the permitting rule and policy version; the approval-analytics report (R36) extends to always-allowed patterns |

## Feature catalog additions

| # | Feature | Req |
|---|---|---|
| F40 | Backtest engine (`agentpolicy backtest --history <window> --candidate <policy>`) + PR decision-diff (`--ci` attaches the flip set to the step summary) | R43 |
| F41 | Layered policy composition (org → project → session) with the narrow-only invariant enforced at load | R44 |
| F42 | Coverage report (`agentpolicy report coverage`) — taxonomy × rules × fleet inventory, four quadrants | R45 |
| F43 | Shipped `self-attack` pack + release-cadence CI job | R46 |
| F44 | `matched_rule` on all outcomes + allow-justification in the audit entry + allow patterns in the analytics report | R47 |

## Semantics that matter

- **Backtest is evidence, not proof.** History ≠ future: the report states the coverage window, the % of fleet
  actions it represents, and that it is **advisory input to review**, never auto-merge or auto-block. Backtest
  decisions emit **no fleet events** (watermarked `backtest`, excluded from live analytics and from the CI
  golden gate — a backtest flip is a review signal, not a failure).
- **Layering is enforced at load, not at decide.** A widening overlay is a **PR-time `check` failure** with the
  exact rule that widens — the invariant never becomes a runtime surprise. Session consent is the third layer:
  consent may only narrow (this is the same invariant as delegation scope-subset, R25/R39 — one rule, three
  layers).
- **The coverage report has a honesty contract.** Four quadrants: covered+exercised (good), covered+never
  (dead rule — lint's cousin), **uncovered+exercised (the dangerous quadrant — named loudly)**,
  uncovered+never (declare it out-of-scope or accept the noise). `gap:unexplained` must be zero — we apply our
  own agentwatch discipline to the user's policy.
- **The self-attack pack is a pack, not a test.** It runs through the same pack format anyone else uses —
  so third parties can run it against *their* deployed agentpolicy, and a pass is a claim we publish with the
  release (misses included, the ecosystem's honesty rule).
- **Allow-justification completes the symmetry.** Denies name the rule that blocked; allows name the rule that
  permitted. Without both, an audit can only ever answer half of "who authorized what?" — and the
  rubber-stamp analytics (R36) get their allow-side counterpart: always-permitted patterns surface for review.

## Critical user journeys

### CUJ-29 — Backtest a policy change against real history (P2 Ravi)
1. Ravi opens a policy PR that tightens the exfil-sink rules; CI runs `agentpolicy backtest --history 7d --ci`.
2. The PR shows the **decision-diff**: 14 newly-denied, 3 newly-asked, 0 newly-allowed, with the reasons and
   the actions' context.
3. **Success:** the flip set is exact and reproducible; the report states its coverage (what % of fleet actions
   the window represents) and that it is advisory; nothing re-executed and no live events were emitted.

### CUJ-30 — Guarantee the floor (P1 Maya)
1. The central team owns the org baseline (prod-writes `ask`, secrets critical). A project team overlays a
   pack that tries to allow prod writes silently.
2. **Success:** `agentpolicy check` **fails at PR time** naming the widening rule; no combination of overlays
   can widen the floor (fuzz-tested); locally the team can still tighten further.

### CUJ-31 — See the uncovered action space (P1 Maya)
1. Maya runs `agentpolicy report coverage` before a compliance review.
2. **Success:** the report names the **exercised-but-uncovered** verbs ("the fleet ran `secrets.rotate` 12
   times last week; no rule mentions it"), the dead rules, and the declared out-of-scope set —
   `gap:unexplained` is zero.

### CUJ-32 — Verify agentpolicy against itself (public / P5 Alex)
1. Every release, the shipped `self-attack` pack runs against the deployed PDP in CI.
2. **Success:** a tamper/replay/bypass attempt that gets through **blocks the release**; the pack's result is
   published with the release notes, misses included; a third party can re-run the same pack against their own
   deployment.

### CUJ-33 — Justify an allow (auditor)
1. An auditor asks who authorized a production write that was **allowed** last Tuesday.
2. **Success:** the decision + audit entry name the permitting rule, the policy version, and (if consent-scoped)
   the session consent — allows are exactly as traceable as denies (R5's deny contract, completed).

## Traceability

| Req | CUJ | Test |
|---|---|---|
| R43 | CUJ-29 | `tests/test_m15_backtest.py` — flip set exact over fixture history; read-only; watermarked; no golden-gate pollution |
| R44 | CUJ-30 | `tests/test_m15_layering.py` — widening overlay fails at `check`; floor holds under layer-combination fuzz |
| R45 | CUJ-31 | `tests/test_m15_coverage.py` — dangerous quadrant named; `gap:unexplained` = 0 |
| R46 | CUJ-32 | `tests/test_m15_selfattack.py` — the pack runs as a pack; a seeded miss blocks the release |
| R47 | CUJ-33 | `tests/test_m15_allow_justify.py` — allow names permitting rule + version; allow patterns in the report |

Milestone: **M15 (v0.2.0)** — extends the M0–M14 commitment in [PRD 12](12-traceability.md) §WBS.

## New risks

| # | Risk | Mitigation |
|---|---|---|
| **RK-21** | **Backtest false confidence** — "the diff was empty, ship it" on a thin history window | Coverage % + window stated on every report; backtest is advisory and never auto-merges; the golden gate (R22) remains the hard gate |
| **RK-22** | **Layering complexity** — three layers + packs + consent becomes unreadable | The narrow-only invariant is one rule enforced at load; the coverage report (R45) and lint (R12) are the readability guardrails |
| **RK-23** | **Self-attack pack rots** — the pack stops tracking the real attack surface | Every new decision-surface feature (R33–R47) must add or update a self-attack case; the pack's coverage is itself reported (R45 discipline) |

## With this document, the PRD set is complete

PRD 00–23 now cover: why, architecture, landscape, users/CUJs (33), features (R1–R47, F1–F44), security baseline,
success metrics, risks (RK-1–23), roadmap, parity, decisions, traceability, NFRs, non-goals, data model, rule
packs, explain/evidence, budgets, harness compatibility, standards/claims, evidence/method, policy intelligence
(PRDM 22), and enterprise adoption (this document). **The next artifacts are the WBS, design docs, and code —
not more PRD.** The agentdrill lesson stands: the field test found 11 harness defects no PRD anticipated;
further specification before field feedback is over-specification.
