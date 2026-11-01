<!-- HAND-MAINTAINED DOCUMENT — edit by hand only.
     Do NOT regenerate or overwrite this file with scripts/fieldtest/build_report.py.
     That script refuses to touch a file carrying this marker (see build_report.py).
     A lossy automated rewrite of this report has destroyed notes before; never again. -->

# agentpolicy v0.1.0 — Field Test Report

> **Status: IN PROGRESS (s16 interrupted mid-suite).** This is a **hand-maintained** journal, updated as the sweep runs — not a
> generated scoreboard. Counts here are read from the committed `field-test/v0.1.0/results/` verdicts and written
> by hand; nothing is auto-overwritten.
> **Current:** **86 ✅ PASS · 2 ❌ FAIL · 3 ◆ declared · 8 ▫ not run** (91/99 verdicts on disk). The deterministic
> matrix ran green (**2,988/2,988 cells, 36 scenarios × 83 agents**); suites `s0`–`s15` + `s17` are complete and
> deep-verified; **`FT-T1-CLAUDE` now runs LIVE** (Claude Code ↔ local oMLX, no hosted model — Anthropic-format
> endpoint, no Anthropic key); **`s16-frameworks` is mid-run** (3 of 11 done; interrupted — see the journal).
> **Structure:** follows the format of `agentdrill`/`agentwatch` v0.2.0 `FIELD_TEST_REPORT.md` (a journal, not a
> scoreboard), pointed at [FIELD_TEST_PLAN.md](FIELD_TEST_PLAN.md) §6 (matrix), §8 (CUJ map), §12 (release gate),
> §16 (R-map). This report states **honestly** what was tested, what passed, and what was **not** run.

---

## BLUF + Release Gate Verdict

> **86 PASS · 2 FAIL · 3 declared · 8 not run (91/99 verdicts).** The harness, the Docker setup, the deep-verification
> gate, and the case matrix are **ready and exercised** (§What Was Tested). **`s0`–`s15` + `s17` are complete:
> 85 deterministic cases PASS, every one deep-verified grounded, leak scan clean.** **`FT-T1-CLAUDE` runs LIVE
> and PASSes** — the real Claude Code agent loop driven by local oMLX (Anthropic `/v1/messages` format, no
> hosted model, no Anthropic key), gated by a PreToolUse hook → `agentpolicy evaluate`, with 6 LLM
> request/response pairs captured and an audit trail of all three decisions. `s16-frameworks` is mid-run
> (interrupted): `FT-FWK-LG` ✅ PASS (**17/17 pairs**); `FT-FWK-CREW`/`FT-FWK-PAI` ❌ FAIL (live-model tool-call
> flakiness — every row that emitted a tool call decided correctly; see the journal); 8 cases not yet run this
> sweep. The **OMLX model choice is benchmarked and applied** (§OMLX LLM Benchmark). No case is
> deleted, skipped, or optimistically marked — a case without a verdict reads **`not run`**, and a PASS without a
> re-derived assertion is not counted as grounded. An LLM-involved case that does **not** log its request/response
> pairs is an automatic **FAIL** (deep-verification rule, §Gates).

### Run status (s16 mid-run; 91/99 verdicts on disk)

| | Count |
|---|---|
| PASS (raw verdict) | 86 |
| — of which grounded (asserting check re-derived, not exit-0) | 86 (0 over-claimed) |
| FAIL | **2** (`FT-FWK-CREW`, `FT-FWK-PAI` — live-model tool-call flakiness; §Small-Group Run Journal) |
| declared (P/F\|D, environment cannot provide — named) | 3 (Cursor: GUI host absent; Codex + Gemini: not yet re-run through their new conditional steps) |
| not run | 8 (all s16 — the interrupted suite) |
| N/A (retired) | 0 |

### Release gate verdict (PRD 07 items; filled as the sweep runs)

| # | Gate (PRD 07 §release gate) | Status | Evidence / honesty |
|---|---|---|---|
| 1 | Five outcomes demonstrable (allow/deny/ask/rate-limit/redact) | ✅ | FT-DEC-* 8/8 PASS grounded (s1); Cedar matrix scenarios green in the deterministic run |
| 2 | 3 launch packs block their incident | ✅ | FT-PACK-LAUNCH PASS (grounded); 2/3 packs blocked live, 1 via deterministic pack-launch rows |
| 3 | Every deny explainable + actionable | ✅ | FT-EXPLAIN-ACTIONABLE + FT-EXPLAIN-CLAUSE PASS (grounded) |
| 4 | Decisions in the agentwatch schema | ✅ | FT-EVENT-BIND PASS (grounded) |
| 5 | Policies git-reviewed; unreviewed change flagged | ✅ | FT-AUDIT-PROVENANCE + FT-AUDIT-CHAIN PASS (grounded) |
| 6 | p99 < 100 ms + fail-closed on every path | ✅ | FT-NFR-LATENCY + FT-FAILCLOSED PASS (grounded, s17) |
| 7 | CI rejects a golden deny→allow flip | ✅ | FT-GOLDEN-FLIP PASS (grounded) |
| 8 | Adversarial sub-matrix: zero crafted allows | ✅ | FT-ADV-* 8/8 PASS (grounded, s10) — 0 crafted allows |
| 9 | Compatibility table published | ◑ | §S18: **Claude Code exercised LIVE (PASS)**; Cursor/Codex/Gemini declared with named limitations; §S16 live frameworks mid-run |
| 10 | Security baseline + coverage matrix | ✅ | FT-COMPLIANCE-MATRIX PASS (grounded) |
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

### Groups 2–11 — the next ten suites (2026-11-01) — **57/57 ✅ PASS, deep-verified**
Run one suite at a time (`run-suite.sh <suite>`, exit 0 each); each run's own deep-verification reported
*"every PASS is grounded"* and *"leak scan: clean"*. **No failures, so nothing to fix**; every case below is
`grounded=true`.

| Group | Suite | Cases | Result | Findings / notes |
|---|---|---|---|---|
| 2 | `s0-regression` | 3 | ✅ 3/3 | `FT-REG-MATRIX` re-confirms the full **36×83 = 2,988-cell** deterministic matrix, 0 failures; `FT-REG-CLI`/`FT-REG-ACCEPT` pass |
| 3 | `s2-explain` | 7 | ✅ 7/7 | deny explainability actionable + clause-level; audit chain + provenance; event-schema binding; offline evidence; allow-justification all grounded |
| 4 | `s3-packs` | 7 | ✅ 7/7 | 3 launch packs block their incident; golden deny→allow flip rejected; drill; claims ledger; self-attack; compliance matrix |
| 5 | `s4-policy` | 7 | ✅ 7/7 | posture, init, diff, lint, export, layer-narrow, coverage all behave per spec |
| 6 | `s5-shadow` | 3 | ✅ 3/3 | shadow-mode compare, calibration, canary promotion |
| 7 | `s6-budgets` | 5 | ✅ 5/5 | budget exhaust/retry/burst/state + halt all enforced |
| 8 | `s7-data` | 7 | ✅ 7/7 | arg validation, http guard, exfil sink, secret hiding, arg redaction, redact receipt, verify — zero unmasked leaks |
| 9 | `s8-ask` | 5 | ✅ 5/5 | ask round-trip + timeout + binding, dual-control, break-glass |
| 10 | `s9-surfaces` | 5 | ✅ 5/5 | surface parity, authzen, adapters, MCP-ask, and `FT-DOCKER-SMOKE` (real container: stack up → ready → CLI) |
| 11 | `s10-adversarial` | 8 | ✅ 8/8 | normalization/obfuscation, dispatcher, replay, flood, deny-storm, distinct-challenge, scope, step-up — **0 crafted allows** |

- **What I fixed:** nothing across Groups 2–11 — all green on first run.
- **Working:** every case in these ten suites.
- **Not working:** nothing in these groups.
- **Still open after this batch:** `s11-freeze`, `s12-enroll`, `s13-multiagent`, `s14-draft`, `s15-backtest`,
  `s16-frameworks` (holds the 3 FAILs: `FT-FWK-CREW/LG/PAI`), `s17-nfr`, `s18-tier1` (4 declared).

### Groups 12–18 — the remaining deterministic suites (2026-11-01) — **31/31 ✅ PASS, deep-verified**
Run one suite at a time (`run-suite.sh <suite>`, exit 0 each); each run's own deep-verification reported
*"every PASS is grounded"* and *"leak scan: clean"*. **No failures, nothing to fix.**

| Group | Suite | Cases | Result | Findings / notes |
|---|---|---|---|---|
| 12 | `s11-freeze` | 2 | ✅ 2/2 | policy freeze + dataclass semantics hold |
| 13 | `s12-enroll` | 2 | ✅ 2/2 | agent enrollment + approvals |
| 14 | `s13-multiagent` | 3 | ✅ 3/3 | alternation, delegation, inter-agent flows |
| 15 | `s14-draft` | 2 | ✅ 2/2 | NL drafting + draft lock |
| 16 | `s15-backtest` | 2 | ✅ 2/2 | backtest + read-only mode |
| 17 | `s17-nfr` | 8 | ✅ 8/8 | **p99 latency, portability, fail-closed, sandbox, cost, parity, defer, doctor** — release-gate items 6 & 10 green |
| 18 | `s18-tier1` | 4 | ◆ 4 declared | Claude Code / Cursor / Codex / Gemini CLIs **not installed on this box** — each `declared` with its limitation + lower-layer coverage (honest declared, not failures) |

### Group 19 — `s16-frameworks` (live LLM) — **MID-RUN (interrupted)** — 1 ✅ · 2 ❌ · 8 ▫
- **Run:** `run-suite.sh s16-frameworks` — **interrupted mid-suite** (FT-FWK-OAI was mid-case). Completed
  before the interrupt: `FT-FWK-LG`, `FT-FWK-CREW`, `FT-FWK-PAI`. Not run this sweep: `FT-FWK-OAI` (partial),
  `FT-FWK-ADK/AG2/LI/SMOL/SWE/MCP`, `FT-REPLAN`.
- **Deep verification (verify-only pass over everything on disk):** gate exit 0 — **85 PASS, all 85 grounded,
  0 over-claimed**; leak scan clean; every LLM capture **balanced** (req==resp) and **all-2xx**.
- **New gate rule (hardening):** an LLM-involved case (registry `llm: yes` **or** a step that drives a model)
  whose request/response pairs are **not logged** now **fails deep verification and flips the verdict to FAIL
  on disk** (`check_grounding.py` — proven on a temp copy; never on the real results).
- **Findings:**
  - `FT-FWK-LG` ✅ **PASS** — live LangGraph agent, **10/10 rows**, **17 request + 17 response pairs captured**
    (sanitized, all 2xx), `langgraph-captured` assertion grounded.
  - `FT-FWK-CREW` ❌ **FAIL** — **10/14 rows**; 4 rows `status=not-available called=False`: the local
    `Qwen3-4B-2507-4bit` model **did not emit a tool call** on those prompts → no decision to check.
    **Every row that did call decided exactly as expected** (0 policy mismatches). Capture fine (28/28 pairs).
  - `FT-FWK-PAI` ❌ **FAIL** — **9/14 rows**; same `not-available` flakiness (5 rows); plus an asyncio
    *"Event loop is closed"* teardown traceback (pydanticai async cleanup noise, not a policy failure).
    **Every row that did call decided exactly as expected.** Capture fine (14/14 pairs).
  - **Root cause (both fails):** the pinned 4-bit local model is a **flaky tool-call emitter** (~70–80% per
    call under repeated sampling). **Not a policy defect.** `FT-FWK-LG` itself failed this way earlier and
    passed 10/10 on re-run — CREW/PAI are expected to flip green on a re-run with retry.
- **What I fixed:** the report only (this entry). **No code touched in the verify-only pass.**
- **Working:** `FT-FWK-LG` end-to-end incl. LLM capture; the new not-logged⇒FAIL gate.
- **Not working (yet):** CREW/PAI tool-call flakiness (retry on next re-run); the 8 interrupted s16 cases.
- **Captured evidence:** `field-test/v0.1.0/results/s16-frameworks/cases/FT-FWK-*/` — verdicts + 59 captured
  LLM pairs total (17 LG + 28 CREW + 14 PAI), all sanitized.

### Group 20 — `FT-T1-CLAUDE` (Tier-1, LIVE Claude Code ↔ local oMLX) — **✅ PASS, deep-verified** (2026-11-01)
The first Tier-1 case to run **live**: the real Claude Code agent loop (`claude -p`, v2.1.187), driven by the
**box-local oMLX model** — no hosted model, **no Anthropic key** (oMLX natively serves the Anthropic
`/v1/messages` format; `ANTHROPIC_BASE_URL` points the CLI at it).
- **Run:** `run-case.sh FT-T1-CLAUDE` → **pass**, 7/7 assertions, `llm_captured: true`, exit 0.
- **The wiring:** PreToolUse hook (`t1_claude.sh`) → `t1_evaluate.py` (a thin wrapper over the **shipped**
  `load_policy` + `Engine.evaluate` — no fork of the decision path) → a deterministic policy
  (staging read = allow, prod write = escalate, prod destructive = deny).
- **The three-call triple, proven in the live loop:**
  1. **allow → the command EXECUTED** (`cat notes.txt` ran; the transcript shows the real output);
  2. **ask → the loop PAUSED**, side-effect file **NOT created** (the escalation surfaced as a structured
     decision the agent asked about, not a crash);
  3. **deny → structured rejection, agent replanned** (`rm -rf ft-t1-target` blocked with the policy reason).
- **Audit trail:** every decision emitted an entry — `allow_low_risk` / `escalate_prod_write` /
  `deny_critical_op`, each tied to its policy rule, in `artifacts/audit.ndjson`.
- **LLM evidence:** **6 request + 6 response pairs** captured via `t1_proxy.py` (a stdlib logging proxy
  between the CLI and oMLX — the CLI is a separate node process, so the in-process httpx hook cannot see
  its traffic; without the proxy the case would correctly **fail** `ft_assert_llm_capture`). Sanitized, all-2xx.
- **Findings / what it took (three real harness bugs found and fixed on the way):**
  1. **cwd `.claude/settings.json` silently does not load** without trusted-directory state — the first
     run's "blocks" came from Claude Code's *own* sandbox policy, not agentpolicy (0 audit entries exposed
     it). Fix: pass `--settings` explicitly. *Lesson: a hook that never fires looks exactly like a hook
     that allowed the call — assert on the audit trail, not on the block.*
  2. **`ft_cmd` routes through the agentpolicy CLI** — wrong tool for raw shell; the step needed `ft_assert`.
  3. **Policy decisions are `escalate`, not `ask`** — the hook maps agentpolicy `escalate` → Claude Code `ask`.
- **What I fixed:** `t1_claude.sh` (harness), `t1_evaluate.py` (hook entrypoint), `t1_proxy.py` (capture
  proxy), the `FT-T1-CLAUDE` registry entry (`llm: yes`, conditional live/declare steps), regenerated spec+step.
- **Working:** Claude Code ↔ oMLX end-to-end — the flagship Tier-1 journey (CUJ-2/R28) is proven live.
- **Not working / open:** Codex + Gemini steps re-drafted but **not yet proven or run** (still `declared`
  from their prior runs); Cursor stays declared (GUI host absent); the 8 interrupted s16 cases.
- **Captured evidence:** `field-test/v0.1.0/results/s18-tier1/cases/FT-T1-CLAUDE/` — verdict, assertions,
  `artifacts/claude-call{1,2,3}.txt` (live transcripts), `artifacts/audit.ndjson` (3 decisions),
  `artifacts/llm/` (6 pairs), `harness/` (policy + hook + settings, fully reproducible).

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
| FT-FWK-LG | s16-frameworks | P/F\|D | ✅ PASS | ✓ grounded — live LangGraph 10/10 rows, 17/17 LLM pairs captured |
| FT-FWK-LI | s16-frameworks | P/F\|D | ▫ not run |  |
| FT-FWK-MCP | s16-frameworks | P/F | ▫ not run |  |
| FT-FWK-OAI | s16-frameworks | P/F\|D | ▫ not run |  |
| FT-FWK-PAI | s16-frameworks | P/F\|D | ❌ FAIL | live framework run failed — see §Small-Group Run Journal |
| FT-FWK-SMOL | s16-frameworks | P/F\|D | ▫ not run |  |
| FT-FWK-SWE | s16-frameworks | P/F | ▫ not run |  |
| FT-REPLAN | s16-frameworks | P/F | ▫ not run |  |
| FT-COST | s17-nfr | P/F | ✅ PASS | ✓ grounded |
| FT-DEFER | s17-nfr | P/F | ✅ PASS | ✓ grounded |
| FT-DOCTOR | s17-nfr | P/F | ✅ PASS | ✓ grounded |
| FT-FAILCLOSED | s17-nfr | P/F | ✅ PASS | ✓ grounded |
| FT-NFR-LATENCY | s17-nfr | P/F | ✅ PASS | ✓ grounded |
| FT-NFR-PORT | s17-nfr | P/F | ✅ PASS | ✓ grounded |
| FT-PARITY | s17-nfr | P/F | ✅ PASS | ✓ grounded |
| FT-SANDBOX | s17-nfr | P/F | ✅ PASS | ✓ grounded |
| FT-T1-CLAUDE | s18-tier1 | P/F\|D | ✅ PASS | ✓ grounded — LIVE Claude Code ↔ oMLX triple (allow/ask/deny) + 6 LLM pairs + audit trail |
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

**Totals:** 86 ✅ PASS (all grounded, 0 over-claimed) · 2 ❌ FAIL · 3 ◆ declared · 8 ▫ not run.

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
| s16-frameworks | 11 | 1 | 2 | 0 | 8 |
| s17-nfr | 8 | 8 | 0 | 0 | 0 |
| s18-tier1 | 4 | 1 | 0 | 3 | 0 |
| **Total** | **99** | **86** | **2** | **3** | **8** |

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

### FT-FWK-LG → CREW/PAI — live-framework FAILs — flaky tool-call emission from the local 4-bit model
- **Symptom:** `FT-FWK-LG` first FAIL: 1 row `status=not-available called=False`. On re-run **PASS 10/10**.
  `FT-FWK-CREW` **10/14** and `FT-FWK-PAI` **9/14**: rows report `not-available called=False`, i.e. the model
  **never emitted a tool call**, so the agent never invoked the scenario tool → no decision to check.
- **Root cause:** the pinned box-local `Qwen3-4B-Instruct-2507-4bit` is a **flaky tool-call emitter**
  (~70–80% per call under repeated sampling; the OMLX benchmark's 3/3 sample overstated reliability).
  **Not a policy defect** — every row that *did* emit a call decided **exactly as expected** (0 mismatches),
  and PAI's stderr `RuntimeError: Event loop is closed` is pydanticai async-teardown noise, not a failure.
- **Fix path:** retry/re-run on the next s16 pass (LG already flipped green this way); consider a retry budget
  per row in `run_field_agents.py` before declaring a row `not-available`.
- **Verification:** capture evidence is intact for all three (17/28/14 balanced, sanitized, all-2xx pairs).

---

## Defect Catalogue

| # | Defect | Found by | Fix | Regression evidence |
|---|---|---|---|---|
| I-1 | Legacy path coerced scenario fields with `str()`, breaking nonstring fail-closed | FT-REG-MATRIX (83 fail) | raw fields in the legacy path | FT-REG-MATRIX PASS; `test_scenario_bound_tools_preserve_nonstring_action` |
| I-2 | `COPY tests/field` failed (`.dockerignore` excludes `tests/`) | `docker compose build` | removed the COPY; runtime bind-mount | image builds; FT-DOCKER-SMOKE PASS |
| I-3 | Grounding gate missed an empty-command assertion | `verify_harness.py` | `empty-command` rule added to `check_grounding.py` | `verify_harness.py` OK (12/12 catalogue) |
| I-4 | `build_report.py` guard compared relative vs absolute paths, so it could overwrite the hand-authored report | this report's own no-automation test | resolve-path comparison; default to `.generated.md` | guard refuses the canonical report; only `.generated.md` written |

---

## Field Notes — Findings, Learnings, and Observations

Detailed notes from the run, for the write-ups. Each is a claim **grounded in the evidence paths cited**.

### 1. The verdict vocabulary is the product (not the harness)
The most useful thing this field test produced is not a pass count — it is the discipline that **a result is
one of `{pass, fail, declared, not run}` and nothing else**. `s18-tier1` (Claude Code / Cursor / Codex /
Gemini) cannot run on this box: those CLIs are not installed. A "95% pass rate" dashboard would quietly drop
them. Here each is **`declared` with the exact limitation and the named lower-layer coverage** (e.g. Cursor:
"no host; policyweave compile-out proven by the export test"). Declared ≠ pass, and the distinction is the
honesty of the whole report. *Article angle: "your test dashboard lies by omission; here is a vocabulary that
doesn't."*

### 2. "The command exited 0" is not "the test passed" — grounding re-derivation
Every `PASS` verdict is re-derived **from disk, by an independent gate** (`check_grounding.py`), not trusted
from the runner's exit code. The gate re-runs each asserting check against the emitted decision and rejects
**weak shapes** that cannot fail: bare `true`, `import x`, `python -m module`, `|| true`, `json.tool`,
`test -f`, bare `pytest` outside the run_pytest driver, empty commands. Catalogue of weak shapes is itself
regression-tested (`verify_harness.py`, 12/12). Result across this run: **85/85 PASS verdicts grounded,
0 over-claimed, 0 weak shapes** — verified twice, once by the runner, once verify-only over a temp copy.
*Article angle: "exit code 0 is the weakest evidence you have; make your verifier re-derive every claim."*

### 3. Deep verification must be **verify-only-capable** — never trust a gate that can only write
The deep-verification gate can **flip a bad PASS to FAIL on disk**, which is a destructive action. When I
verified it, I did **not** run it against the real results — I copied all 91 verdicts to a temp dir, ran the
gate there, and threw the copy away. (A prior session learned this the hard way: testing the
report-overwrite guard by running it *did* clobber the hand-maintained report — defect I-4.) Rule captured:
**a destructive command is never the way to test a guard; exercise it on a copy.**
*Article angle: "test your gates the way you test your backups."*

### 4. The local-model trap: a 4-bit model that benchmarks 3/3 and flakes 30% in the field
The OMLX benchmark (`omlx_bench.py`) picked `Qwen3-4B-Instruct-2507-4bit`: **3/3 tool calls at ~1.0 s p50** —
the only candidate that emitted tool calls at all (`Llama-3.2-3B-Instruct-4bit` 0/3, `Qwen3-8B-4bit` ~27.5 s).
Three samples was **not enough**: in the live sweep the model **declined to emit a tool call ~20–30% of the
time** (`status=not-available called=False`), which cost `FT-FWK-CREW` 4/14 rows and `FT-FWK-PAI` 5/14.
**Every row that did emit a call decided exactly as expected — zero policy mismatches.** The failures were
model flakiness, not policy defects, and `FT-FWK-LG` proved it: FAIL on one run, **10/10 PASS on re-run**.
*Learnings: (a) benchmark tool-call reliability with n≥20, not n=3; (b) give live-sweep rows a retry budget
before declaring `not-available`; (c) separate "model didn't answer" from "policy decided wrong" in your
status vocabulary — they have completely different remedies.*

### 5. Capture the LLM traffic, or you have no evidence — and make its absence a failure
The live framework cases (`FT-FWK-*`) drive real agents (LangGraph, CrewAI, pydantic-ai, …) against the local
endpoint. Initially **none of that traffic was logged**: the verdict said pass while the actual
request/response evidence evaporated. Fix: `run_field_agents.py` installs an **httpx hook (sync +
`AsyncClient.send`) that records every `/chat/completions`-style call** to the case's
`artifacts/llm/call-NNNN-{request,response}.json`, **sanitized** (Bearer/`sk-` masked). Then the rule this
report enforces: **an LLM-involved case whose pairs are not logged fails deep verification — the verdict
flips to FAIL on disk.** Evidence state: **59/59 pairs captured** (17 LG + 28 CREW + 14 PAI), balanced
(req==resp), all-2xx, 0 secrets.
*Article angle: "if your eval doesn't persist the model traffic, it isn't an eval — it's a vibe."*

### 6. What the deterministic core actually proved (the boring, load-bearing 66)
`s0`–`s10` re-ran **twice**, green both times, every verdict grounded: the full **36-scenario × 83-agent
matrix (2,988 cells) at 100%** acceptance correctness — including 8 adversarial scenarios with **0 crafted
allows** (obfuscation, dispatch-confusion, replay, flood, deny-storm, distinct-challenge, scope creep,
privilege step-up); the five outcomes incl. **fail-closed on a nonstring action** (an int `action: 12345`
must `deny_malformed_input`, never coerce to a verb — defect I-1's guard); budgets (exhaust/retry/burst/state,
halt); ask-approval (round-trip, timeout, binding), **break-glass with dual control**; data defenses
(arg validation, http guard, exfil sink, secret hiding, redaction receipts); surfaces (MCP, Docker real
container, parity); explainability (clause-level, actionable, audit chain + provenance, agentwatch schema
binding, offline evidence); shadow/calibration/canary; and policy ops (posture, diff, lint, coverage,
layer-narrowing) plus packs (launch, validate, **golden deny→allow flip rejected**, drill, claims ledger,
self-attack, compliance matrix). Then `s11`–`s15` + `s17` (freeze/dataclass, enroll/approvals, multi-agent,
NL drafting, backtest, and the NFRs: **p99 latency < 100 ms, portability, fail-closed, sandbox, cost, parity,
defer, doctor** — release-gate items 6 & 10 green). **No policy defect surfaced anywhere in the deterministic
core.** *Article angle: "the matrix is the product; the LLM sweep is the smoke test on top."*

### 7. Defects found — and where they were found (all four were in the harness, not the policy)
I-1 `str()` coercion defeating fail-closed (83 matrix failures, **a real policy bug**, guard shipped);
I-2 Docker build excluding `tests/`; I-3 the grounding gate missing empty-command assertions; I-4 the
report-overwrite guard comparing relative vs absolute paths. Three of four were **test-harness bugs** — which
is the honest, expected distribution for a v0.1.0: the policy engine's defects came from the matrix
(I-1), and the harness kept finding **itself** first. That is what the deep-verification gate is *for*.
*Article angle: "your harness is a test surface too; here's the defect taxonomy after 99 field units."*

### 8. Operationally: small groups beat one big sweep
The full `run-all.sh` was interrupted twice (power/session), once mid-case. What survived: the **suite-by-suite
small-group loop** — run → deep-verify → fix → journal → pause — because each suite's results are committed
independently, and an interrupted suite is cheap to restart (`s2-explain` re-ran clean in seconds). The
journal you're reading is the audit trail of exactly that: Groups 1–11 (s0–s10), 12–18 (s11–s15+s17+s18),
19 (s16, mid-run). *Article angle: "batch size is a durability decision, not just a scheduling one."*

### 9. Environment facts that mattered (reproducibility notes)
- **Docker SUT**: image `agentpolicy-fieldtest:local` builds green; stack reaches `healthy`; oMLX stays
  **host-side** (`http://127.0.0.1:8000/v1`; container sees `host.docker.internal:8000`).
- **Vendor repos (791 MB)** live under `tests/field/agents/vendor/`, **gitignored** — verified **0 vendor
  files tracked**. Third-party clones never enter the repo; the sweep re-downloads them.
- **Python**: everything runs on the repo `.venv` python; system `python3` lacks pytest (a previous
  run silently mis-gated until this was pinned in the runner).
- **Async teardown noise**: pydanticai leaves `RuntimeError: Event loop is closed` in stderr on exit —
  harmless cleanup-order artifact, worth documenting so it isn't miscounted as a failure.

### 10. Honest remaining work (as of this entry)
1. Finish `s16-frameworks`: `FT-FWK-OAI` (interrupted mid-case) + `FT-FWK-ADK/AG2/LI/SMOL/SWE/MCP`,
   `FT-REPLAN` — 8 cases, not run this sweep.
2. Retry `FT-FWK-CREW` / `FT-FWK-PAI` (expected to flip green like LG did); consider a per-row retry budget.
3. Prove + run the new Codex/Gemini live steps (drafted, not yet exercised); Cursor needs a GUI host.
4. Release gate: 9/11 green; item 9 (compatibility table) waits on s16 + s16-related work; item 11 is a user test.

### 11. How FT-T1-CLAUDE was made to work locally — the full wiring story (for the write-ups)
**Goal:** run the *real* Claude Code agent loop against the **box-local oMLX model** — no hosted LLM, no
Anthropic key — with every tool call gated by `agentpolicy evaluate` and every decision captured as evidence.
What it took, in the order the problems appeared:

1. **The unlock: oMLX natively speaks Anthropic's `/v1/messages` format.** First probe returned `200` with a
   real `msg_*` body (`content[]`, `stop_reason`, usage) — so Claude Code could point straight at it via
   `ANTHROPIC_BASE_URL=http://127.0.0.1:8000`, `ANTHROPIC_AUTH_TOKEN=local`, `ANTHROPIC_MODEL=Qwen3-4B…`.
   No translation proxy needed for the protocol, no key for the auth. *Verify the transport before wiring
   anything on top of it.*
2. **A silent non-firing hook looks exactly like a working policy (the dangerous one).** The first "run"
   produced plausible block messages — but `audit.ndjson` had **0 entries**: Claude Code had never fired our
   PreToolUse hook, and the blocks came from **Claude's own sandbox policy**, not agentpolicy. Root cause:
   a cwd `.claude/settings.json` does not load without trusted-directory state. Fix: `--settings <file>`
   passed explicitly. *Lesson: never validate a hook by its block messages — **assert on the audit trail.**
   A hook that never fires is indistinguishable from an allow, until you count decisions.*
3. **`ft_cmd` vs `ft_assert`.** The step ran `ft_cmd "…" bash …` — but `ft_cmd` routes through the
   agentpolicy CLI, so `bash` was rejected as a subcommand. The whole first registered run "failed" on a
   plumbing mismatch. Fix: raw shell assertions go through `ft_assert`.
4. **The decision vocabulary: `escalate`, not `ask`.** The policy's rule decision for "needs a human" is
   `escalate` (rule decisions are `allow | audit | escalate | deny`); Claude Code's permission vocabulary
   calls it `ask`. The hook maps `escalate → ask` at the boundary. Earlier the policy itself failed schema
   validation with `decision: ask` — the fail-closed parser caught it with a line:column pointer (I-1's
   guard doing its job on our own config).
5. **Separate-process traffic can't be hooked in-process.** The earlier httpx capture hook (built for the
   Python framework runners) cannot see Claude Code's traffic — it's a node process. Fix: **`t1_proxy.py`**,
   a stdlib `ThreadingHTTPServer` logging proxy between the CLI and oMLX that writes every
   `/messages|/completions` pair to `artifacts/llm/call-NNNN-{request,response}.json`, sanitized. Without it,
   `ft_assert_llm_capture` and the deep-verification LLM gate correctly **fail** the case — the evidence bar
   was set first, the harness caught up to it.
6. **Prove the pieces standalone before composing them.** The hook was tested with
   `printf '{"tool_input":{"command":"cat …"}}' | hook.sh` (all three decisions verified) *before* the live
   loop was trusted; the policy was proven through `agentpolicy evaluate` before the hook existed; the proxy
   was proven with curl before claude ran through it. Every composition failure thereafter was in exactly one
   new layer.
7. **The final shape (all reusable, all committed with the run):** `t1_evaluate.py` (hook entrypoint over the
   shipped loader+engine — no fork), `t1_claude.sh` (policy+hook+triple runner, evidence into the case dir),
   `t1_proxy.py` (capture proxy), and the registry's conditional step: CLI+oMLX present → live triple;
   absent → honest `declare`. **Result: FT-T1-CLAUDE `pass`, `llm_captured: true`, 6 pairs, 3-decision audit
   trail, exit 0 — the flagship Tier-1 journey proven on a box with no cloud and no key.**

*Article angle: "you can field-test a Tier-1 agent harness on a laptop — here's the exact wiring, and the
three bugs that made the first run look green when it wasn't."*

---

## Coverage, Gaps, and Declared Limitations

Status vocabulary: **not run | PASS | FAIL | declared | N/A** — this run so far: **86 PASS · 2 FAIL · 3 declared ·
8 not run** (91/99 verdicts).

- **Coverage so far:** the deterministic matrix ran green (2,988 cells) and **85 cases pass, all 85 grounded**
  (0 over-claimed); the harness + Docker + gates are exercised. **`s0`–`s15` and `s17` are complete** — every
  case in them has a verdict and it is PASS (s18: declared).
- **Failing (2):** `FT-FWK-CREW` (10/14 rows) and `FT-FWK-PAI` (9/14 rows) — live-model tool-call flakiness
  (**not** a policy defect; see §Root Cause Analysis). Stated as FAIL, never hidden.
- **Declared (3):** FT-T1-CURSOR (GUI IDE host absent; policyweave compile-out proven by the export test),
  FT-T1-CODEX / FT-T1-GEMINI (CLIs installed on the box but their new conditional live steps are drafted,
  not yet proven — re-run pending; Codex needs a local chat-completions provider, Gemini's backend is
  Google-hosted only). Each names its limitation; none is a silent skip.
- **Failing (2):** `FT-FWK-CREW` (10/14 rows) / `FT-FWK-PAI` (9/14 rows) — live-model tool-call flakiness,
  **not** policy defects (§Root Cause Analysis). Stated as FAIL, never hidden.
- **Not run (8):** the interrupted `s16-frameworks` remainder — `FT-FWK-OAI` (cut off mid-case) and
  `FT-FWK-ADK/AG2/LI/SMOL/SWE/MCP` + `FT-REPLAN` (never started this sweep).
- **Gaps:** the s16 remainder needs the live sweep to finish (vendor repos are present, oMLX is up); Cursor
  needs a GUI host; Codex/Gemini need their live steps proven and re-run.
- **Not tested (honest):** everything not listed as PASS/FAIL/declared above — stated as `not run`, never omitted.

---

## Success Metrics (PRD 07 targets; Achieved filled as the sweep runs)

| Measure | Target | Achieved | Evidence |
|---|---|---|---|
| Five outcomes exercised | 5/5 | ✅ all 5 + fail-closed/context/determinism pass, grounded | `field-test` matrix; FT-DEC-* |
| Acceptance-matrix correctness | 100% | ✅ **2,988/2,988** (deterministic matrix) | FT-REG-MATRIX |
| Deny explainability | 100% actionable | ✅ grounded | FT-EXPLAIN-ACTIONABLE / FT-EXPLAIN-CLAUSE |
| Decision latency | p99 < 100 ms | ✅ pass, grounded (s17) | FT-NFR-LATENCY |
| Fail-closed coverage | 0 silent allows | ✅ pass, grounded (s17) | FT-FAILCLOSED |
| Adversarial sub-matrix | 0 crafted allows | ✅ 8/8 grounded | FT-ADV-*, s10 |
| Field-case pass rate | 100% after fixes | ◑ 85/87 with verdicts are PASS, 2 FAIL (live-LLM flakiness); 8 pending | this report |
| Declared / not-tested completeness | 100% with reasons | ✅ every declared names its limitation | §Coverage |
| Leak gate | 0 unmasked secrets | ✅ clean | `scan_results.py` |
| LLM evidence capture | every live call logged | ✅ 59/59 pairs (17 LG + 28 CREW + 14 PAI), balanced, sanitized, all-2xx; not-logged ⇒ FAIL gate | `artifacts/llm/`, `check_grounding.py` |

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
7. [ ] Finish `s16-frameworks`: `FT-FWK-OAI` (interrupted mid-case) + `FT-FWK-ADK/AG2/LI/SMOL/SWE/MCP`, `FT-REPLAN`.
8. [ ] Retry `FT-FWK-CREW` / `FT-FWK-PAI` (flaky tool-call rows; LG flipped green on re-run) — consider a per-row retry budget in `run_field_agents.py`.
9. [ ] Exercise ≥2 Tier-1 harnesses on a harness host → FT-T1-* exercised.
10. [ ] Keep updating **this report by hand** with the verdicts + RCA + learnings (§Field Notes).

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
