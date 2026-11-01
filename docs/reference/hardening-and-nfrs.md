# Hardening & NFRs — reference (v0.1.0)

WBS M23 · R8 / R32 / R13 / R14 / R31. Design:
[hardening-and-nfrs.md](../design/hardening-and-nfrs.md).

## Performance + portability (`23.1`)

```python
from agentpolicy.nfr import p99_ms, supported_python, is_portable_platform, local_first
supported_python()          # Python 3.10+
is_portable_platform()      # macOS / Linux
local_first()               # decides in-process, no network
```

The sub-100 ms p99 budget is measured on the **engine** path in `tests/test_m23_nfr.py` (the Cedar evaluator's
budget is covered by `tests/test_cedar_latency.py`).

## Fail-closed fault injection (`23.2`)

```python
from agentpolicy.faultinject import fault_hook, InjectedFault
monkeypatch.setattr(engine_mod, "score", fault_hook("engine_unavailable"))
# evaluate() → deny with reason_code=engine_unavailable; never an allow, never a crash
```

`tests/test_m23_failclosed.py` injects a fault at every engine stage and asserts a reasoned deny; the injection
loop never aborts.

## Untrusted-pack sandbox (`23.3`)

```python
from agentpolicy.sandbox import SandboxPolicy, run_pack_sandboxed, sanitized_env
clean = sanitized_env()                       # secrets stripped from the env
results, events = run_pack_sandboxed("packs/x", policy=SandboxPolicy(required_trust="launch"))
```

Trust levels (`untrusted < community < launch < trusted`) gate who may run a pack; an untrusted pack is never
granted the network (`--network none`); every sandboxed run emits an audit event (no env leaked).

## Cost controls (`23.4`)

```sh
agentpolicy backtest --history h.jsonl --candidate c.yaml --max-cost 500
```

`CostGovernor(max_cost)` charges each unit of work; over the ceiling the run **aborts and reports**
(`BacktestReport.aborted` / `abort_reason`, `CostExceeded`).

## Standards / claims (`23.6`)

```sh
agentpolicy compliance export            # the computed OWASP ASI/LLM + ATLAS matrix
agentpolicy compliance claims            # lint published claims (exit 1 on drift)
```

`claims.lint_claims()` asserts every published claim references a covered control — no claim may assert
coverage of an uncovered one.

## Deferred-optional (`23.7`)

```python
from agentpolicy.deferred import deferred_gate, deferred_report
deferred_gate()   # [] — every item is implemented or waived with a reason
```

| Req | Item | Disposition |
|---|---|---|
| R13 | OPA → Cedar migration assistant | **waived** — a v0.2 authoring surface; the OPA peer backend already ships |
| R14 | Rule-pack marketplace | **waived** — a v0.3 distribution surface, not a control |
| R31 | Fleet sync | **waived** — agentwatch/agentcomply own the fleet (ADR-0007) |

Parity closure is tracked in the [parity ledger](parity-ledger.md).
