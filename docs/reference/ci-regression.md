# CI regression & fail-closed — reference (v0.1.0)

WBS M11 · CUJ-7 / CUJ-9 · R22 / R8 / R32. Design: [ci-regression.md](../design/ci-regression.md).

## Golden regression gate (`11.1`)

```sh
agentpolicy goldens check                                  # capture the golden baseline (JSON)
agentpolicy goldens check --baseline goldens.json          # fail on a deny->allow flip
agentpolicy goldens check --baseline goldens.json --json
```

`goldens.detect_flips(baseline, cases)` reports **flips** (a previously-blocked case now allows — build-breaking)
and **drift** (any other change). `GateResult.passed` is False when a flip exists.

## agentdrill incident-replay gate (`11.2`)

```sh
agentpolicy drill check --packs-dir packs
```

Replays each incident pack (`packs/<name>/tests.yaml`) and **fails** if a fixture whose expected outcome was a
block (`deny`/`ask`/`rate-limit`/`redact`) now allows — "this change un-blocks the incident".

## Fail-closed fuzz (`11.3`)

`tests/test_m11_ci.py` uses `hypothesis` to fuzz the input space (random tool/action/environment/data/agent) and
asserts the engine **never raises** and **never allows** a destructive production-PII action. A separate sweep
asserts every failure path carries a **distinct, non-empty** reason code.

## Coverage export (`11.4`)

```sh
agentpolicy compliance export --json
agentpolicy compliance export -o coverage.json
```

`compliance.coverage_matrix(packs)` walks the shipped packs (`metadata.yaml: domains`) and computes, per
**OWASP ASI/LLM** and **ATLAS** control, whether the current policy set covers it. The artifact
(`agentcomply.coverage.v1`) is what agentcomply/agentwatch consume; it is **computed**, never hardcoded.

```python
from agentpolicy import compliance
matrix = compliance.export_matrix()          # {schema, target, frameworks:{OWASP-ASI:{covered,total,controls}, …}}
```
