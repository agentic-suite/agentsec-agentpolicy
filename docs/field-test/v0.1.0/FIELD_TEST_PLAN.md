# Field-Test Plan — agentpolicy v0.1.0

**Milestone:** M24 Field Tests · **Authored:** `24.D0` (#255), 2026-11-01
**Plan (this doc) →** report `docs/field-test/v0.1.0/FIELD_TEST_REPORT.md` · **Harness:** `agentpolicy field-test` +
`scripts/run_field_agents.py` · **Results:** `tests/field/results/<framework>/` · **Scenario matrix:**
`tests/field/scenarios.yaml` · **Roster:** `tests/field/agents.yaml`.

**BLUF.** agentpolicy v0.1.0 is a **deterministic Cedar policy decision point** — `(principal, action, resource,
context) → allow / deny / ask / rate-limit / redact` — behind every enforcer. Its field test drives **real agents
across 10 frameworks** through a scripted scenario matrix plus an adversarial sub-matrix, and must prove **every
CUJ-1…CUJ-33 end to end** (PRD 04), **every R1–R47** in a live loop (PRD 05 / PRD 12), the **own-threat-model**
(PRD 06), and the predecessor's decision model **absorbed and not regressed** (PRD 10). This plan **extends** the
predecessor's field-test plan (`agent-tooltrust` v0.1.0 + v0.2.0 S1–S10); it does not replace it. The matrix is
frozen here so M24 execution is a matter of **running, not deciding**.

Sources: [WBS v0.1.0 Part 13](../../wbs/v0.1.0/wbs-v0.1.0-part13-fieldtest-release.md) (M24 items #255–#266),
[PRD 04](../../prd/04-users-and-cujs.md) (CUJ-1…33), [PRD 05](../../prd/05-features.md) (R1–R47),
[PRD 06](../../prd/06-security-baseline.md) (own attack surface), [PRD 10](../../prd/10-feature-parity.md) (parity),
[PRD 12](../../prd/12-traceability.md) (traceability), [PRD 19](../../prd/19-harness-compatibility.md) (harness
compat), [PRD 07](../../prd/07-success-metrics.md) (release gate). Predecessor plan:
`_predecessors/agent-tooltrust/docs/field-test/field-test-plan.md` (v0.1.0, M7) and
`field-test-plan-v0.2.0.md` (v0.2.0 S1–S10).

---

## 0. Readiness, doctrine, and status

### 0.1 Doctrine (inherited from the predecessor field test, unchanged)

- **No skips.** Every case is `pass` / `fail`. A case that cannot run is a **failure**, not a skip, and the run
  exits non-zero. The one exception is the **declare class** (§0.2), used only where the release gate says so.
- **Determinism is the product.** The decision path contains **no ML, no randomness, no network**. The LLM (when
  used by a live framework adapter) is a **test oracle**, never the decision-maker (DD-04). Replay of the
  same input + policy **must** reproduce the same decision (DD-04, NFR).
- **Boot the system under test per layer, and verify it before assertions** — the engine matrix boots the
  in-process `Engine`; the surface cases boot the MCP server / HTTP PDP; the live cases boot the vendored framework
  against OMLX. `agentpolicy doctor` is the readiness probe.
- **Verify the verifier.** Every suite's assertions are exercised against a **known-bad input** (a deliberately
  broken fixture) so a green run cannot hide an unexercised path — the agentdrill lesson, applied to the harness.
- **One harness, layered under test.** The field test reuses the shipped primitives — `FieldTestRunner`
  (`agentpolicy field-test`), `scripts/run_field_agents.py` (Plan A/B/full), the packs/gates, and the CLI — and
  **never forks a parallel harness**.

### 0.2 The "declare" class

Cases whose environment is genuinely unavailable in the runner (no OMLX, a framework's vendored repo not
checked out, no Docker) may resolve to **`declared`** — allowed **only** for a case whose live-gate permits it
(PRD 19 honest-coverage rule). A `declared` case requires **all** of:

1. a named limitation with a PRD/PRD-19-tier reference,
2. an evidence artifact showing the blocked attempt (`commands.log` + `stderr.log` + an environment fingerprint),
3. a line in `docs/field-test/v0.1.0/known-limitations.md` with its proving test, and
4. a release gate that permits "declared".

`declared` is **not** allowed for any hard gate (the five outcomes, fail-closed, explainability, the packs, the
self-attack, parity). The `Class` column fixes this: **P/F** = must pass or fail; **P/F|D** = pass, or declared.
A `declared` case still **fails the suite** unless its release gate permits it, so the run stays honest.

### 0.3 Status at authoring (2026-11-01)

M0–M23 are complete on `feat-0.1.0` (WBS index Progress). The field-test harness, the 30-scenario predecessor
matrix, and the 100-agent roster already exist (M7); the new cases below are the **v0.1.0 additions** (R9–R47).

| Item | Status |
|---|---|
| `agentpolicy field-test` + `FieldTestRunner` (deterministic engine matrix) | ✅ available |
| `scripts/run_field_agents.py` (live/self-test, Plan A/B/full) + vendor download | ✅ available |
| `tests/field/{scenarios,agents}.yaml` (20 decision + 10 adversarial · 100 agents) | ✅ available |
| Framework shims (`tests/field/agents/*.py`, 10 frameworks) | ✅ available |
| Pack/CI gates (`goldens`, `drill`, `self-attack`, `compliance`, `claims`) | ✅ available (M11/M22/M23) |
| New scenario groups (S1–S18, this plan) | ☐ to add to `scenarios.yaml` + the L1/Tier-1 drivers |
| Report `docs/field-test/v0.1.0/FIELD_TEST_REPORT.md` | ☐ to write (M24.5) |

**Overall status: READY TO RUN.** The roster and matrix are frozen; execution is M24.

---

## 1. What already exists (reuse as-is — do not fork)

| Asset | Role in the M24 plan |
|---|---|
| `agentpolicy.field.runner.FieldTestRunner` + `agentpolicy field-test` | the deterministic engine matrix (decision + adversarial), exit non-zero on failure |
| `scripts/run_field_agents.py` (`--plan A\|B\|full`, `--list`) | the live/self-test framework sweep + covering design |
| `tests/field/agents/*.py` (10 shims) + `scripts/download_field_agents.sh` | real framework agents sourced from upstream repos |
| `tests/field/{scenarios,agents}.yaml` | the scenario matrix + the 100-agent roster |
| `agentpolicy goldens check`, `drill check`, `self-attack check` | the CI regression / incident-replay / self-attack gates |
| `agentpolicy compliance export`, `compliance claims` | the computed standards matrix + the claims linter |
| `agentpolicy {evaluate,explain,check,init,diff,lint,export,audit,ask,escalation,freeze,breakglass,draft,backtest,report}` | the per-feature drivers |
| `agentpolicy {doctor,nfr,faultinject,sandbox,cost,parity,deferred}` | the NFR / hardening / parity primitives (M23) |
| `.github/workflows/ci.yml` `field-test` job | the CI leg (deterministic matrix + agent-build smoke + scripted replan) |

**Do not create a parallel harness.** New cases drive the same `FieldTestRunner` / `run_field_agents.py` / CLI.

---

## 2. What M24 must additionally prove (the gap this plan closes)

The predecessor field test proved the **record/decision layer** on 4 outcomes. v0.1.0 must additionally prove:

- **The five outcomes** — `ask` (renaming the predecessor's `escalate`), `rate-limit` and `redact` (new);
  `audit` folds into always-on event emission (R1, DD-03, PRD 03) — all five exercised end to end (CUJ-1).
- **The own attack surface** — policy tamper, normalization bypass, ask replay, budget splitting, audit
  truncation, event forgery (PRD 06) → the `self-attack` pack (R46) run every release.
- **The v0.1.0 additions** — budgets, exfil, step-up/AuthZEN, freeze, data-class, enrollment, approval analytics,
  nearest-permissible-action, multi-agent, break-glass, dual-control, NL drafting, backtest, layered policies,
  coverage, allow-justification (R9–R47).
- **The predecessor's v0.2.0 S1–S10 scenario groups** — incorporated case-by-case (§5a), mapped to R-items.
- **Parity closure** — every absorbed predecessor capability delivered/delegated/waived (PRD 10 / `parity`).
- **Every CUJ-1…CUJ-33** appears in ≥1 end-to-end field case (§8).

---

## 3. Harness layers & topology

The predecessor used Docker per case. agentpolicy is **local-first, in-process**; its field test is layered:

| Layer | System under test | Boot | Driver |
|---|---|---|---|
| **L0 — Engine matrix** | the in-process `Engine` (legacy ported 4-state path) | `Engine(default_field_policy(...))` | `agentpolicy field-test` (`FieldTestRunner`) |
| **L1 — Cedar five-outcome core** | `cedar.CedarEvaluator` + shaper + `ServerCore` | in-process | **acceptance-matrix fixtures** (`tests/fixtures/acceptance_matrix.yaml`) + **pack replays** (`pack test`) + `CedarEvaluator` cases |
| **L2 — Delivery surfaces** | library (`api.evaluate`), CLI, MCP server, HTTP PDP (AuthZEN) | in-process / loopback server | surface-parity cases |
| **L3 — Live frameworks** | the 10 framework adapters against vendored repos + OMLX | `scripts/download_field_agents.sh` + `run_field_agents.py` | live/self-test sweep |
| **L3b — Tier-1 harnesses** | Claude Code / Cursor / Codex CLI / Gemini CLI via their hook/config surfaces | the harness on the box, or `agentpolicy export` → policyweave artifacts | §S18 |
| **Docker (optional)** | the HTTP PDP / MCP server container | `docker compose up` | `docker-test` (smoke + SSE) |

**Driver note (load-bearing):** `agentpolicy field-test` (`FieldTestRunner`) evaluates through the **legacy
4-state Engine** — its shipped `scenarios.yaml` expects `allow`/`audit`/`escalate`/`deny` with the legacy reason
codes. The **five-outcome Cedar path** (`ask`/`rate-limit`/`redact`) is exercised by the L1 drivers: the
acceptance-matrix fixtures, the pack replays, the server-core cases, and direct `CedarEvaluator` cases (see
`tests/test_m5_explain.py::_GATED`). An FT-DEC-* case names its actual driver; a five-outcome case never claims
the legacy field runner. **Harness work item (24.1):** add a `--core cedar` mode to `field-test` so the matrix
can also drive the Cedar path natively (optional nicety; the L1 drivers above are the proof of record).

**No-Docker default:** L0–L2 run with **zero Docker**; L3/L3b run wherever the frameworks + OMLX / the harnesses
are available; the Docker legs (`agentpolicy doctor` in-container, the HTTP/MCP smoke) are `P/F|D` where Docker
is absent.

---

## 4. Local models (OMLX) — where LLMs are and are not used

> **Explicit boundary (DD-04): no LLM ever decides anything under test.** The decision under test —
> `allow / deny / ask / rate-limit / redact` — is always the output of the deterministic engine (Cedar +
> rules + budgets). An LLM appears in exactly **one** place in this field test: the **L3 live-framework
> sweep**, where it plays the *agent under guard* — it chooses **which tool to call**, and the guard
> intercepts that call. It is a **test oracle** proving the adapter surfaces decisions inside a real agent
> loop (the DD-11 "deny surfaces as a protocol crash vs a ToolMessage" class of bug) — it never produces,
> scores, or softens an expected outcome. **No case calls a hosted model**; every LLM is the box-local OMLX
> endpoint. Every assertion is checked against a **golden expectation fixed in `scenarios.yaml`** — a case
> passes on the engine's decision, never on model output. The engine's own decision path contains **no ML,
> no randomness, no network** — asserted by FT-DEC-DETERMINISM and the M19 boundary-lock test (the runtime
> never imports a model).

Where LLMs actually appear in this repo's testing, exhaustively:

| Surface | LLM? | Role |
|---|---|---|
| The decision path (`Engine`, `CedarEvaluator`, packs) | **never** | deterministic — DD-04; asserted by FT-DEC-DETERMINISM + the M19 boundary lock |
| L0–L2 cases (§S1–S15, §S17) + SWE-bench/MCP self-tests | **never** | fixtures + golden expectations only |
| `agentpolicy draft` (M19) | authoring-time only | advisory candidate generation; **blocked from the runtime path by design and by test** |
| `engine/llm_explain.py` | optional, off by default | explanation enrichment; not exercised by any field case |
| L3 live frameworks (`run_field_agents.py`) | **yes — deliberately** | the LLM *acts as the agent* and picks which tool to call; the guard + engine decide |
| Replan round-trip | `scripted` = none; `live` = OMLX | `scripted` is the CI-safe default |

Endpoint/model are recorded in the per-run environment fingerprint; `temperature=0`. **New rule:** every
LLM-backed case also asserts the model was actually called (`llm_called_ok`); a silent fallback is not a
pass.

### 4.1 Model selection — the OMLX benchmark (applied)

The live-sweep model is chosen for exactly two things: it must **reliably emit a tool call**
(`scn_<id>`) and it must be **fast**. `scripts/fieldtest/omlx_bench.py` measures every model served by
the box's OMLX with a field-test-shaped request (`tools=[scn_…]`, `tool_choice=auto`). Findings
(2026-11-01, this box, 3 trials, `temperature=0`):

| OMLX model | tool calls | p50 latency | tps | verdict |
|---|---|---|---|---|
| **Qwen3-4B-Instruct-2507-4bit** | **3/3** | **~1.0 s** | 19.1 | ✅ **pinned — best fit** |
| mlx-community--Qwen3.5-4B-4bit | 3/3 | ~6.6 s | 25.7 | ok (faster tps, ~7× slower) |
| Qwen3.5-4B-4bit | 3/3 | ~6.8 s | 23.2 | ok |
| Qwen3.5-9B-MLX-4bit | 3/3 | ~12.9 s | 17.0 | slow |
| Qwen3-8B-4bit | 3/3 | ~27.5 s | 20.3 | too slow |
| Llama-3.2-3B-Instruct-4bit | **0/3** | ~0.8 s | 16.6 | ❌ **disqualified** — never emits a tool call |

**Recommendation (applied):** pin **`Qwen3-4B-Instruct-2507-4bit`** — the fastest model that reliably
emits a tool call (~7× faster than the Qwen3.5-4B pair at p50, ~27× faster than Qwen3-8B), and the
predecessor's (agentdrill's) primary pin. Tool-call reliability is the gating criterion, so
Llama-3.2-3B is out despite the lowest raw latency; the 8B/9B models are out on latency. The pin lives
in `.env.example`, `lib.sh`, `docker-compose.fieldtest.yml`, `tests/field/agents/__init__.py`, and
`field/replan.py`; re-run `python3 scripts/fieldtest/omlx_bench.py` on a new box to re-derive it.
`MarkItDown` is a document converter, not an LLM, and is excluded.

---

## 5. Layer 0 — the predecessor regression gate (mandatory, unchanged)

v0.1.0 must not regress the decision model. The **entire predecessor matrix runs first** in every M24 run:

| Regression block | Count | Source |
|---|---|---|
| Decision matrix (`allow`/`audit`/`escalate`/`deny`) | 20 | `tests/field/scenarios.yaml` (decision) |
| Adversarial sub-matrix (CUJ-11) | 10 | `tests/field/scenarios.yaml` (adversarial) |
| Predecessor v0.2.0 groups **S1–S10** | see §5a | mapped to M24 cases below |

**Pass condition:** 30/30 scenarios ✓ across the roster, zero skips, before any v0.1.0 case is evaluated. A
predecessor regression is a **release blocker**, fixed with its own regression test (M24.6).

### 5a. Predecessor v0.2.0 S1–S10 — incorporated (nothing silently dropped)

| Predecessor group | Predecessor capability | M24 case(s) | R-item |
|---|---|---|---|
| **S1** session risk escalation | cumulative risk/budget pushes `allow`→`escalate` | FT-BUDGET-EXHAUST, FT-BUDGET-STATE | R9, R17 |
| **S2** argument bypass | right tool, unsafe args → deny | FT-ARG-VALIDATE | R19 |
| **S3** escalation round-trip | escalate → human approves via CLI → executes | FT-ASK-ROUNDTRIP, FT-ASK-BINDING | R18 |
| **S4** tool scanning/hiding | read-only agent probes a hidden tool | FT-HIDING | R21 |
| **S5** dispatcher smuggled calls | `git push --force` / `aws s3 rm` / curl strings | FT-DISPATCHER | R24 |
| **S6** URL fetch guard | PII body / SSRF redirect / robots.txt | FT-HTTP-GUARD | R10, R19 |
| **S7** deny-storm probe | dense denied-tool run → throttle/lock/pause | FT-DENYSTORM | R26 |
| **S8** scope enforcement | staging-scoped agent touches prod → deny | FT-SCOPE | R15, R28 |
| **S9** delegation subset | child scope ⊆ parent; superset denied | FT-DELEGATION | R25, R39 |
| **S10** self-report vs ground truth | agent claims done; counter didn't move | FT-VERIFY | R6 (agentwatch verifier) |

### 5b. Predecessor v0.1.0 30 scenarios — retained verbatim

The 20 decision + 10 adversarial scenarios keep their original ids and expected decisions; the new cases **append**
to `scenarios.yaml` and never renumber an existing id. A changed feature keeps its original case **plus** a v0.1.0
companion (the parity discipline).

---

## 6. Master scenario matrix — the v0.1.0 cases

`Class`: **P/F** = must pass or fail. **P/F|D** = pass, or declared with a named limitation.
`Env` keys: `ci` = ci-hermetic (no LLM/Docker), `mac`/`lin` = local OS, `llm` = OMLX local, `vend` = vendored
frameworks present, `t1` = a Tier-1 coding-agent harness on the box, `docker` = Docker available.

### S1 — Five outcomes & the decision core (R1, R15; CUJ-1)

| ID | Capability | PRD/ticket | CUJ | Env | Driver | Pass condition | Class |
|---|---|---|---|---|---|---|---|
| FT-DEC-ALLOW | benign read in staging → `allow` | R1, R15 | 1 | ci | acceptance matrix + `field-test` | `decision=allow`, `reason_code=allow_low_risk` | P/F |
| FT-DEC-DENY | destructive prod action → `deny` | R1 | 1 | ci | acceptance matrix + `CedarEvaluator` | `decision=deny`, criticality `critical`, clause named | P/F |
| FT-DEC-ASK | prod write (human-gate class) → `ask` | R1, R4 | 1 | ci | `CedarEvaluator` + `gates` | `decision=ask`, `human_gate_required`, `ask_id` | P/F |
| FT-DEC-RATE | over session budget → `rate-limit` | R1, R23 | 1,18 | ci | `CedarEvaluator(budget_exhausted=True)` + server | `decision=rate-limit`, `retry_after` present | P/F |
| FT-DEC-REDACT | secret in tool output → `redact` | R1, R20 | 1,15 | ci | `CedarEvaluator` + `redaction` | `decision=redact`, receipt class/count/location | P/F |
| FT-DEC-UNKNOWN | unknown tool → `deny` (fail-closed) | R8 | 1,9 | ci | acceptance matrix + `field-test` | `deny`, `unknown_action` | P/F |
| FT-DEC-CONTEXT | same call differs by env/data_class | R15 | 1,8 | ci | acceptance matrix + `field-test` | matrix scores differently per env/class | P/F |
| FT-DEC-DETERMINISM | same input+policy → same decision | R8, NFR | 1 | ci | pytest + `CedarEvaluator` | 1000 replays identical; no network in path | P/F |

### S2 — Explain, events, audit, evidence, allow-justification (R5, R6, R7, R47; CUJ-3,6,20,33)

| ID | Capability | PRD/ticket | CUJ | Env | Driver | Pass condition | Class |
|---|---|---|---|---|---|---|---|
| FT-EXPLAIN-CLAUSE | every deny names its clause | R5 | 3 | ci | `explain` | 100% of denies carry `matched_rule`/reason class | P/F |
| FT-EXPLAIN-ACTIONABLE | the actionability test | R5 | 3 | ci | `explain` | the one change that flips is derivable from the text alone | P/F |
| FT-EVENT-BIND | decisions in the agentwatch schema | R6 | 6,14 | ci | `agentwatch.to_event` | event + audit join on `event_id`/`decision_id` | P/F |
| FT-AUDIT-CHAIN | tamper-evident hash chain | R7, F17 | 6,20 | ci | `audit` | a broken link is detected; verify green on a clean log | P/F |
| FT-AUDIT-PROVENANCE | policy provenance per entry | R7 | 6 | ci | `audit` | `policy_version`+`policy_hash`+`matched_rule` on every entry | P/F |
| FT-EVIDENCE-OFFLINE | offline evidence artifact | R5, R6 | 20 | ci | `audit evidence` | a third party re-derives the decision offline | P/F |
| FT-ALLOW-JUSTIFY | allow names its permitting rule | R47 | 33 | ci | `explain`/`audit` | an allowed call names `matched_rule`+version | P/F |

### S3 — Rule packs & CI gates (R3, R22, R29, R32, R46; CUJ-5,7,32)

| ID | Capability | PRD/ticket | CUJ | Env | Driver | Pass condition | Class |
|---|---|---|---|---|---|---|---|
| FT-PACK-LAUNCH | 3 launch packs block their incident | R3 | 5,7 | ci | `pack test` | each pack denies its named replay, zero false positives on the benign twin | P/F |
| FT-PACK-VALIDATE | pack schema + Cedar parse | R29 | 5 | ci | `pack validate` | every shipped pack validates | P/F |
| FT-GOLDEN-FLIP | golden deny→allow flip fails | R22 | 7 | ci | `goldens check` | a flipped golden fails the build, deterministically | P/F |
| FT-DRILL | agentdrill incident replay | R22 | 7 | ci | `drill check` | an un-blocked incident replay fails | P/F |
| FT-SELF-ATTACK | self-attack pack gate | R46 | 32 | ci | `self-attack check` | a seeded miss exits 1; the shipped pack has zero misses | P/F |
| FT-COMPLIANCE-MATRIX | computed standards matrix | R32 | 6 | ci | `compliance export` | matrix computed from pack domains (not hardcoded) | P/F |
| FT-CLAIMS | claims linter | R32, PRD 20 §G | — | ci | `compliance claims` | a claim on an uncovered control is rejected | P/F |

### S4 — Posture, init, diff, lint, export, layering, coverage (R16, R12, R2, R44, R45; CUJ-8,16,17,30,31)

| ID | Capability | PRD/ticket | CUJ | Env | Driver | Pass condition | Class |
|---|---|---|---|---|---|---|---|
| FT-POSTURE | strict/balanced/permissive differ | R16 | 8 | ci | `check`/engine | a custom env/data-class scores the same call differently | P/F |
| FT-INIT | commented, pre-populated preset | R16 | 8 | ci | `init` | `load(text) == default_policy(name)`; not blank | P/F |
| FT-DIFF | kept / overridden / gaps (+`--json`) | R16 | 8 | ci | `diff` | classes the delta vs the posture default | P/F |
| FT-LINT | unused/shadowed/over-permissive/secrets | R12 | 17 | ci | `lint` | each finding reported with a location; CI-failable | P/F |
| FT-EXPORT | Cedar source + policyweave artifact compiled outward | R2, PRD 19 | 16 | ci | `export` | Cedar source + the policyweave artifact; drift between source and a harness format is flagged | P/F |
| FT-LAYER-NARROW | a widening overlay fails `check` | R44 | 30 | ci | `check --parent` | exit 2 naming the widening `allow` rule | P/F |
| FT-COVERAGE | four quadrants, `gap:unexplained`=0 | R45 | 31 | ci | `report coverage` | dangerous quadrant named; gap zero over the corpus | P/F |

### S5 — Shadow, calibration, canary (R30; CUJ-4)

| ID | Capability | PRD/ticket | CUJ | Env | Driver | Pass condition | Class |
|---|---|---|---|---|---|---|---|
| FT-SHADOW | `dry_run` logs the real decision, returns `allow` | R30 | 4 | ci | engine | audit shows the would-be decision; caller sees `allow` | P/F |
| FT-CALIBRATION | false-block/miss rates + threshold table | R30 | 4 | ci | `calibrate report` | rates are pure functions of the trail | P/F |
| FT-CANARY | deterministic session-percent canary | R30 | 4 | ci | engine | cohort = `sha256(session_id)%100`; 5→50→100 stages | P/F |

### S6 — Budgets, rate limits, blast radius (R9, R23; CUJ-12,18)

| ID | Capability | PRD/ticket | CUJ | Env | Driver | Pass condition | Class |
|---|---|---|---|---|---|---|---|
| FT-BUDGET-EXHAUST | cumulative exhaustion → `rate-limit` | R9 | 12 | ci | engine | splitting across calls does not evade the ceiling | P/F |
| FT-BUDGET-RETRY | `retry_after` the agent can honor | R23 | 18 | ci | engine | a structured throttle reason + `retry_after` | P/F |
| FT-BUDGET-BURST | burst/op-count limit | R23 | 18 | ci | engine | runaway loop throttled at the ceiling | P/F |
| FT-BUDGET-STATE | `budget_state` on every decision | R9 | 12 | ci | engine | remaining per dimension visible | P/F |
| FT-HALT | agenthalt fires on hard exhaustion | R9 | 12 | ci | `agenthalt` | a halt event with budget-state evidence | P/F |

### S7 — Argument validation, exfil, hiding, secrets, redaction (R19, R10, R21, R38, R20; CUJ-11,13,15)

| ID | Capability | PRD/ticket | CUJ | Env | Driver | Pass condition | Class |
|---|---|---|---|---|---|---|---|
| FT-ARG-VALIDATE | regex/enum/path_root/url_allowlist | R19 | 11 | ci | engine | SELECT-only SQL, refund cap, path containment, URL allowlist | P/F |
| FT-HTTP-GUARD | PII body / SSRF / robots.txt | R10, R19 | 11 | ci | `fetch_guard` | SSRF blocked; robots.txt enforced; PII flagged | P/F |
| FT-EXFIL-SINK | exfil chain denied, source+sink named | R10 | 13 | ci | engine | the documented chain is blocked, naming both ends | P/F |
| FT-HIDING | discovery-time tool hiding | R21 | 8 | ci | engine | a denied/hidden tool never appears in the capability list | P/F |
| FT-ARG-SECRET | secret in arguments scrubbed/blocked | R38 | 15 | ci | `redaction` | receipt class/count/location; raw value never persisted | P/F |
| FT-REDACT-RECEIPT | redaction receipt on the output path | R20 | 15 | ci | `redaction` | the secret is removed before the model sees it | P/F |
| FT-VERIFY | self-report vs external ground truth | R6 (agentwatch) | 6 | ci | `verify` | a contradicted self-report is flagged | P/F |

### S8 — Ask round-trip, escalation, dual-control, break-glass (R18, R40, R41; CUJ-10,25,26)

| ID | Capability | PRD/ticket | CUJ | Env | Driver | Pass condition | Class |
|---|---|---|---|---|---|---|---|
| FT-ASK-ROUNDTRIP | ask → approve → allow | R18 | 10 | ci | `ask`/`approve` | approved call executes; audit records the approver | P/F |
| FT-ASK-TIMEOUT | timeout = deny | R18 | 10 | ci | `ask` | an expired/timed-out ask → `deny` (`human_gate_timeout`) | P/F |
| FT-ASK-BINDING | approval bound to action identity | R18 | 10,11 | ci | `ask` | an approval for X cannot release Y (replay fails) | P/F |
| FT-DUALCONTROL | quorum of distinct approvers | R41 | 26 | ci | `dualcontrol` | one approval ≠ release; two distinct = release | P/F |
| FT-BREAKGLASS | time-boxed elevation auto-reverts | R40 | 25 | ci | `breakglass` | expiry reverts without action; `break_glass_id` on decisions | P/F |

### S9 — Delivery surfaces & AuthZEN interop (R28, R27; CUJ-2,14,16)

| ID | Capability | PRD/ticket | CUJ | Env | Driver | Pass condition | Class |
|---|---|---|---|---|---|---|---|
| FT-SURFACE-PARITY | library/CLI/MCP/HTTP same decision | R28 | 2,14 | ci | `api`/MCP/HTTP | identical `Decision` across all four surfaces | P/F |
| FT-AUTHZEN | conformant `/access/v1/evaluation` | R27 | 14 | ci | HTTP PDP | a conformant AuthZEN caller gets the same decision | P/F |
| FT-ADAPTERS | adapter registry validated | R28 | 2 | ci | `adapters` | unknown/missing-extra → `ConfigError` (exit 2) | P/F |
| FT-MCP-ASK | the MCP ask path | R18, R28 | 14 | docker | MCP server | an MCP client resolves an ask like the in-process path | P/F\|D |
| FT-DOCKER-SMOKE | container health + SSE | R28 | 2 | docker | `docker-test` | health endpoint ok; SSE integration green | P/F\|D |

### S10 — Normalization, dispatcher, scope, step-up & the adversarial suite (R24, R26, R15, R11; CUJ-11,19)

| ID | Capability | PRD/ticket | CUJ | Env | Driver | Pass condition | Class |
|---|---|---|---|---|---|---|---|
| FT-NORM-OBFUSCATION | Unicode/case/whitespace tool names | R24 | 11 | ci | `field-test` (adv) | normalized before matching; unknown → deny | P/F |
| FT-DISPATCHER | bash/git/http/aws smuggling | R24 | 11 | ci | `dispatcher` | canonicalized to the same policy; unparseable → deny | P/F |
| FT-ADV-REPLAY | approval replay with different args | R26 | 11 | ci | `ask`/`escalation` | replay denied, distinct reason | P/F |
| FT-ADV-FLOOD | rapid calls hoping one slips | R26 | 11 | ci | engine | per-session limits; every call evaluated | P/F |
| FT-DENYSTORM | deny-storm / probe detection | R26 | 11 | ci | `deny_storm` | lock/throttle/pause fires with a distinct reason | P/F |
| FT-ADV-DISTINCT | every attack yields a distinct reason | R26 | 11 | ci | `field-test` (adv) | no two attack classes share a reason code | P/F |
| FT-SCOPE | session/identity scope enforcement | R15, R28 | 11 | ci | engine | a staging-scoped agent touching a prod entity → `deny_out_of_scope` | P/F |
| FT-STEPUP | scope-escalation → least-privilege step-up | R11 | 19 | ci | `stepup` | a 403 challenge maps to a narrowed-scope variant (`acr_values`) | P/F |

### S11 — Freeze windows & data-class derivation (R33, R34; CUJ-21)

| ID | Capability | PRD/ticket | CUJ | Env | Driver | Pass condition | Class |
|---|---|---|---|---|---|---|---|
| FT-FREEZE | declared window flips the posture | R33 | 21 | ci | `freeze` | a prod write → `ask`/`deny`; `freeze_id` stamped; on/off audited | P/F |
| FT-DATACLASS | deterministic derivation + loud conflict | R34 | 21,1 | ci | `data_class` | an untagged resource resolves; a conflict fails loudly | P/F |

### S12 — Enrollment/probation & approval analytics (R35, R36; CUJ-22,23)

| ID | Capability | PRD/ticket | CUJ | Env | Driver | Pass condition | Class |
|---|---|---|---|---|---|---|---|
| FT-ENROLL | first-seen agent → probation | R35 | 22 | ci | engine | first write → `ask`, `agent_probation`; classification logged | P/F |
| FT-APPROVALS | rubber-stamp + always-allowed patterns | R36, R47 | 23,33 | ci | `report approvals` | an always-approved gate is flagged; allow-side patterns surfaced | P/F |

### S13 — Nearest-permissible-action & multi-agent governance (R37, R39; CUJ-24,28)

| ID | Capability | PRD/ticket | CUJ | Env | Driver | Pass condition | Class |
|---|---|---|---|---|---|---|---|
| FT-ALT | verified-permissible alternatives | R37 | 24 | ci | `explain` | each alternative is evaluated-true; no policy internals leak | P/F |
| FT-DELEGATION | delegation-chain scope-subset | R39, R25 | 28 | ci | engine | a child's out-of-scope action denied naming the chain link | P/F |
| FT-INTERAGENT | an agent→agent request is decided | R39 | 28 | ci | `Engine.inter_agent` | decided like any action; same determinism | P/F |

### S14 — NL policy drafting (R42; CUJ-27)

| ID | Capability | PRD/ticket | CUJ | Env | Driver | Pass condition | Class |
|---|---|---|---|---|---|---|---|
| FT-DRAFT | sentence → candidate Cedar rule | R42 | 27 | ci | `draft` | compiles, passes generated tests + lint, waits for review | P/F |
| FT-DRAFT-LOCK | boundary lock | R42 | 27 | ci | pytest | the runtime decision path never calls a model | P/F |

### S15 — Policy backtest & PR decision-diff (R43; CUJ-29)

| ID | Capability | PRD/ticket | CUJ | Env | Driver | Pass condition | Class |
|---|---|---|---|---|---|---|---|
| FT-BACKTEST | exact flip set over recorded history | R43 | 29 | ci | `backtest` | newly-denied/asked/allowed exact + reproducible | P/F |
| FT-BACKTEST-RO | read-only + watermarked + advisory | R43 | 29 | ci | `backtest` | no fleet events; `--ci` exits 0; window + limits stated | P/F |

### S16 — Framework adapters & harness compatibility (R28, R19; CUJ-2,14,16)

| ID | Capability | PRD/ticket | CUJ | Env | Driver | Pass condition | Class |
|---|---|---|---|---|---|---|---|
| FT-FWK-LG | LangGraph adapter end to end | R28, PRD 19 T2 | 2 | vend,llm | `run_field_agents.py` | a real LangGraph agent surfaces each decision type | P/F\|D |
| FT-FWK-PAI | PydanticAI adapter | R28 | 2 | vend,llm | `run_field_agents.py` | each decision type surfaced in a live loop | P/F\|D |
| FT-FWK-CREW | CrewAI adapter | R28 | 2 | vend,llm | `run_field_agents.py` | each decision type surfaced | P/F\|D |
| FT-FWK-OAI | OpenAI Agents SDK adapter | R28 | 2 | vend,llm | `run_field_agents.py` | each decision type surfaced | P/F\|D |
| FT-FWK-AG2 | AutoGen / AG2 adapter | R28 | 2 | vend,llm | `run_field_agents.py` | each decision type surfaced | P/F\|D |
| FT-FWK-SMOL | smolagents adapter | R28 | 2 | vend,llm | `run_field_agents.py` | each decision type surfaced | P/F\|D |
| FT-FWK-LI | LlamaIndex adapter | R28 | 2 | vend,llm | `run_field_agents.py` | each decision type surfaced | P/F\|D |
| FT-FWK-ADK | Google ADK adapter | R28 | 2 | vend,llm | `run_field_agents.py` | each decision type surfaced | P/F\|D |
| FT-FWK-SWE | SWE-bench self-test adapter | R28 (delegated) | 2 | ci | `run_field_agents.py` | deterministic self-test, no LLM | P/F |
| FT-FWK-MCP | agentpolicy-MCP self-test | R28 | 14 | ci | `run_field_agents.py` | deterministic self-test, no LLM | P/F |
| FT-REPLAN | deny → different tool → allow | R37, R30 | 4,24 | ci | `field-test --replan scripted` | the replacement call is allowed; both in the audit trace | P/F |

> **Covering design (PRD 19 honest coverage):** 10 frameworks × 10 agents = 100 agents. The full cross product
> (2,490 cells) is **overkill** — the engine is framework-agnostic and its correctness is proven by L0. The live
> sweep uses **Plan A** (one scenario per agent; all scenarios/agents/frameworks covered, ~83 runs) and **Plan B**
> (each framework individually proves allow/audit/escalate/deny + one adversarial, ~123 runs) via
> `scripts/run_field_agents.py --plan A|B`. The `vend`+`llm` cases are `P/F|D`: where a vendored repo or OMLX is
> absent, they are **declared** with the CI leg (agent-build smoke + deterministic matrix) as evidence, never
> silently skipped.

### S17 — NFRs, hardening, parity & deferred (R8, R32, PRD 06/10/13)

| ID | Capability | PRD/ticket | CUJ | Env | Driver | Pass condition | Class |
|---|---|---|---|---|---|---|---|
| FT-NFR-LATENCY | sub-100 ms p99 | R8 | 1 | ci | `nfr` | engine p99 < 100 ms over a warm run | P/F |
| FT-NFR-PORT | Python 3.10+, macOS/Linux, local-first | R8, NFR | 1 | mac,lin | `nfr` | supported python/platform; in-process decision | P/F |
| FT-FAILCLOSED | fault injection at every stage | R8, CUJ-9 | 9 | ci | `faultinject` | every injected fault → a reasoned `deny`, never an abort | P/F |
| FT-SANDBOX | untrusted-pack sandbox | PRD 06 | — | ci | `sandbox` | env stripped; trust levels enforced; `--network none` | P/F |
| FT-COST | `--max-cost` budget governor | R8, PRD 13 | — | ci | `cost` | the run aborts + reports over the ceiling | P/F |
| FT-PARITY | absorption ledger, no silent drops | PRD 10 | — | ci | `parity` | `parity_gate()` empty | P/F |
| FT-DEFER | deferred-optional implemented/waived | R13/R14/R31 | — | ci | `deferred` | every item implemented or waived **with a reason** | P/F |
| FT-DOCTOR | environment/policy sanity | R8, NFR | 1 | ci | `doctor` | reports env/policy readiness | P/F |

### S18 — Tier-1 coding-agent harnesses (WBS `24.3`, PRD 19 Tier-1; CUJ-2,16)

> PRD 19: "all 5 Tier-1 harnesses are reachable at v0.1.0 through some enforcement point; **≥2 are exercised
> end-to-end** in the field test. Copilot's closed hook surface is covered at a lower layer and documented
> honestly." These cases are that exercise — the harness calls agentpolicy through its **native** hook/config
> surface, and the decision must surface **inside the harness's own loop** (DD-11: a deny must not surface as a
> protocol crash).

| ID | Capability | PRD/ticket | CUJ | Env | Driver | Pass condition | Class |
|---|---|---|---|---|---|---|---|
| FT-T1-CLAUDE | Claude Code `PreToolUse` hook → `agentpolicy evaluate` | R28, PRD 19 | 2 | t1 | Claude Code hook | a denied call returns a structured, model-consumable rejection the agent replans around; an `ask` pauses the loop; every decision emits an audit entry | P/F\|D |
| FT-T1-CURSOR | Cursor `permissions.json` compiled by policyweave from `agentpolicy export` | R2, PRD 19 | 2,16 | t1 | `export` → policyweave | the compiled artifact governs Cursor; drift between the Cedar source and the compiled format is flagged | P/F\|D |
| FT-T1-CODEX | Codex CLI config/hook surface → `agentpolicy evaluate` / agentgate | R28, PRD 19 | 2 | t1 | Codex config + CLI | a governed call is decided pre-execution; a deny surfaces as a structured rejection | P/F\|D |
| FT-T1-GEMINI | Gemini CLI config/hook surface (MCP-native via agentgate) | R28, PRD 19 | 2,14 | t1 | Gemini config + MCP | same decision as the in-process path for the same call | P/F\|D |

**Tier-1 coverage rule (PRD 19):** **≥2 of the 4 must be exercised end-to-end** on the box (Class `P/F` once
exercised); the remainder may be **declared** with the lower-layer coverage named (agentseatbelt/agentgate) and
the reachability documented — the release compatibility table states honest coverage, per PRD 19 and DD-30.
GitHub Copilot (the 5th Tier-1) has a closed hook surface; it is covered at the confinement layer
(agentseatbelt) and **documented as such — never claimed as field-exercised**.

**Totals:** 30 predecessor scenarios (Layer 0) + **96 new cases** across S1–S18, of which the `P/F|D` declare
class is 14 (the 8 live-framework legs + the 4 Tier-1 legs + the 2 Docker legs) — and of those 14, **≥2 Tier-1
and ≥3 framework adapters must be *exercised* end-to-end** (declared, not skipped, where the box lacks them).
Every CUJ-1…CUJ-33 is covered (§8); every R1–R47 (§16).

---

## 7. Detailed case specifications

Each case follows the harness lifecycle and gives **Goal · Preconditions · Steps · Assertions · Artifacts ·
Fallback**. Assertions are machine-checkable (`FieldTestRunner` per-cell expectations + the CLI exit codes);
**pass = all assertions true**. A missing prerequisite fails the case (or declares, for a `P/F|D` case). The
flagship and novel-mechanics cases are specified in full; the remainder follow the same template and are frozen in
the matrix and in `scenarios.yaml`.

### 7.1 S1 — Five outcomes

- **FT-DEC-ASK — the human gate (flagship).** Goal: prove a prod write resolves to `ask`, not `deny`/`allow`.
  Preconditions: the field policy + the mandatory human-gate class (`cedar.gates`). Steps: evaluate
  `deploy_service/write/production`; capture the decision. Assertions: `decision == "ask"`,
  `reason_code == "human_gate_required"`, an `ask_id` is minted, the gate class is the single source of truth
  (`is_human_gate`). Artifacts: decision JSON. Fallback: none (hard gate).
- **FT-DEC-RATE / FT-DEC-REDACT — the new outcomes (flagship).** Steps: drive a session past its send budget
  (`rate-limit`) and read a secret-bearing tool output (`redact`). Assertions: `rate-limit` carries `retry_after`;
  `redact` carries a class/count/location receipt; neither silently downgrades to `allow`. Artifacts: decision +
  budget state + receipt.
- **FT-DEC-DETERMINISM.** Steps: evaluate the same call 1000×. Assertions: byte-identical decisions; no network
  syscall in the path (fault-injected network probe).

### 7.2 S2 — Explain / evidence / audit

- **FT-EXPLAIN-ACTIONABLE (flagship).** Steps: take 20 denies; give a human **only** the explanation text + the
  original action. Assertions: for each, the one change that flips the outcome (approve / move to staging / lower
  data class / reduce scope) is derivable without docs — the acceptance test is automated, not a vibe.
- **FT-EVENT-BIND + FT-AUDIT-CHAIN + FT-EVIDENCE-OFFLINE.** Steps: emit a decision event, append a chained audit
  entry, then verify offline. Assertions: `event_id == decision_id` join; the chain verifies on a clean log and a
  mutated entry names the first broken link; the evidence artifact re-derives the decision against the pinned
  policy on a machine without agentpolicy.

### 7.3 S3 — Packs & self-attack

- **FT-SELF-ATTACK (flagship, R46).** Steps: `agentpolicy self-attack check --pack packs/self-attack`; then swap
  in a seeded-miss pack. Assertions: the shipped pack reports zero misses (all six attack classes blocked, the
  benign control fixture still allowed); the seeded miss exits **1** and is named. Artifacts: the pack result,
  published with the release, misses included.
- **FT-DRILL + FT-GOLDEN-FLIP.** Steps: un-block an incident replay / flip a golden `deny→allow`. Assertions:
  each fails the build with the exact clause + fixture; deterministic.

### 7.4 S4 — Posture / lint / layering / coverage

- **FT-LAYER-NARROW (flagship, R44).** Steps: `agentpolicy check project.yaml --parent org.yaml` where the
  project adds an `allow` not backed by the org. Assertions: exit **2**, naming the widening rule; a narrowing
  child passes; composition is the intersection (a deny in any layer wins). Artifacts: the violation list.
- **FT-COVERAGE (flagship, R45).** Steps: `agentpolicy report coverage --inventory <window>`. Assertions: the
  exercised-but-uncovered quadrant is named loudly, dead rules listed, `gap:unexplained == 0` over the corpus
  (every dangerous verb covered or declared out-of-scope).

### 7.5 S8 — Human gates

- **FT-ASK-ROUNDTRIP + FT-ASK-BINDING (flagship, R18).** Steps: an `ask`, then `agentpolicy approve <ask_id>`,
  then resolve; then replay the approval for a different call. Assertions: approved → allow with the approver
  audited; a replay with different args → `deny_action_identity_mismatch`; timeout → deny.
- **FT-DUALCONTROL (flagship, R41).** Steps: `ask` an irreversible call; approve once, then with the same
  principal, then with a second distinct approver. Assertions: one approval does not release; the same principal
  is rejected; two distinct approve; the quorum is audited.
- **FT-BREAKGLASS (flagship, R40).** Steps: elevate with a reason, act, wait past the TTL. Assertions: every
  decision in the window carries `break_glass_id`; the revert is automatic and logged; a dual-control action still
  requires its quorum inside the window.

### 7.6 S16 — Live frameworks

- **FT-FWK-\<framework\> (flagship, R28).** Steps: `scripts/download_field_agents.sh <repo>`;
  `uv run python scripts/run_field_agents.py <framework> --plan B`. Assertions: every scenario tool call is
  intercepted by the guard; the decision matches the golden; each framework individually surfaces
  allow/audit/escalate/deny + one adversarial; `llm_called_ok` on every LLM row. Fallback (repo or OMLX absent):
  **declare** with the CI agent-build smoke + deterministic matrix as evidence.
- **FT-REPLAN.** Steps: `agentpolicy field-test --replan scripted` (LLM-free) and, where OMLX exists,
  `--replan live`. Assertions: a denied call → a different admissible tool → allow; both calls in the audit trace.

### 7.7 S18 — Tier-1 harnesses

- **FT-T1-CLAUDE — Claude Code `PreToolUse` (flagship).** Goal: prove a Tier-1 harness calls agentpolicy through
  its **native** hook surface and the decision surfaces inside the agent loop. Preconditions: Claude Code on the
  box; the hook wired to `agentpolicy evaluate`. Steps: run a benign read (allow), a prod write (ask), a
  destructive call (deny). Assertions: allow executes; **ask pauses the loop** (not a crash); deny returns a
  **structured, model-consumable rejection** the agent replans around (DD-11); every decision emits an audit
  entry. Artifacts: the harness transcript + audit trail. Fallback (no Claude Code on the box): **declare** with
  the reachability doc (agentgate/agentseatbelt lower-layer coverage) + the CI deterministic matrix as evidence.
- **FT-T1-CURSOR — policyweave compile-out (flagship, CUJ-16).** Steps: `agentpolicy export` → policyweave →
  `permissions.json`; run a governed + a denied call under Cursor. Assertions: the compiled artifact governs;
  **drift between the Cedar source and the compiled format is flagged**; the same call yields the same decision
  as the in-process path. Fallback: declare with the export artifact as evidence.
- **FT-T1-CODEX / FT-T1-GEMINI.** Steps: wire the Codex/Gemini config or MCP surface (via agentgate) to
  `agentpolicy evaluate`; run the same three-call triple. Assertions: same decision as the in-process path
  (parity); deny surfaces as a structured rejection. Fallback: declare with the lower-layer coverage named.

---

## 8. CUJ coverage matrix (CUJ-1…CUJ-33)

Every CUJ is proven end to end by ≥1 case; flagship journeys map to several. No CUJ is left without a case.

| CUJ | Journey | Proving cases |
|---|---|---|
| CUJ-1 | Evaluate one action (five outcomes) | FT-DEC-ALLOW/DENY/ASK/RATE/REDACT/UNKNOWN, FT-DEC-CONTEXT |
| CUJ-2 | Wire into a harness/enforcer | FT-SURFACE-PARITY, FT-ADAPTERS, FT-FWK-LG/PAI, FT-T1-CLAUDE/CURSOR/CODEX, FT-DOCKER-SMOKE |
| CUJ-3 | Understand *why* | FT-EXPLAIN-CLAUSE, FT-EXPLAIN-ACTIONABLE |
| CUJ-4 | Adopt in shadow mode | FT-SHADOW, FT-CALIBRATION, FT-CANARY, FT-REPLAN |
| CUJ-5 | Extend with a rule pack | FT-PACK-LAUNCH, FT-PACK-VALIDATE |
| CUJ-6 | Prove compliance | FT-EVENT-BIND, FT-AUDIT-PROVENANCE, FT-COMPLIANCE-MATRIX, FT-VERIFY |
| CUJ-7 | Gate a policy PR | FT-GOLDEN-FLIP, FT-DRILL, FT-PACK-LAUNCH |
| CUJ-8 | Customize the posture | FT-POSTURE, FT-INIT, FT-DIFF, FT-HIDING |
| CUJ-9 | Degraded & failure modes | FT-FAILCLOSED, FT-DEC-UNKNOWN |
| CUJ-10 | Ask round-trip | FT-ASK-ROUNDTRIP, FT-ASK-TIMEOUT, FT-ASK-BINDING |
| CUJ-11 | Adversarial resilience | FT-NORM-OBFUSCATION, FT-DISPATCHER, FT-ADV-REPLAY/FLOOD, FT-DENYSTORM, FT-ARG-VALIDATE, FT-HTTP-GUARD |
| CUJ-12 | Budget the blast radius | FT-BUDGET-EXHAUST, FT-BUDGET-STATE, FT-HALT |
| CUJ-13 | Block an exfil chain | FT-EXFIL-SINK |
| CUJ-14 | Ask the gate from anywhere | FT-AUTHZEN, FT-MCP-ASK, FT-SURFACE-PARITY, FT-T1-GEMINI |
| CUJ-15 | Redact a secret | FT-DEC-REDACT, FT-REDACT-RECEIPT, FT-ARG-SECRET |
| CUJ-16 | Compile one policy everywhere | FT-EXPORT, FT-T1-CURSOR (policyweave compile-out) |
| CUJ-17 | Lint the policy | FT-LINT |
| CUJ-18 | Rate-limit a runaway | FT-BUDGET-RETRY, FT-BUDGET-BURST |
| CUJ-19 | Step-up on scope escalation | FT-STEPUP, FT-SCOPE |
| CUJ-20 | Verify a decision offline | FT-EVIDENCE-OFFLINE, FT-AUDIT-CHAIN |
| CUJ-21 | Declare a change freeze | FT-FREEZE, FT-DATACLASS |
| CUJ-22 | Enroll an unknown agent | FT-ENROLL |
| CUJ-23 | Find the rubber-stamp gates | FT-APPROVALS |
| CUJ-24 | Get a denial I can act on | FT-ALT, FT-EXPLAIN-ACTIONABLE |
| CUJ-25 | Break glass without breaking trust | FT-BREAKGLASS |
| CUJ-26 | Two humans for the irreversible class | FT-DUALCONTROL |
| CUJ-27 | Draft a policy from a sentence | FT-DRAFT, FT-DRAFT-LOCK |
| CUJ-28 | Delegate without leaking scope | FT-DELEGATION, FT-INTERAGENT |
| CUJ-29 | Backtest a policy change | FT-BACKTEST, FT-BACKTEST-RO |
| CUJ-30 | Guarantee the floor | FT-LAYER-NARROW |
| CUJ-31 | See the uncovered action space | FT-COVERAGE |
| CUJ-32 | Verify agentpolicy against itself | FT-SELF-ATTACK |
| CUJ-33 | Justify an allow | FT-ALLOW-JUSTIFY, FT-APPROVALS |

A `declared` outcome for a `P/F|D` case still names its CUJ in the report with the limitation (PRD 19).

---

## 9. Harness work (M24 items)

Extend the existing harness — do **not** fork it.

1. **Harness (`24.1`, #256).** Confirm `agentpolicy field-test` boots L0/L1/L2 with no Docker and exits non-zero on
   any miss; record a per-run environment fingerprint (OS/arch, python, policy version+hash, OMLX model,
   vendored repo SHAs, Tier-1 harness versions). Existing: `FieldTestRunner`, `scripts/run_field_agents.py`.
   **Add:** a `--core cedar` mode for the field runner so the matrix can also drive the Cedar five-outcome path
   natively (the L1 acceptance-matrix/pack-replay drivers remain the proof of record).
2. **Scenario matrix (`24.2`, #257).** Append the S1–S18 scenarios to `tests/field/scenarios.yaml` (and the
   L1/Tier-1 drivers for the CLI/server/harness cases); every outcome (allow/deny/ask/rate-limit/redact) +
   fail-closed + replan is exercised. Predecessor 30 scenarios are retained verbatim.
3. **Framework + Tier-1 coverage (`24.3`, #258).** Prove **≥2 Tier-1 harnesses exercised end-to-end** through
   their native hook/config surfaces (§S18) **and ≥3 framework adapters** in their native loops (§S16, PRD 19);
   the roster is 10 frameworks × 10 agents; Copilot documented as lower-layer covered, never claimed.
4. **Adversarial + self-attack (`24.4`, #259).** Run the adversarial sub-matrix and `self-attack check` in the
   field run; every attempt blocks.
5. **Report (`24.5`, #260).** Publish `docs/field-test/v0.1.0/FIELD_TEST_REPORT.md` — scenarios × frameworks ×
   expected/actual; misses named; an **empty not-tested list**.
6. **Fix loop (`24.6`, #261).** Every harness defect → fixed with a regression test; 0 open product defects.

**Fixtures.** The vendored framework repos (`scripts/download_field_agents.sh`, gitignored) + the deterministic
fixture corpora (goldens, packs, swe-bench tasks, ask/escalation stores).

---

## 10. Results

```
tests/field/results/<framework>/<agent_id>.json     # per-agent rows: scenario × decision × expected/status/passed
tests/field/results/replan/{scripted,live}.json     # the replan round-trip
docs/field-test/v0.1.0/FIELD_TEST_REPORT.md         # the published report
```

Each row records `scenario_id`, `tool`, `action`, `environment`, `data_class`, `called`, `decision`,
`reason_code`, `expected`, `status` (`ok` | `no-call` | `no-llm-response` | `unexpected-decision` |
`not-available` | `exception`), `passed`, and `mismatches`. A `declared` row carries `declared` + `limitation` +
the release-gate item.

---

## 11. Execution

```bash
make setup
uv sync --group dev

# Layer 0 + L1 — deterministic engine matrix (no LLM, no Docker)
uv run agentpolicy field-test --agents all --matrix both --report none

# L1/L2 — the five-outcome + feature cases (fixture-backed)
uv run agentpolicy field-test --matrix both            # writes docs/field-test/field-test-report-v1.md by default
uv run agentpolicy goldens check && uv run agentpolicy drill check
uv run agentpolicy self-attack check --pack packs/self-attack
uv run agentpolicy compliance export > /dev/null && uv run agentpolicy compliance claims

# replan round-trip (LLM-free in CI)
uv run agentpolicy field-test --replan scripted --report none

# L3 — live frameworks (where vendored repos + OMLX exist)
./scripts/download_field_agents.sh
uv run python scripts/run_field_agents.py langgraph  --plan B
# … pydanticai crewai openai-agents autogen smolagents llamaindex adk swebench agentpolicy-mcp

# L3b — Tier-1 harnesses (≥2 of 4 exercised end-to-end; rest declared with lower-layer coverage named)
# Claude Code: PreToolUse hook → `agentpolicy evaluate`; Cursor: `agentpolicy export` → policyweave → permissions.json
# Codex / Gemini CLI: config/hook or MCP surface via agentgate

# docker legs (optional)
make docker-test        # smoke + SSE
```

**CI mapping (`.github/workflows/ci.yml` `field-test` job):** deterministic decision + adversarial matrix
(LLM-free) → agent-build smoke (`pytest -m field`) → scripted replan → committed-results status whitelist. The
live framework sweep runs where OMLX + vendored repos are present; absent → `declared` with the CI leg as
evidence. **M24 issue mapping:** plan #255 · harness #256 · matrix #257 · frameworks #258 · adversarial/self-attack
#259 · report #260 · fix loop #261 · gates #262–#266.

---

## 12. Gates, release-gate mapping & honesty

- A case passes only on explicit assertions; anything else is a failure. `declared` is reserved for the `P/F|D`
  cases and only where PRD 19's honest-coverage rule permits it; it needs evidence + a known-limitations line.
- **PRD 07 release-gate mapping:** (1) five outcomes → FT-DEC-*; (2) launch packs → FT-PACK-LAUNCH; (3) actionable
  denies → FT-EXPLAIN-ACTIONABLE; (4) agentwatch schema → FT-EVENT-BIND; (5) git/review → FT-AUDIT-PROVENANCE;
  (6) p99 + fail-closed → FT-NFR-LATENCY + FT-FAILCLOSED; (7) CI rejects a golden flip → FT-GOLDEN-FLIP; (8)
  adversarial sub-matrix zero crafted allows → FT-ADV-*; (9) compatibility table → §S16 + §S18 + report; (10)
  security baseline matrix → FT-COMPLIANCE-MATRIX; (11) CUJ-8 afternoon → FT-INIT/FT-POSTURE + the user test.
- **Parity closure (PRD 10):** FT-PARITY is green (no silent drops); the report carries the parity ledger status.
- **Self-attack (PRD 06 / R46):** FT-SELF-ATTACK runs every release; a miss is release-blocking; the result is
  published with the release notes, misses included.
- **Defects (M24.6):** every field-test defect is fixed with its own regression test; the report records
  root-cause analysis.
- **Do not claim a gate passed unless it was run on the merged HEAD.** A `declared` case is never reported as
  "done".

---

## 13. Report template (`docs/field-test/v0.1.0/FIELD_TEST_REPORT.md`)

1. BLUF + release-gate verdict (the PRD 07 gate items).
2. Environment (per-layer fingerprints; policy version+hash; models; vendored repo SHAs).
3. What was tested (Layer 0 predecessor regression + the 96 v0.1.0 cases + the live/Tier-1 sweep).
4. **Scenario Results (master table)** — every case with `pass|fail|declared` + evidence path.
5. Per-group results (S1–S18) and per-framework / per-harness pass rates.
6. **CUJ-1…CUJ-33 verification table** (from §8).
7. Root-cause analysis for every defect (fix + regression evidence).
8. Coverage & gaps; the `declared` register (named limitation + release-gate item).
9. **Observations · Learnings · Takeaways.**
10. Parity-ledger status + self-attack result (misses included).
11. Evidence paths + reproduce commands.

---

## 14. Out of scope (declared) & limitations

Enforcement, detection/classification, runtime isolation, credential issuance, telemetry storage, and compliance
certification remain out of scope (PRD 14; the enforcers own them). The `P/F|D` cases (live frameworks, Tier-1
harnesses, Docker/MCP legs) declare a named limitation when their environment is absent — never a silent
skip. OMLX-backed adapters, Tier-1 harnesses, and Docker legs are the only declared-environment surfaces; every
case in §S1–S15 and §S17 is deterministic and must pass.

---

## 15. Rollout

1. Confirm the harness (§9.1) and append the S1–S18 scenarios to `scenarios.yaml` (§9.2).
2. Run **Layer 0** (predecessor regression) to green — no v0.1.0 case is evaluated before this.
3. Run S1–S8 (outcomes/explain/packs/posture/shadow/budgets/data/ask), then S9–S18
   (surfaces/normalization/freeze/enroll/alt/draft/backtest/frameworks/NFRs/Tier-1).
4. Fix defects with regressions (§9.6); confirm the CI `field-test` job.
5. Publish the report (§9.5); close #255–#266; record the M24 checkpoint in the WBS index.

---

## 16. Appendix — requirement coverage index (R1–R47)

Every requirement is proven by ≥1 case (PRD 12 traceability, completed by the field run).

| Req | Proving case(s) | Req | Proving case(s) |
|---|---|---|---|
| R1 five outcomes | FT-DEC-* | R25 child delegation | FT-DELEGATION |
| R2 Cedar + OPA import | FT-POSTURE, FT-PACK-VALIDATE, FT-EXPORT (OPA/Rego suite-covered: `test_opa.py`) | R26 adversarial suite | FT-ADV-*, FT-DENYSTORM |
| R3 launch packs | FT-PACK-LAUNCH | R27 AuthZEN interop | FT-AUTHZEN |
| R4 human-gate class | FT-DEC-ASK | R28 delivery surfaces | FT-SURFACE-PARITY, FT-FWK-* |
| R5 explain-decision | FT-EXPLAIN-* | R29 pack catalog | FT-PACK-VALIDATE |
| R6 agentwatch events | FT-EVENT-BIND, FT-VERIFY | R30 shadow/calibration/canary | FT-SHADOW, FT-CALIBRATION, FT-CANARY |
| R7 versioned policies | FT-AUDIT-PROVENANCE, FT-AUDIT-CHAIN | R31 fleet sync (deferred) | FT-DEFER |
| R8 local-first/fail-closed | FT-NFR-*, FT-FAILCLOSED | R32 compliance export | FT-COMPLIANCE-MATRIX |
| R9 blast-radius budgets | FT-BUDGET-EXHAUST, FT-HALT | R33 freeze windows | FT-FREEZE |
| R10 exfil-sink | FT-EXFIL-SINK, FT-HTTP-GUARD | R34 data-class derivation | FT-DATACLASS |
| R11 scope-escalation + step-up | FT-SCOPE, FT-STEPUP | R35 enrollment + probation | FT-ENROLL |
| R12 rule-pack lint | FT-LINT | R36 approval analytics | FT-APPROVALS |
| R13 OPA→Cedar migration (deferred) | FT-DEFER | R37 nearest-permissible-action | FT-ALT |
| R14 marketplace (deferred) | FT-DEFER | R38 secrets-in-args | FT-ARG-SECRET |
| R15 contextual model | FT-DEC-CONTEXT | R39 multi-agent governance | FT-DELEGATION, FT-INTERAGENT |
| R16 posture + init | FT-POSTURE, FT-INIT, FT-DIFF | R40 break-glass | FT-BREAKGLASS |
| R17 session state | FT-BUDGET-STATE | R41 dual-control | FT-DUALCONTROL |
| R18 ask round-trip | FT-ASK-* | R42 NL drafting | FT-DRAFT, FT-DRAFT-LOCK |
| R19 argument validation | FT-ARG-VALIDATE, FT-HTTP-GUARD | R43 backtest + PR diff | FT-BACKTEST, FT-BACKTEST-RO |
| R20 redact-and-allow | FT-DEC-REDACT, FT-REDACT-RECEIPT | R44 narrow-only layering | FT-LAYER-NARROW |
| R21 tool hiding | FT-HIDING | R45 coverage report | FT-COVERAGE |
| R22 CI regression suite | FT-GOLDEN-FLIP, FT-DRILL | R46 self-attack pack | FT-SELF-ATTACK |
| R23 rate/burst + retry_after | FT-BUDGET-RETRY, FT-BUDGET-BURST | R47 allow-justification | FT-ALLOW-JUSTIFY |
| R24 dispatcher safety | FT-NORM-OBFUSCATION, FT-DISPATCHER | | |

**Totals: 30 predecessor scenarios + 96 v0.1.0 cases (§6); every R1–R47 and CUJ-1…CUJ-33 appears in ≥1 case.** No
requirement or journey is covered only "in spirit".
