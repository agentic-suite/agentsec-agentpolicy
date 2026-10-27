# PRD 12 — Traceability

**BLUF:** Every v0.1.0 requirement traces to a critical user journey, a work-breakdown item, an acceptance
test, and its parity disposition. No requirement is orphaned and no absorbed capability is silently dropped.

**Status:** Draft — v0.1.0 (2026-10-26) · **Owner:** @deghosal-2026 · **Parent:** agentic-suite #209 · PRD #211

## Foundation milestones (M0)

M0 carries no new R-items; it establishes the engine, identity, and CLI surface every later milestone builds on.

| Milestone | Foundation deliverable | Acceptance test |
|---|---|---|
| M0 | Policy loader + validator, CLI surface + reserved exit codes, fail-closed config, `agentpolicy check`, `doctor` | `tests/test_cli_surface.py`, `tests/test_policy_loader.py`, `tests/test_config.py`, `tests/test_check.py` |

## Requirement → CUJ → WBS → test → parity

| Req | Requirement (short) | CUJ | WBS | Acceptance test | Parity ([PRD 10](10-feature-parity.md)) |
|---|---|---|---|---|---|
| **R1** | Five outcomes (allow/deny/ask/rate-limit/redact) | CUJ-1 | M1 | All five outcomes in the acceptance matrix · `tests/test_m1_outcomes.py` | Delivered, extended (P1) |
| **R2** | Cedar authoring + OPA/Rego import | CUJ-1, CUJ-5 | M1, M3 | First policy < 1 afternoon (user test) · `tests/test_m1_cedar.py`, `tests/test_m3_rego.py` | Delivered (P27) |
| **R3** | 3 launch rule packs block their incident replay | CUJ-4, CUJ-7 | M3 | Each pack blocks its named replay · `tests/test_m3_packs.py` | Delivered (P3, P25) |
| **R4** | Mandatory human-gate class (irreversible → ask) | CUJ-1, CUJ-10 | M1, M5 | Changing the default is a logged amendment · `tests/test_m1_gate_class.py` | Delivered (P14) |
| **R5** | `explain-decision` (clause + context) | CUJ-3 | M4 | 100% of denies traceable; actionability test · `tests/test_m4_explain.py`, `tests/test_m4_actionable.py` | Delivered (P10) |
| **R6** | Decisions in the agentwatch schema | CUJ-6, CUJ-14 | M4 | decision and record join on a common id · `tests/test_m4_events.py` | Delivered (P11) |
| **R7** | Versioned, reviewable policies | CUJ-6, CUJ-7 | M6 | Unreviewed change flagged · `tests/test_m6_policy_version.py` | Delivered (P5, P11) |
| **R8** | Local-first, sub-100 ms p99, fail-explicit | CUJ-1, CUJ-9 | M1, M10 | p99 in CI; every failure denies · `tests/test_m1_latency.py`, `tests/test_m10_failclosed.py` | Delivered (P26) |
| **R9** | Blast-radius budgets | CUJ-12 | M11 | Exhaustion halts with a reason · `tests/test_m11_budgets.py` | Delivered (P13) |
| **R10** | Exfil-sink rule class | CUJ-13 | M12 | Blocks the documented chain; names source+sink · `tests/test_m12_exfil.py` | Delivered (P16) |
| **R11** | Scope-escalation + step-up | CUJ-19 | M12 | Step-up loop is least-privilege · `tests/test_m12_stepup.py` | Delivered |
| **R12** | Rule-pack lint | CUJ-17 | M8 | Unused/shadowed/over-permissive reported · `tests/test_m8_lint.py` | Delivered |
| **R13** | OPA→Cedar migration + AuthZEN (full) | CUJ-14 | later | Rego migrates with a report | Waived at v0.1.0 (P9 partial) |
| **R14** | Policy-pack marketplace | CUJ-5 | later | Signed pack installs + passes `pack test` | Waived at v0.1.0 |
| **R15** | Contextual decision model (dimensions + taxonomy) | CUJ-1, CUJ-8 | M2 | Matrix scores differently by env/data class · `tests/test_m2_matrix.py` | Delivered (P2, P3) |
| **R16** | Posture presets + `init` scaffold | CUJ-8 | M8 | Pre-populated policy; `diff` shows gaps · `tests/test_m8_postures.py`, `tests/test_m8_diff.py` | Delivered (P6, P7) |
| **R17** | Session/context state | CUJ-12 | M11 | `session_id` reconstructs state · `tests/test_m11_session.py` | Delivered (P13) |
| **R18** | Ask round-trip (identity-bound, expiry, timeout=deny) | CUJ-10 | M5 | Replay/expiry rejected · `tests/test_m5_ask.py`, `tests/test_m5_replay.py` | Delivered (P14) |
| **R19** | Argument-level semantic validation | CUJ-11 | M12 | SELECT-only, refund cap, SSRF, path containment · `tests/test_m12_args.py` | Delivered (P15) |
| **R20** | Redact-and-allow + receipts | CUJ-15 | M5 | Secret removed before the model sees it · `tests/test_m5_redact.py` | Delivered (P16) |
| **R21** | Discovery-time tool hiding | CUJ-8 | M12 | Agent never sees a denied tool · `tests/test_m12_hiding.py` | Delivered (P17) |
| **R22** | CI policy regression suite | CUJ-7 | M10 | Golden deny→allow flip fails the build · `tests/test_m10_golden.py` | Delivered (P18) |
| **R23** | Rate/burst limits | CUJ-18 | M11 | Runaway throttled at the ceiling · `tests/test_m11_rate.py` | Delivered (P19) |
| **R24** | Dispatcher-bypass safety + normalization | CUJ-11 | M2 | Smuggled/obfuscated action denied · `tests/test_m2_normalize.py`, `tests/test_m2_dispatcher.py` | Delivered (P20) |
| **R25** | Child-agent delegation scope | later | later | Child scope escalation rejected | Waived at v0.1.0 (P21) |
| **R26** | Adversarial resilience suite | CUJ-11 | M12 | Replay + flood blocked; distinct reasons · `tests/test_m12_adversarial.py` | Delivered (P22) |
| **R27** | AuthZEN PDP interop | CUJ-14 | M12 | Conformant AuthZEN caller gets the same decision · `tests/test_m12_authzen.py` | Delivered, supersedes (P28) |
| **R28** | Delivery surfaces (library/CLI/MCP/HTTP) | CUJ-2, CUJ-14 | M7 | Same decision across surfaces · `tests/test_m7_surfaces.py`, `tests/test_m7_adapters.py` | Delivered (P8, P29) |
| **R29** | Pack catalog + `pack validate`/`test` | CUJ-5 | M3 | Community pack lands via one PR · `tests/test_m3_pack_test.py` | Delivered (P25) |
| **R30** | Shadow/dry-run + calibration report | CUJ-4 | M9 | Shadow logged; rates reported · `tests/test_m9_shadow.py`, `tests/test_m9_calibration.py` | Delivered (P24) |
| **R31** | Fleet/distributed policy sync | later | later | Policy propagates with drift detection | Waived at v0.1.0 (P9) |
| **R32** | Compliance-mapped evidence export | CUJ-6, CUJ-20 | M10 | Coverage matrix regenerated per release · `tests/test_m10_coverage.py` | Delivered (P26) |
| **R33** | Change-freeze / maintenance-mode windows | CUJ-21 | M13 | Freeze flips posture for the window, audited · `tests/test_m13_freeze.py` | New ([PRD 22](22-policy-intelligence-and-governance.md)) |
| **R34** | Declarative data-class derivation | CUJ-21, CUJ-1 | M13 | Untagged resource resolves; conflict fails loudly · `tests/test_m13_dataclass.py` | New |
| **R35** | Agent enrollment + probation | CUJ-22 | M13 | First-seen write → `ask` + `agent_probation` · `tests/test_m13_enrollment.py` | New |
| **R36** | Approval analytics (rubber-stamp detection) | CUJ-23 | M13 | Always-approved gate flagged · `tests/test_m13_approvals.py` | New |
| **R37** | Nearest-permissible-action | CUJ-24 | M13 | Alternative verified-permissible; no internals leak · `tests/test_m13_alternatives.py` | New |
| **R38** | Secrets-in-arguments | CUJ-15 | M13 | Arg secret scrubbed with receipt · `tests/test_m13_args_secrets.py` | New |
| **R39** | Multi-agent governance depth (extends R25) | CUJ-28 | M14 | Child out-of-scope denied, chain link named · `tests/test_m14_delegation.py` | New |
| **R40** | Break-glass with auto-revert | CUJ-25 | M14 | Expiry reverts without manual action · `tests/test_m14_breakglass.py` | New |
| **R41** | Dual-control approvals | CUJ-26 | M14 | One approval ≠ release; two distinct approvers = release · `tests/test_m14_dualcontrol.py` | New |
| **R42** | NL policy drafting (authoring-time) | CUJ-27 | M14 | Draft compiles, passes tests, waits for review · `tests/test_m14_draft.py` | New |
| **R43** | Policy backtest & PR decision-diff | CUJ-29 | M15 | Flip set exact; read-only; watermarked; advisory · `tests/test_m15_backtest.py` | New ([PRD 23](23-enterprise-adoption-and-governance-hardening.md)) |
| **R44** | Narrow-only policy layering | CUJ-30 | M15 | Widening overlay fails at `check`; floor holds under fuzz · `tests/test_m15_layering.py` | New |
| **R45** | Action-space coverage report | CUJ-31 | M15 | Dangerous quadrant named; `gap:unexplained` = 0 · `tests/test_m15_coverage.py` | New |
| **R46** | Self-attack pack (release cadence) | CUJ-32 | M15 | Seeded miss blocks the release; published with misses · `tests/test_m15_selfattack.py` | New |
| **R47** | Allow-justification | CUJ-33 | M15 | Allow names permitting rule + version · `tests/test_m15_allow_justify.py` | New |

## CUJ → requirement (reverse)

| CUJ | Serves |
|---|---|
| CUJ-1 Evaluate one action | R1, R2, R4, R8, R15 |
| CUJ-2 Wire into a harness/enforcer | R28 |
| CUJ-3 Understand why | R5 |
| CUJ-4 Adopt in shadow mode | R3, R30 |
| CUJ-5 Extend with a pack | R2, R29 |
| CUJ-6 Prove compliance | R6, R7, R32 |
| CUJ-7 Gate a policy PR | R3, R7, R22 |
| CUJ-8 Customize the posture | R15, R16, R21 |
| CUJ-9 Failure modes | R8 |
| CUJ-10 Ask round-trip | R4, R18 |
| CUJ-11 Adversarial resilience | R19, R24, R26 |
| CUJ-12 Budget the blast radius | R9, R17, R23 |
| CUJ-13 Block an exfil chain | R10 |
| CUJ-14 Ask from anywhere | R6, R27, R28 |
| CUJ-15 Redact a secret | R20 |
| CUJ-16 Compile one policy everywhere | R2 (policyweave) |
| CUJ-17 Lint the policy | R12 |
| CUJ-18 Rate-limit a runaway | R23 |
| CUJ-19 Step-up on escalation | R11 |
| CUJ-20 Verify a decision offline | R5, R6 |
| CUJ-21 Declare a change freeze | R33, R34 |
| CUJ-22 Enroll an unknown agent | R35 |
| CUJ-23 Find rubber-stamp gates | R36 |
| CUJ-24 Get a denial I can act on | R37 |
| CUJ-25 Break glass without breaking trust | R40, R41 |
| CUJ-26 Two humans for the irreversible class | R41 |
| CUJ-27 Draft a policy from a sentence | R42 |
| CUJ-28 Delegate without leaking scope | R39 (extends R25) |
| CUJ-29 Backtest a policy change | R43 (extends R22) |
| CUJ-30 Guarantee the floor | R44 |
| CUJ-31 See the uncovered action space | R45 |
| CUJ-32 Verify agentpolicy against itself | R46 |
| CUJ-33 Justify an allow | R47 (completes R5) |

## Decisions → requirements

| Decision | Enables |
|---|---|
| DD-01 decide-only | R28 (PDP surfaces), R27 |
| DD-02 Cedar primary | R2, R7 |
| DD-03 five outcomes | R1, R9, R20 |
| DD-04 no ML | R8 (determinism) |
| DD-05 event schema | R6 |
| DD-06 fail-closed | R8 |
| DD-09 canonical action | R24 |
| DD-10 AuthZEN | R27 |

## WBS (authored)

The work breakdown now exists: [`docs/wbs/v0.1.0/`](../wbs/v0.1.0/wbs-v0.1.0-index.md) — **M0–M25 across 13
part files**, with M0 a bulk port of the predecessor and M24/M25 the field tests + release readiness. **The WBS
is the operational source of truth and supersedes the milestone column above**: it renumbers with **M0 = the
port** (so the pre-WBS rows M0–M15 shift by +1 and the P1/P2 rows land at M12–M23), and it links **every CUJ
(CUJ-1..CUJ-33) explicitly** to a milestone. This PRD remains the requirement-side source of truth. Open
decisions still to resolve are listed in [PRD 21](21-evidence-register-and-method.md) §PRD tensions.
