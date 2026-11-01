# NFRs, Hardening, Parity Closure & Deferred-Optional — Design (M23, v0.1.0)

**BLUF:** M23 closes the non-functionals, hardens against the own-threat-model, closes the predecessor **parity
ledger** (no silent drops), ships the **standards/claims** guardrails, and lands or **explicitly waives** the
deferred-optional items. This is the design of record (`23.D0`).

> Status: **Done** — branch `feat-0.1.0`. Modules: `agentpolicy/nfr.py`, `faultinject.py`, `sandbox.py`,
> `cost.py`, `parity.py`, `claims.py`, `deferred.py`.

---

## 1. Performance + portability (`23.1`) — R8

`agentpolicy/nfr.py`: `p99_ms(fn, samples, warmup)` measures the sub-100 ms p99 budget on the **engine** path
(the Cedar evaluator's budget is already covered by `tests/test_cedar_latency.py`); `supported_python()` asserts
Python 3.10+; `is_portable_platform()` asserts macOS/Linux; `local_first()` asserts the engine imports and
evaluates with no network/env. Budgets are measured in `tests/test_m23_nfr.py`.

## 2. Fail-closed fault injection (`23.2`) — R8

`agentpolicy/faultinject.py`: `InjectedFault(AgentPolicyError)` and `fault_hook(reason_code)` raise at a chosen
stage. `tests/test_m23_failclosed.py` injects a failure at **every** engine stage (normalize / scope / argument
policy / score / decide / explain) and asserts the result is a **deny with a reason code** and that the
injection loop **never aborts** — no silent allow, no crash.

## 3. Untrusted-pack sandbox (`23.3`) — R6 / PRD 06

`agentpolicy/sandbox.py`: `sanitized_env(env, allow=())` strips secret-looking keys (env isolation);
`SandboxPolicy(trust, network)` + `authorize_pack(manifest, policy)` enforce **trust levels** (an `untrusted`
pack is refused when the policy does not allow it, and `--network none` refuses an untrusted pack that asks for
network); `run_pack_sandboxed(...)` runs the pack under the sanitized env and emits an **audit event**.

## 4. Cost controls (`23.4`) — R8

`agentpolicy/cost.py`: `CostGovernor(max_cost)` charges each unit of work and raises `CostExceeded` over the
ceiling. `backtest(..., max_cost=...)` aborts the replay **and reports** (`BacktestReport.aborted` /
`abort_reason`); the `backtest` CLI exposes `--max-cost`.

## 5. Parity / absorption ledger (`23.5`) — PRD 10

`agentpolicy/parity.py`: a registry of every predecessor capability (the WBS porting map) with a status of
**delivered / delegated / waived** and a reason. `parity_gate()` returns the capabilities that are neither
delivered nor explicitly waived — **green == no silent drops**. `docs/reference/parity-ledger.md` records it.

## 6. Standards / compliance export + claims linter (`23.6`) — R32

`agentpolicy/claims.py` lints the published **claims** against the computed coverage matrix (`compliance.py`):
a claim must reference a framework control and must not assert coverage of an **uncovered** control. The
coverage matrix (`compliance.export_matrix`) remains computed from the shipped packs' domains.

## 7. Deferred-optional (`23.7`) — R13 / R14 / R31

`agentpolicy/deferred.py` records each deferred-optional item with a status of **implemented** or **waived**
with a written reason: the OPA→Cedar migration assistant (R13) and the pack marketplace (R14) are **waived**
(their acceptance is a v0.2/v0.3 product surface, not a v0.1.0 control); fleet sync (R31) is **waived**
(agentpolicy decides; agentwatch/agentcomply own the fleet). `deferred_gate()` fails any item with neither an
implementation nor a waiver reason — "implemented or explicitly waived with reason".

## 8. WBS M23 item mapping

| Item | Where |
|---|---|
| 23.D0 design docs first | this document |
| 23.1 performance + portability | `agentpolicy/nfr.py`, `tests/test_m23_nfr.py` |
| 23.2 fail-closed fault injection | `agentpolicy/faultinject.py`, `tests/test_m23_failclosed.py` |
| 23.3 untrusted-pack sandbox | `agentpolicy/sandbox.py` |
| 23.4 cost controls | `agentpolicy/cost.py`, `cli/backtest.py --max-cost` |
| 23.5 parity ledger | `agentpolicy/parity.py`, [parity reference](../reference/parity-ledger.md) |
| 23.6 standards/claims | `agentpolicy/claims.py`, `compliance.py` |
| 23.7 deferred-optional | `agentpolicy/deferred.py` |
| 23.T/23.C/23.L/23.CR/23.D | tests · coverage · ruff/mypy · [codereview-log](../wbs/v0.1.0/codereview-log.md) · [hardening reference](../reference/hardening-and-nfrs.md) |
