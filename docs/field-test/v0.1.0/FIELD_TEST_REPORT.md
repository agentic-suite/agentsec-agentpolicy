<!-- HAND-MAINTAINED DOCUMENT — edit by hand only.
     Do NOT regenerate or overwrite this file with scripts/fieldtest/build_report.py.
     That script refuses to touch a file carrying this marker (see build_report.py).
     A lossy automated rewrite of this report has destroyed notes before; never again. -->

# agentpolicy v0.1.0 — Field Test Report

> **Status: IN PROGRESS (partial run).** This is a **hand-maintained** journal, updated as the sweep runs — not a
> generated scoreboard. Counts here are read from the committed `field-test/v0.1.0/results/` verdicts and written
> by hand; nothing is auto-overwritten.
> **Current:** **76 ✅ PASS · 3 ❌ FAIL · 4 ◆ declared · 16 ▫ not run** (of 99 field units). The deterministic
> matrix ran green (**2,988/2,988 cells, 36 scenarios × 83 agents**); the remaining suites are being finished in
> **small groups** — each run → deep-verified → fixed → journaled (§Small-Group Run Journal).
> **Structure:** follows the format of `agentdrill`/`agentwatch` v0.2.0 `FIELD_TEST_REPORT.md` (a journal, not a
> scoreboard), pointed at [FIELD_TEST_PLAN.md](FIELD_TEST_PLAN.md) §6 (matrix), §8 (CUJ map), §12 (release gate),
> §16 (R-map). This report states **honestly** what was tested, what passed, and what was **not** run.

---

## BLUF + Release Gate Verdict

> **76 PASS · 3 FAIL · 4 declared · 16 not run (of 99).** The harness, the Docker setup, the deep-verification
> gate, and the case matrix are **ready and exercised** (§What Was Tested); the suite is being finished in
> **small groups** — each group is run, **deep-verified**, fixed, and journaled (§Small-Group Run Journal).
> The **OMLX model choice is benchmarked and applied** (§OMLX LLM Benchmark). No case is deleted, skipped, or
> optimistically marked — a case without a verdict reads **`not run`**, and a PASS without a re-derived
> assertion is not counted as grounded.

### Run status (groups in progress; 83/99 verdicts on disk)

| | Count |
|---|---|
| PASS (raw verdict) | 76 |
| — of which grounded (asserting check re-derived, not exit-0) | 76 |
| FAIL | **3** (s16 live frameworks — §Small-Group Run Journal) |
| declared (P/F\|D, environment cannot provide — named) | 4 |
| not run | 16 (s16 remainder + s17 NFR) |
| N/A (retired) | 0 |

### Release gate verdict (PRD 07 items; filled as the sweep runs)

| # | Gate (PRD 07 §release gate) | Status | Evidence / honesty |
|---|---|---|---|
| 1 | Five outcomes demonstrable (allow/deny/ask/rate-limit/redact) | ◑ | Cedar matrix scenarios (`cedar-allow/ask/redact/deny/ratelimit`) pass in the deterministic run; the per-outcome cases (FT-DEC-*) are wired, pending the full sweep |
| 2 | 3 launch packs block their incident | ▫ pending | FT-PACK-LAUNCH wired |
| 3 | Every deny explainable + actionable | ◑ | FT-EXPLAIN-ACTIONABLE ✅ PASS (grounded); FT-EXPLAIN-CLAUSE pending |
| 4 | Decisions in the agentwatch schema | ▫ pending | FT-EVENT-BIND wired |
| 5 | Policies git-reviewed; unreviewed change flagged | ▫ pending | FT-AUDIT-PROVENANCE wired |
| 6 | p99 < 100 ms + fail-closed on every path | ▫ pending | FT-NFR-LATENCY, FT-FAILCLOSED wired |
| 7 | CI rejects a golden deny→allow flip | ▫ pending | FT-GOLDEN-FLIP wired |
| 8 | Adversarial sub-matrix: zero crafted allows | ▫ pending | FT-ADV-* wired |
| 9 | Compatibility table published | ◑ | §S18 Tier-1 declared; §S16 live frameworks declared (no vendor repos) |
| 10 | Security baseline + coverage matrix | ▫ pending | FT-COMPLIANCE-MATRIX wired |
| 11 | Non-security engineer completes CUJ-8 in an afternoon | ▫ pending | user test |

---

## Small-Group Run Journal

Work is done in **small groups** (by suite). Each group: **run → deep-verify → fix → journal**, then pause.
A group is listed here only once **every** case in it has run; any failing case is fixed before the group closes.
Deep verification = `check_grounding.py` re-derives each asserting check from the emitted decision (a PASS that
is not grounded is not counted) + `scan_results.py` leak scan.

### Group 1 — `s1-outcomes` (five-outcome decision core) — **8/8 ✅ PASS, deep-verified** (2026-11-01)
- **Run:** `bash scripts/fieldtest/run-suite.sh s1-outcomes` → exit 0; **8/8 cases pass**.
- **Deep verification:** *every PASS is grounded* (each asserting check re-derived, not exit-0); leak scan
  **clean**; every verdict `grounded=true`, `assertions 1/1` grounded.
- **Findings:** the five PRD outcomes (allow / deny / ask / rate-limit / redact) plus fail-closed on an unknown
  verdict, context binding, and determinism all behave as specified. **No defects found.**
- **What I fixed:** nothing — the group was green on its first run.
- **Working:** `FT-DEC-ALLOW/DENY/ASK/RATE/REDACT/UNKNOWN/CONTEXT/DETERMINISM` — all grounded, all pass.
- **Not working:** nothing in this group.
- **Captured evidence:** `field-test/v0.1.0/results/s1-outcomes/cases/FT-DEC-*/` (`verdict.json`,
  `assertions.ndjson`, `commands.log`, `stdout/stderr`).

---

## Environment

| Item | Value |
|---|---|
| Host | macOS `Darwin` arm64 |
| Python | 3.13 (repo `.venv`) |
| Docker / Compose | available (field image `agentpolicy-fieldtest:local` builds; stack reaches `healthy`) |
| OMLX endpoint | `http://127.0.0.1:8000/v1` (host) · `http://host.docker.internal:8000/v1` (container) |
| OMLX models served | `Qwen3-4B-Instruct-2507-4bit` · `Qwen3.5-4B-4bit` · `mlx-community--Qwen3.5-4B-4bit` · `Qwen3.5-9B-MLX-4bit` · `Qwen3-8B-4bit` · `Llama-3.2-3B-Instruct-4bit` · `MarkItDown` |
| **Field-test LLM (pinned)** | **`Qwen3-4B-Instruct-2507-4bit`** (§OMLX LLM Benchmark) |
| Results | `field-test/v0.1.0/results/<suite>/` (verdict.json, assertions.ndjson, commands.log, stdout/stderr, artifacts/) |
| Harness | `scripts/fieldtest/` (runner, generator, gates) — see §Reproducibility |

Recorded per run in `field-test/v0.1.0/results/env.json`.

---

## OMLX LLM Benchmark — the model choice, and why

The live framework sweep (`scripts/run_field_agents.py`) drives a **real agent** whose only job is to emit a
**tool call** for a scenario tool (`scn_<id>`). The decision itself is **always** made by the deterministic
engine — the LLM is an oracle, never the decider (DD-04). So the model is chosen on exactly two criteria:
**(1) tool-call reliability**, then **(2) latency**.

`scripts/fieldtest/omlx_bench.py` measures every model OMLX serves with a field-test-shaped request
(`tools=[scn_decision-allow-01]`, `tool_choice=auto`, `temperature=0`). Findings — **2026-11-01, this box,
3 trials**:

| OMLX model | tool calls | p50 latency | tps | verdict |
|---|---|---|---|---|
| **Qwen3-4B-Instruct-2507-4bit** | **3/3** | **~1.0 s** | 19.1 | ✅ **PINNED — best fit** |
| mlx-community--Qwen3.5-4B-4bit | 3/3 | ~6.6 s | 25.7 | ok (higher tps, ~7× slower at p50) |
| Qwen3.5-4B-4bit | 3/3 | ~6.8 s | 23.2 | ok |
| Qwen3.5-9B-MLX-4bit | 3/3 | ~12.9 s | 17.0 | slow |
| Qwen3-8B-4bit | 3/3 | ~27.5 s | 20.3 | too slow |
| Llama-3.2-3B-Instruct-4bit | **0/3** | ~0.8 s | 16.6 | ❌ **DISQUALIFIED** — never emits a tool call |

**Reasoning.**
- **Tool-call reliability is gating.** `Llama-3.2-3B-Instruct-4bit` is the *fastest* model (~0.8 s) but returned
  **zero tool calls in three trials** — useless for the sweep (the agent never invokes the guarded tool, so the
  guard never records a decision). Disqualified outright, however fast.
- **Then latency decides.** Among the reliable tool-callers, `Qwen3-4B-Instruct-2507-4bit` is **~7× faster at
  p50 than the Qwen3.5-4B pair** and **~27× faster than `Qwen3-8B-4bit`**. Over a Plan-A/B sweep that is the
  difference between minutes and ~an hour.
- **Provenance.** It is exactly agentdrill's (the predecessor field test's) primary pin — the same model, same
  role — so the choice is evidence-backed, not novel.
- **Caveat.** p50 includes full generation, so the 6–27 s figures largely reflect how much text those models emit
  before the call; the 4B-Instruct is both fast *and* tool-reliable.

**Applied.** `Qwen3-4B-Instruct-2507-4bit` is pinned in `scripts/fieldtest/.env.example`, `scripts/fieldtest/lib.sh`,
`scripts/fieldtest/docker-compose.fieldtest.yml`, `tests/field/agents/__init__.py`, and `src/agentpolicy/field/replan.py`.
Re-run `python3 scripts/fieldtest/omlx_bench.py` on a new box to re-derive. (`MarkItDown` is a document converter,
not an LLM; excluded.)

---

## What Was Tested

**Harness + Docker setup (M24.1) — done and exercised.**
- `scripts/fieldtest/` — `lib.sh` (per-case lifecycle + grounding), `run-case.sh` / `run-suite.sh` / `run-all.sh`,
  `stack-ft.sh`, `gen_cases.py` (registry → specs + steps), `collect-results.py`, `check_grounding.py`,
  `scan_results.py`, `run_pytest.py`, `verify_harness.py`, `build_report.py`, `llm_capture.py`, `omlx_bench.py`,
  `docker-compose.fieldtest.yml`, `agentpolicy.Dockerfile`.
- Docker SUT image builds; `stack-ft.sh up` reaches `healthy`; the CLI answers in-container.
- Per-run environment fingerprint (`env.json`), version-scoped results, freeze guard, gitignore for transient
  results.

**Deep verification — wired into the run, not a separate step.**
- Per case: `ft_finalize` fails a PASS with **no grounded assertion**; `run_pytest.py` treats **skip = no-tests = failure**.
- Per suite / per run: `run-suite.sh` and `run-all.sh` invoke `check_grounding.py` (re-derives grounding from
  disk) + `scan_results.py` (leak gate); `run-all.sh` runs `verify_harness.py` **first** (if the gate can't catch
  a shallow pass, the run aborts).
- `collect-results.py` counts an un-grounded PASS as **fail** (over-claimed).

**Deterministic matrix (Layer 0 + the five-outcome Cedar scenarios) — green.**
- `agentpolicy field-test --agents all --matrix both` = **2,988 cells → 2,905 pass / 83 → all fixed** (see RCA):
  the matrix includes 30 predecessor scenarios + 6 five-outcome Cedar scenarios (`ask`/`rate-limit`/`redact`/…) ×
  83 roster agents. **FT-REG-MATRIX ✅ PASS (grounded)**.

**Spot-verified cases (5).** FT-REG-MATRIX, FT-DEC-ASK, FT-EXPLAIN-ACTIONABLE, FT-SELF-ATTACK, FT-DOCKER-SMOKE
— all **PASS, grounded**; FT-T1-* (4 Tier-1) and FT-FWK-LG **declared**.

**Not yet run (honest): 89 cases** — the per-feature suites S1–S17 (outcomes, explain, packs, posture, shadow,
budgets, data, ask, surfaces, adversarial, freeze, enroll, multi-agent, draft, backtest, NFRs) await the full sweep
(`bash scripts/fieldtest/run-all.sh`).

**Declared (5):** the four Tier-1 harnesses (Claude Code / Cursor / Codex / Gemini — not installed on this box;
reachable via their hook/config surfaces, covered at the lower enforcer layer until exercised on a harness host)
and FT-FWK-LG (no vendored framework repo on this box; covered by the CI deterministic matrix + agent-build smoke).
Each names its limitation; none is a silent skip.

**Status vocabulary:** PASS | FAIL | declared | not run | N/A — plus qualifiers: **✓ grounded** (an asserting
check re-derived from disk), **⛔ open**, **DECLARED** (not run, named reason). A PASS that is not grounded is
treated as **not proven**.
**Class:** **P/F** = hard gate · **P/F\|D** = pass/fail-or-declare (a named declaration is acceptable; never a
silent skip).

---

## Scenario Results (Master Table)

99 field units (96 plan cases + 3 Layer-0 regression wrappers). Current verdicts below; the rest await the sweep.

| Case | Suite | Class | Status | Notes |
|---|---|---|---|---|
| FT-REG-ACCEPT | s0-regression | P/F | ✅ PASS | ✓ grounded |
| FT-REG-CLI | s0-regression | P/F | ✅ PASS | ✓ grounded |
| FT-REG-MATRIX | s0-regression | P/F | ✅ PASS | ✓ grounded — full 36×83 matrix (2,988 cells) |
| FT-DEC-ALLOW | s1-outcomes | P/F | ✅ PASS | ✓ grounded |
| FT-DEC-ASK | s1-outcomes | P/F | ✅ PASS | ✓ grounded |
| FT-DEC-CONTEXT | s1-outcomes | P/F | ✅ PASS | ✓ grounded |
| FT-DEC-DENY | s1-outcomes | P/F | ✅ PASS | ✓ grounded |
| FT-DEC-DETERMINISM | s1-outcomes | P/F | ✅ PASS | ✓ grounded |
| FT-DEC-RATE | s1-outcomes | P/F | ✅ PASS | ✓ grounded |
| FT-DEC-REDACT | s1-outcomes | P/F | ✅ PASS | ✓ grounded |
| FT-DEC-UNKNOWN | s1-outcomes | P/F | ✅ PASS | ✓ grounded |
| FT-ADV-DISTINCT | s10-adversarial | P/F | ✅ PASS | ✓ grounded |
| FT-ADV-FLOOD | s10-adversarial | P/F | ✅ PASS | ✓ grounded |
| FT-ADV-REPLAY | s10-adversarial | P/F | ✅ PASS | ✓ grounded |
| FT-DENYSTORM | s10-adversarial | P/F | ✅ PASS | ✓ grounded |
| FT-DISPATCHER | s10-adversarial | P/F | ✅ PASS | ✓ grounded |
| FT-NORM-OBFUSCATION | s10-adversarial | P/F | ✅ PASS | ✓ grounded |
| FT-SCOPE | s10-adversarial | P/F | ✅ PASS | ✓ grounded |
| FT-STEPUP | s10-adversarial | P/F | ✅ PASS | ✓ grounded |
| FT-DATACLASS | s11-freeze | P/F | ✅ PASS | ✓ grounded |
| FT-FREEZE | s11-freeze | P/F | ✅ PASS | ✓ grounded |
| FT-APPROVALS | s12-enroll | P/F | ✅ PASS | ✓ grounded |
| FT-ENROLL | s12-enroll | P/F | ✅ PASS | ✓ grounded |
| FT-ALT | s13-multiagent | P/F | ✅ PASS | ✓ grounded |
| FT-DELEGATION | s13-multiagent | P/F | ✅ PASS | ✓ grounded |
| FT-INTERAGENT | s13-multiagent | P/F | ✅ PASS | ✓ grounded |
| FT-DRAFT | s14-draft | P/F | ✅ PASS | ✓ grounded |
| FT-DRAFT-LOCK | s14-draft | P/F | ✅ PASS | ✓ grounded |
| FT-BACKTEST | s15-backtest | P/F | ✅ PASS | ✓ grounded |
| FT-BACKTEST-RO | s15-backtest | P/F | ✅ PASS | ✓ grounded |
| FT-FWK-ADK | s16-frameworks | P/F\|D | ▫ not run |  |
| FT-FWK-AG2 | s16-frameworks | P/F\|D | ▫ not run |  |
| FT-FWK-CREW | s16-frameworks | P/F\|D | ❌ FAIL | live framework run failed — see §Small-Group Run Journal |
| FT-FWK-LG | s16-frameworks | P/F\|D | ❌ FAIL | live framework run failed — see §Small-Group Run Journal |
| FT-FWK-LI | s16-frameworks | P/F\|D | ▫ not run |  |
| FT-FWK-MCP | s16-frameworks | P/F | ▫ not run |  |
| FT-FWK-OAI | s16-frameworks | P/F\|D | ▫ not run |  |
| FT-FWK-PAI | s16-frameworks | P/F\|D | ❌ FAIL | live framework run failed — see §Small-Group Run Journal |
| FT-FWK-SMOL | s16-frameworks | P/F\|D | ▫ not run |  |
| FT-FWK-SWE | s16-frameworks | P/F | ▫ not run |  |
| FT-REPLAN | s16-frameworks | P/F | ▫ not run |  |
| FT-COST | s17-nfr | P/F | ▫ not run |  |
| FT-DEFER | s17-nfr | P/F | ▫ not run |  |
| FT-DOCTOR | s17-nfr | P/F | ▫ not run |  |
| FT-FAILCLOSED | s17-nfr | P/F | ▫ not run |  |
| FT-NFR-LATENCY | s17-nfr | P/F | ▫ not run |  |
| FT-NFR-PORT | s17-nfr | P/F | ▫ not run |  |
| FT-PARITY | s17-nfr | P/F | ▫ not run |  |
| FT-SANDBOX | s17-nfr | P/F | ▫ not run |  |
| FT-T1-CLAUDE | s18-tier1 | P/F\|D | ◆ declared | Claude Code not installed on the box; reachable via the PreToolUse hook |
| FT-T1-CODEX | s18-tier1 | P/F\|D | ◆ declared | Codex CLI not installed on the box; reachable via its config/hook surface |
| FT-T1-CURSOR | s18-tier1 | P/F\|D | ◆ declared | no Cursor host; policyweave compile-out proven by the export test |
| FT-T1-GEMINI | s18-tier1 | P/F\|D | ◆ declared | Gemini CLI not installed on the box; reachable via its config/MCP surface |
| FT-ALLOW-JUSTIFY | s2-explain | P/F | ✅ PASS | ✓ grounded |
| FT-AUDIT-CHAIN | s2-explain | P/F | ✅ PASS | ✓ grounded |
| FT-AUDIT-PROVENANCE | s2-explain | P/F | ✅ PASS | ✓ grounded |
| FT-EVENT-BIND | s2-explain | P/F | ✅ PASS | ✓ grounded |
| FT-EVIDENCE-OFFLINE | s2-explain | P/F | ✅ PASS | ✓ grounded |
| FT-EXPLAIN-ACTIONABLE | s2-explain | P/F | ✅ PASS | ✓ grounded |
| FT-EXPLAIN-CLAUSE | s2-explain | P/F | ✅ PASS | ✓ grounded |
| FT-CLAIMS | s3-packs | P/F | ✅ PASS | ✓ grounded |
| FT-COMPLIANCE-MATRIX | s3-packs | P/F | ✅ PASS | ✓ grounded |
| FT-DRILL | s3-packs | P/F | ✅ PASS | ✓ grounded |
| FT-GOLDEN-FLIP | s3-packs | P/F | ✅ PASS | ✓ grounded |
| FT-PACK-LAUNCH | s3-packs | P/F | ✅ PASS | ✓ grounded |
| FT-PACK-VALIDATE | s3-packs | P/F | ✅ PASS | ✓ grounded |
| FT-SELF-ATTACK | s3-packs | P/F | ✅ PASS | ✓ grounded (self-attack pack + CLI gate) |
| FT-COVERAGE | s4-policy | P/F | ✅ PASS | ✓ grounded |
| FT-DIFF | s4-policy | P/F | ✅ PASS | ✓ grounded |
| FT-EXPORT | s4-policy | P/F | ✅ PASS | ✓ grounded |
| FT-INIT | s4-policy | P/F | ✅ PASS | ✓ grounded |
| FT-LAYER-NARROW | s4-policy | P/F | ✅ PASS | ✓ grounded |
| FT-LINT | s4-policy | P/F | ✅ PASS | ✓ grounded |
| FT-POSTURE | s4-policy | P/F | ✅ PASS | ✓ grounded |
| FT-CALIBRATION | s5-shadow | P/F | ✅ PASS | ✓ grounded |
| FT-CANARY | s5-shadow | P/F | ✅ PASS | ✓ grounded |
| FT-SHADOW | s5-shadow | P/F | ✅ PASS | ✓ grounded |
| FT-BUDGET-BURST | s6-budgets | P/F | ✅ PASS | ✓ grounded |
| FT-BUDGET-EXHAUST | s6-budgets | P/F | ✅ PASS | ✓ grounded |
| FT-BUDGET-RETRY | s6-budgets | P/F | ✅ PASS | ✓ grounded |
| FT-BUDGET-STATE | s6-budgets | P/F | ✅ PASS | ✓ grounded |
| FT-HALT | s6-budgets | P/F | ✅ PASS | ✓ grounded |
| FT-ARG-SECRET | s7-data | P/F | ✅ PASS | ✓ grounded |
| FT-ARG-VALIDATE | s7-data | P/F | ✅ PASS | ✓ grounded |
| FT-EXFIL-SINK | s7-data | P/F | ✅ PASS | ✓ grounded |
| FT-HIDING | s7-data | P/F | ✅ PASS | ✓ grounded |
| FT-HTTP-GUARD | s7-data | P/F | ✅ PASS | ✓ grounded |
| FT-REDACT-RECEIPT | s7-data | P/F | ✅ PASS | ✓ grounded |
| FT-VERIFY | s7-data | P/F | ✅ PASS | ✓ grounded |
| FT-ASK-BINDING | s8-ask | P/F | ✅ PASS | ✓ grounded |
| FT-ASK-ROUNDTRIP | s8-ask | P/F | ✅ PASS | ✓ grounded |
| FT-ASK-TIMEOUT | s8-ask | P/F | ✅ PASS | ✓ grounded |
| FT-BREAKGLASS | s8-ask | P/F | ✅ PASS | ✓ grounded |
| FT-DUALCONTROL | s8-ask | P/F | ✅ PASS | ✓ grounded |
| FT-ADAPTERS | s9-surfaces | P/F | ✅ PASS | ✓ grounded |
| FT-AUTHZEN | s9-surfaces | P/F | ✅ PASS | ✓ grounded |
| FT-DOCKER-SMOKE | s9-surfaces | P/F\|D | ✅ PASS | ✓ grounded (real container: stack-up + ready + CLI) |
| FT-MCP-ASK | s9-surfaces | P/F\|D | ✅ PASS | ✓ grounded |
| FT-SURFACE-PARITY | s9-surfaces | P/F | ✅ PASS | ✓ grounded |

**Totals:** 76 ✅ PASS (all grounded, 0 over-claimed) · 3 ❌ FAIL · 4 ◆ declared · 16 ▫ not run.

---

## Per-Suite Results

| Suite | Cases | PASS | FAIL | declared | not run |
|---|---|---|---|---|---|
| s0-regression | 3 | 3 | 0 | 0 | 0 |
| s1-outcomes | 8 | 8 | 0 | 0 | 0 |
| s2-explain | 7 | 7 | 0 | 0 | 0 |
| s3-packs | 7 | 7 | 0 | 0 | 0 |
| s4-policy | 7 | 7 | 0 | 0 | 0 |
| s5-shadow | 3 | 3 | 0 | 0 | 0 |
| s6-budgets | 5 | 5 | 0 | 0 | 0 |
| s7-data | 7 | 7 | 0 | 0 | 0 |
| s8-ask | 5 | 5 | 0 | 0 | 0 |
| s9-surfaces | 5 | 5 | 0 | 0 | 0 |
| s10-adversarial | 8 | 8 | 0 | 0 | 0 |
| s11-freeze | 2 | 2 | 0 | 0 | 0 |
| s12-enroll | 2 | 2 | 0 | 0 | 0 |
| s13-multiagent | 3 | 3 | 0 | 0 | 0 |
| s14-draft | 2 | 2 | 0 | 0 | 0 |
| s15-backtest | 2 | 2 | 0 | 0 | 0 |
| s16-frameworks | 11 | 0 | 3 | 0 | 8 |
| s17-nfr | 8 | 0 | 0 | 0 | 8 |
| s18-tier1 | 4 | 0 | 0 | 4 | 0 |
| **Total** | **99** | **76** | **3** | **4** | **16** |

---

## Root Cause Analysis

### FT-REG-MATRIX — first-run FAIL (fixed) — `str()` coercion broke the nonstring fail-closed case
- **Symptom:** the full matrix reported **83 failures**, all `adversarial-nonstring-08` (an `action: 12345` int),
  expected `deny_malformed_input` but got `allow`/`audit`.
- **Root cause:** the Cedar-mode refactor coerced scenario fields with `str()` in the **legacy** path too, so the
  int action became `"12345"` (a valid low-risk verb) instead of failing closed. The shipped guard
  `test_scenario_bound_tools_preserve_nonstring_action` encodes exactly this rule.
- **Fix:** the legacy path passes **raw** fields (no coercion); the Cedar path keeps `str()` (it canonicalizes).
- **Verification:** FT-REG-MATRIX re-run → **PASS, grounded**, 0 failures.

### Docker leg — first-run FAIL (fixed) — build context excluded `tests/field`
- **Symptom:** `docker compose build` failed: `COPY tests/field … "/tests/field": not found`.
- **Root cause:** `.dockerignore` excludes `tests/`; the Dockerfile copied it.
- **Fix:** the image carries only the shipped packs (`tests/field/` + `scripts/fieldtest/` are bind-mounted at
  runtime). Build green; `stack-ft.sh up` → **READY**; FT-DOCKER-SMOKE → **PASS**.

---

## Defect Catalogue

| # | Defect | Found by | Fix | Regression evidence |
|---|---|---|---|---|
| I-1 | Legacy path coerced scenario fields with `str()`, breaking nonstring fail-closed | FT-REG-MATRIX (83 fail) | raw fields in the legacy path | FT-REG-MATRIX PASS; `test_scenario_bound_tools_preserve_nonstring_action` |
| I-2 | `COPY tests/field` failed (`.dockerignore` excludes `tests/`) | `docker compose build` | removed the COPY; runtime bind-mount | image builds; FT-DOCKER-SMOKE PASS |
| I-3 | Grounding gate missed an empty-command assertion | `verify_harness.py` | `empty-command` rule added to `check_grounding.py` | `verify_harness.py` OK (12/12 catalogue) |
| I-4 | `build_report.py` guard compared relative vs absolute paths, so it could overwrite the hand-authored report | this report's own no-automation test | resolve-path comparison; default to `.generated.md` | guard refuses the canonical report; only `.generated.md` written |

---

## Coverage, Gaps, and Declared Limitations

Status vocabulary: **not run | PASS | FAIL | declared | N/A** — this run so far: **76 PASS · 3 FAIL · 4 declared ·
16 not run**.

- **Coverage so far:** the deterministic matrix ran green (2,988 cells) and **76 cases pass, grounded**; the
  harness + Docker + gates are exercised. **16 cases are `not run`** — the remainder of s16 (live frameworks) and
  s17 (NFRs) await their groups.
- **Declared (4):** FT-T1-CLAUDE/CURSOR/CODEX/GEMINI (Tier-1 harnesses absent → lower-layer coverage named). Each
  names its limitation; none is a silent skip.
- **Failing (3):** FT-FWK-CREW / FT-FWK-LG / FT-FWK-PAI — live framework runs, to be triaged in the s16 group
  (§Small-Group Run Journal). Stated as FAIL, never hidden.
- **Gaps:** the s16 remainder needs the live sweep to finish (vendor repos are present, oMLX is up); the Tier-1
  harnesses need a harness host.
- **Not tested (honest):** everything not listed as PASS/FAIL/declared above — stated as `not run`, never omitted.

---

## Success Metrics (PRD 07 targets; Achieved filled as the sweep runs)

| Measure | Target | Achieved | Evidence |
|---|---|---|---|
| Five outcomes exercised | 5/5 | ✅ all 5 + fail-closed/context/determinism pass, grounded | `field-test` matrix; FT-DEC-* |
| Acceptance-matrix correctness | 100% | ✅ **2,988/2,988** (deterministic matrix) | FT-REG-MATRIX |
| Deny explainability | 100% actionable | ✅ grounded | FT-EXPLAIN-ACTIONABLE / FT-EXPLAIN-CLAUSE |
| Decision latency | p99 < 100 ms | ▫ pending (s17) | FT-NFR-LATENCY |
| Fail-closed coverage | 0 silent allows | ▫ pending (s17) | FT-FAILCLOSED |
| Adversarial sub-matrix | 0 crafted allows | ✅ 8/8 grounded | FT-ADV-*, s10 |
| Field-case pass rate | 100% after fixes | ◑ 76/79 run are PASS, 3 FAIL (s16); 16 pending | this report |
| Declared / not-tested completeness | 100% with reasons | ✅ every declared names its limitation | §Coverage |
| Leak gate | 0 unmasked secrets | ✅ clean | `scan_results.py` |

---

## Performance & Timings

| Measure | Value |
|---|---|
| Deterministic matrix | 2,988 cells, in-process (seconds), 0 failures |
| OMLX field-test model p50 | **~1.0 s** (`Qwen3-4B-Instruct-2507-4bit`, tool call) |
| Docker image build | green (`agentpolicy-fieldtest:local`) |
| Stack readiness | reaches `healthy` + CLI answers (seconds) |

---

## Action Items

Done:
1. [x] Harness + Docker setup built; image + stack verified.
2. [x] Deep verification wired into the run scripts (per-case + per-suite + per-run).
3. [x] All 96 plan cases wired (plan ↔ registry reconcile = 0 missing); Cedar five-outcome scenarios added.
4. [x] OMLX benchmark run; model pinned to `Qwen3-4B-Instruct-2507-4bit`; documented (plan §4.1 + this report).
5. [x] Defects I-1/I-2/I-3/I-4 found and fixed with regressions.
6. [x] This report written **by hand**; `build_report.py` hardened so it cannot overwrite it.

Next:
7. [ ] Run the full sweep: `bash scripts/fieldtest/run-all.sh` (converts the 89 `not run` → verdicts).
8. [ ] Vendor the framework repos (`scripts/download_field_agents.sh`) → FT-FWK-* live.
9. [ ] Exercise ≥2 Tier-1 harnesses on a harness host → FT-T1-* exercised.
10. [ ] Update **this report by hand** with the full verdicts + RCA + observations.

---

## Reproducibility / Evidence Paths

```sh
# Environment + harness
cp scripts/fieldtest/.env.example scripts/fieldtest/.env
python3 scripts/fieldtest/gen_cases.py            # regenerate specs + steps from the registry
python3 scripts/fieldtest/omlx_bench.py           # re-derive the field-test model choice
bash scripts/fieldtest/stack-ft.sh up              # Docker SUT (oMLX is host-side)

# Suites  (results -> field-test/v0.1.0/results/<suite>/)
bash scripts/fieldtest/run-all.sh                  # all suites (runs the gates itself)
bash scripts/fieldtest/run-suite.sh s1-outcomes    # one suite
bash scripts/fieldtest/run-case.sh FT-DEC-ASK      # one case

# Gates (also run automatically inside run-suite.sh / run-all.sh)
python3 scripts/fieldtest/verify_harness.py        # verify the verifier
python3 scripts/fieldtest/check_grounding.py       # every PASS grounded (re-derived from disk)
python3 scripts/fieldtest/scan_results.py          # leak gate
```

**This report is hand-maintained.** `scripts/fieldtest/build_report.py` will **not** overwrite it: it refuses a
file carrying the `HAND-MAINTAINED` marker (relative or absolute `-o` alike) and defaults to a `.generated.md`
sibling.

## Appendices

- Plan: [FIELD_TEST_PLAN.md](FIELD_TEST_PLAN.md) (matrix §6, CUJ map §8, release gate §12, R-map §16).
- Harness: [`scripts/fieldtest/README.md`](../../../scripts/fieldtest/README.md).
- WBS: [Part 13](../../wbs/v0.1.0/wbs-v0.1.0-part13-fieldtest-release.md) (M24).
- PRDs: [04 users/CUJs](../../prd/04-users-and-cujs.md) · [05 features](../../prd/05-features.md) ·
  [07 success metrics](../../prd/07-success-metrics.md).
