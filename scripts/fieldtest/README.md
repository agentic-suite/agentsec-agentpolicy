# Field-test harness (`scripts/fieldtest/`)

The runnable harness behind `docs/field-test/v0.1.0/FIELD_TEST_REPORT.md`. It
drives the shipped `agentpolicy` CLI/engine through real agent loops (frameworks
+ Tier-1 coding agents), enforces deep verification, and records evidence.

## Layout

| File | Role |
|---|---|
| `gen_cases.py` | case registry → case specs + step scripts (single source of truth) |
| `run-case.sh` | run one case (sources `cases/steps/<ID>.sh`) |
| `run-suite.sh` | run every case in one suite (runs the gates itself) |
| `run-all.sh` | run every suite |
| `lib.sh` | per-case lifecycle, assertions, grounding, leak gate |
| `collect-results.py` | aggregate a suite's verdicts |
| `check_grounding.py` | deep verification: every PASS re-derived from disk; **LLM not-logged ⇒ FAIL** |
| `scan_results.py` | leak gate over committed evidence |
| `verify_harness.py` | verifies the verifier (weak-assertion catalogue) |
| `build_report.py` | writes only `.generated.md`; refuses the hand-maintained report |
| `omlx_bench.py` | OMLX model benchmark (the model pin) |
| `t1_claude.sh` / `t1_codex.sh` | Tier-1 harnesses (Claude Code / Codex CLI) |
| `t1_evaluate.py` / `t1_proxy.py` | hook entrypoint + LLM-capture proxy |

## Run

```sh
bash scripts/fieldtest/stack-ft.sh up            # Docker SUT (oMLX is host-side)
bash scripts/fieldtest/run-suite.sh s1-outcomes  # one suite (runs the gates)
bash scripts/fieldtest/run-all.sh                # all suites
python3 scripts/fieldtest/check_grounding.py     # deep-verification gate
```

Results land under `field-test/<version>/results/<suite>/`. See the plan
(`docs/field-test/v0.1.0/FIELD_TEST_PLAN.md`) and the report
(`docs/field-test/v0.1.0/FIELD_TEST_REPORT.md`).
