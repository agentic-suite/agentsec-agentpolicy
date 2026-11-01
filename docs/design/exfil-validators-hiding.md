# Exfil-Sink, Argument Validation & Tool Hiding — Design (M13, v0.1.0)

**BLUF:** M13 closes the data-flow gap. An **exfil-sink rule class** blocks sensitive data
(`restricted`/`customer_pii`) flowing to an **external-sink** tool (an `http`/`email`/`notify` domain), naming the
**source and the sink** — taint-lite, no ML. **Argument-level validation** (regex / enum / range / path-containment
/ URL-allowlist) constrains *how* a tool is called (SELECT-only, refund cap, SSRF, path traversal). **Discovery-time
tool hiding** keeps a tool an agent cannot call out of its capability list. This is the design of record
(`13.D0`); it delivers **CUJ-13** (R10, R19, R21).

> Status: **Done** — branch `feat-0.1.0`. Modules: `engine/exfil.py`, `engine/argument_policy.py`,
> `engine/engine.py` (`capabilities`), `packs/exfil-sink/`.

---

## 1. Exfil-sink rule class (`13.1`)

`engine/exfil.py` — `exfil_violation(call)`: a call is an exfiltration chain when

* the tool's domain is an **external sink** (`http` / `email` / `notify`),
* the verb is **outbound** (`send` / `post` / `put` / `write` / `publish` / `upload` / …), and
* the data class is **sensitive** (`restricted` / `customer_pii`).

The engine (stage 1c, before scoring) denies such a call with `reason_code="deny_exfil_sink"` and an explanation
that **names the source and the sink** (`sensitive customer_pii data flowing to external sink 'send_email'
(email)`). The shipped **`packs/exfil-sink`** pack carries the same rule as Cedar (`@id("exfil-sink-block")`) and
an incident replay proving the chain is blocked.

The rule is deliberately **taint-lite**: it reasons over the call's own context (domain + verb + data class), not
a cross-call data-flow graph — deterministic, no ML, and it names both ends of the chain.

## 2. Argument-level validation (`13.2`)

`ArgumentSpec` (declared per tool/argument in `agentpolicy.yaml` under `tools[].args_policy`) gains
policy-declarable validators:

| Field | Meaning | Example |
|---|---|---|
| `regex` | the value's string form must match (`search` semantics) | `(?i)^\s*select\b` (SELECT-only) |
| `enum` | the value must be one of a closed set | `[staging, production]` |
| `min`/`max` | inclusive numeric bounds (existing) | `max: 100` (refund cap) |
| `path_root` | a path value must stay **contained** under the root (realpath) | defeats `../` traversal |
| `url_allowlist` | a URL value's host must be on the allowlist | blocks SSRF (`169.254.169.254`) |

`check_arguments` applies them in a fixed order and returns the first violating argument; the engine denies with
`deny_argument_policy`. The schema (`ArgumentSpecSchema`) and loader carry the new fields, so a policy declares
them in YAML — no code change per tool.

## 3. Discovery-time tool hiding (`13.3`)

`Engine.capabilities(agent_id)` already omits tools marked `hidden_for` a class. M13 adds: a tool the policy
**unconditionally denies** (a `deny` rule with `tool == <name>` and `action`/`environment`/`data_class` all `*`,
no condition gate) is hidden too — an agent never even sees a tool it cannot call. Hiding is **discovery-time
only**: a direct call to a hidden tool still goes through `evaluate` and is denied by policy, so hiding never
weakens enforcement.

## 4. Fail-closed / determinism

* A dimension with no validator declared is unconstrained (no accidental denials).
* Every validator is a pure function of the argument value (regex/enum/realpath/host) — deterministic.
* Tool hiding is derived from the policy, never a separate allowlist that could drift.

## 5. WBS M13 item mapping

| Item | Where |
|---|---|
| 13.D0 design docs first | this document |
| 13.1 exfil-sink rule class | `engine/exfil.py`, `packs/exfil-sink/` |
| 13.2 argument-level validation | `engine/argument_policy.py`, `policy/schema.py`, `policy/loader.py` |
| 13.3 discovery-time tool hiding | `engine/engine.py` (`capabilities`) |
| 13.T/13.C/13.L/13.CR/13.D | tests · coverage · ruff/mypy · [codereview-log](../wbs/v0.1.0/codereview-log.md) · [exfil/validators reference](../reference/exfil-and-validators.md) |
