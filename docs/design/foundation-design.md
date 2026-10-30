# Foundation & Identity — Design (M1, v0.1.0)

**BLUF:** M1 fixes agentpolicy's identity and foundation: the CLI surface with reserved exit codes, the
configuration model (precedence, `strict`, fail-closed), the policy loader/validator + `check`, `doctor`
self-observability, and the CI quality gate every later milestone builds on. This document is the M1 design of
record (`1.D0`). Most of the surface was delivered by the M0 port; M1 fixes the contracts and adds the pieces
the predecessor lacked (`doctor`, `make setup`, the exit-2 fail-closed contract, the CI coverage gate).

> Status: **Done** — branch `feat-0.1.0`. See [development.md](../development.md) for the dev workflow.

---

## 1. CLI surface & reserved exit codes (`1.2`)

`agentpolicy <command>` (argparse). `--version` prints `agentpolicy <version>`; `--help` lists the surface.

| Command | Purpose |
|---|---|
| `evaluate` | evaluate one tool call → a decision |
| `explain` | factor breakdown + explanation for a call |
| `check` | validate a policy file (fail-closed) |
| `init` | write a posture preset (`balanced`/`strict`/`permissive`) |
| `audit` | query / show / replay / verify the audit trail |
| `pack` | validate + test policy packs |
| `report` | governance/compliance reports |
| `doctor` | environment checks + verdict (**new in M1**) |
| `diff`, `policy`, `scan`, `analytics`, `calibrate`, `baseline`, `escalation`, `swebench`, `test`, `serve`, `field-test` | subsystem surfaces |

**Reserved exit codes** (`cli/errors.py`, `cli/__init__.py`):

| Code | Meaning | Raised by |
|---|---|---|
| `0` | success | — |
| `1` | general user-facing failure | `CliError` |
| `2` | **invalid configuration/policy — fail closed** | `ConfigError`, and argparse usage errors |

`main()` returns `exc.exit_code`, so a broken configuration is a distinct, scriptable failure.

## 2. Configuration model (`1.3`)

Policy/config is a single `agentpolicy.yaml`. Resolution precedence (highest first):

1. explicit `--policy PATH` (or the positional arg for `check`)
2. `AGENTPOLICY_POLICY_PATH` env var
3. `./agentpolicy.yaml`
4. the posture preset (`--posture`, default `balanced`)

The loader (`policy/loader.py`) parses YAML, validates against the Pydantic schema, and merges the posture
default. **Fail-closed:** a missing/unparseable/schema-violating file raises `PolicyParseError`, which the CLI
maps to `ConfigError` → **exit 2** and a message naming the first error. A malformed policy is never accepted
silently. (`check --migrate` additionally reports breaking changes vs. the posture default.)

## 3. Policy loader + validator + `check` (`1.6`)

`agentpolicy check [policy]` loads the file (precedence above) and prints
`ok: <path> (version <v>, posture <p>)` on success (exit 0). On failure it fails closed (exit 2) with the first
error and its line/column. This is the gate used at startup and on policy reload.

> The v0.1.0 **Cedar** policy language is introduced by the **M2 Cedar decision core**; M1 establishes the
> loader/validator/`check` *framework* (schema validation, location-reporting errors, fail-closed).

## 4. Self-observability — `doctor` (`1.5`)

`agentpolicy doctor [--policy PATH] [--json]` runs local checks and returns a verdict:

| Check | Passes when |
|---|---|
| `python` | runtime ≥ 3.11 |
| `policy` | the configured/preset policy loads |
| `engine` | a smoke decision evaluates (`query_logs`/read/staging/internal) |
| `audit_sink` | `~/.agentpolicy/` is creatable and writable |

Verdict: `healthy` (exit 0) or `unhealthy` (exit 1). `--json` emits `{version, ok, checks[]}`.

## 5. CI & quality gate (`1.4`, `1.T`, `1.C`, `1.L`)

`.github/workflows/ci.yml` (test job): `uv sync --group dev` → `ruff check .` → `mypy --strict src/` →
`pytest --cov=agentpolicy` (**coverage ≥ 95%**, enforced by `[tool.coverage.report] fail_under = 95`). DCO
enforced by `.github/workflows/dco.yml`. Docker / UI / field-test / scorecard run as separate jobs.

## 6. Identity & governance docs (`1.7`, `1.D`)

`README.md`, `LICENSE` (Apache-2.0), `CODEOWNERS`, `SECURITY.md`, `CONTRIBUTING.md`, `GOVERNANCE.md`,
`THIRD_PARTY_NOTICES.md`, plus the PRD/ADR/compliance/WBS trees. Traceability lives in
[PRD 12](../prd/12-traceability.md).

## 7. WBS M1 item mapping

| Item | Where |
|---|---|
| 1.D0 | this document |
| 1.1 rebrand build config | `pyproject.toml` (`agentsec-agentpolicy`, bin `agentpolicy`), `Makefile` (`setup`/`test`/`cov`/`lint`/`typecheck`) |
| 1.2 CLI + exit codes | `cli/__init__.py`, `cli/errors.py` (§1) |
| 1.3 config model | `policy/loader.py`, `cli/check.py` (§2, §3) |
| 1.4 CI gate | `.github/workflows/ci.yml`, `dco.yml` (§5) |
| 1.5 self-observability | `cli/doctor.py` (§4) |
| 1.6 loader/validator/`check` | `policy/loader.py`, `cli/check.py` (§3) |
| 1.7 identity docs | §6 |
| 1.T/1.C/1.L/1.CR/1.D | tests + gates + [codereview-log](../wbs/v0.1.0/codereview-log.md) + [CLI reference](../reference/cli.md) |
