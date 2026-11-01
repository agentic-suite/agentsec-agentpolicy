# Cedar Decision Core — Design (M2, v0.1.0)

**BLUF:** M2 is the decision core: a **deterministic Cedar PDP** that evaluates a canonical action and returns
one of **five outcomes** — `allow` / `deny` / `ask` / `rate-limit` / `redact` — with the **mandatory
human-gate class**, the PRD 15 decision model, and a **sub-100 ms p99** inline budget. Cedar is the primary
policy language (PRD 11 DD-02). This is the design of record (`2.D0`); it delivers **CUJ-1**.

> Status: **Done** — branch `feat-0.1.0`. Package: `src/agentpolicy/cedar/`. Engine: `cedarpy` (Cedar Rust
> bindings). No ML and no network in the path.

---

## 1. The five outcomes (`2.2`)

| Outcome | Meaning | Shaped from |
|---|---|---|
| `allow` | execute normally | Cedar **allow** and no gate/budget/redaction applies |
| `deny` | blocked with a reason | Cedar **deny** (destructive or no permit) |
| `ask` | human approval required | Cedar allow + the **human-gate class** |
| `rate-limit` | throttled, `retry_after` | Cedar allow + session budget exhausted |
| `redact` | allow, scrub sensitive output | Cedar allow + sensitive read |

## 2. Pipeline (`2.1`)

```
canonical call ──▶ to_request()  ──▶ cedarpy.is_authorized ──▶ shaper.shape() ──▶ Decision (5 outcomes)
 (NormalizedCall)   (principal,        Allow / Deny /           (+ gate class,
                     action,          NoDecision                budget state)
                     resource,
                     context)
```

* `agentpolicy/cedar/policy.py` — the base Cedar policy + `to_request`/`build_entities`.
* `agentpolicy/cedar/evaluator.py` — `CedarEvaluator` (wraps `cedarpy`, fails fast on a malformed policy).
* `agentpolicy/cedar/shaper.py` — `shape(...)`: maps the Cedar result + metadata → one outcome.
* `agentpolicy/cedar/gates.py` — the human-gate class.
* `agentpolicy/cedar/models.py` — `Decision` / `Factor` / `Explanation` (PRD 15/17).

**Determinism:** the same call + policy always yields the same decision (no randomness, no network, no ML).

## 3. Cedar policy & entities (`2.1`)

The **balanced** base policy (Cedar text, `BASE_POLICY`) is loaded verbatim:

```cedar
@id("permit-read-nonprod")
permit (principal, action, resource)
when { context.verb == "read" && context.environment != "production" };

@id("forbid-destructive-production")
forbid (principal, action, resource)
when { (context.verb == "delete" || ... ) && context.environment == "production" };
...
```

The call maps to a request with `principal = Agent::<agent_id>`, `action = Action::<verb>`,
`resource = Tool::<tool>`, and a `context` carrying `verb`, `environment`, `data_class`, `tool_category`,
`action_class`, `agent_class`. The tool is also an entity carrying its `category`.

> Cedar's default is **deny**: a call with no matching `permit` is a `deny` (fail-closed).

## 4. The shaper (`2.2`)

Precedence: a Cedar **deny is final**; otherwise `rate-limit` > `ask` (gate class) > `redact` > `allow`.

```python
shape(cedar_allowed=..., call=..., matched_rule=..., ctx=ShaperContext(budget_exhausted=..., retry_after=...))
```

## 5. The mandatory human-gate class (`2.3`)

Irreversible actions **default to `ask`** rather than a hard deny. `gates.is_human_gate(call)` is true when the
environment is `production` and the verb is in `HUMAN_GATE_VERBS` (`write`, `deploy`, `send`, `transfer`,
`grant`, `approve`). Destructive verbs (`delete`/`drop`/`destroy`) are **not** in the class — they are hard
denied by Cedar. Changing the gate class is a **logged amendment**
(`gates.amendment_record(...)` + `gates.log_amendment(...)`), never a silent config change.

## 6. Decision model (`2.4`, PRD 15/17)

`Decision(decision, reason_code, criticality, explanation, factors[], policy_version, matched_rule,
retry_after?, redactions?)`, with `Factor(dimension, value, contribution)` and the `Explanation` artifact
(`matched_rule`, `context`, `suggested_change`, `factors[]`). `Decision.to_dict()` is the JSON shape; `rate-limit`
adds `retry_after`, `redact` adds `redactions`.

## 7. Latency budget (`2.5`)

Measured in `tests/test_cedar_latency.py`: **p99 < 100 ms** over 300 warm evaluations (PRD 13 / R8), plus a
generous cold-start bound (policy parse + first decision).

## 8. Fail-closed

A malformed policy raises at `CedarEvaluator` construction (never silently "deny everything"); a call with no
permit is a `deny`; any unexpected Cedar result is treated as not-allowed → `deny`.

## 9. WBS M2 item mapping

| Item | Where |
|---|---|
| 2.D0 | this document |
| 2.1 Cedar evaluator | `cedar/evaluator.py`, `cedar/policy.py` |
| 2.2 five-outcome shaper | `cedar/shaper.py` |
| 2.3 mandatory human-gate class | `cedar/gates.py` |
| 2.4 decision model | `cedar/models.py` |
| 2.5 latency budget | `tests/test_cedar_latency.py` |
| 2.T/2.C/2.L/2.CR/2.D | tests · coverage · ruff/mypy · [codereview-log](../wbs/v0.1.0/codereview-log.md) · [Decisions reference](../reference/decisions.md) |
