# Normalization, Taxonomy & Contextual Model — Design (M3, v0.1.0)

**BLUF:** M3 turns *anything* an agent emits into one **canonical action** and decides it from the contextual
model. Every surface — MCP `tools/call`, a framework tool node, raw Python, HTTP, or a coarse dispatcher
string — funnels into a single canonical `NormalizedCall` `(principal, action, resource, context)` that the
Cedar decision core evaluates. This is the design of record (`3.D0`).

> Status: **Done** — branch `feat-0.1.0`. Facade: `src/agentpolicy/canonical.py`.

---

## 1. The canonical action (`3.1`)

`canonicalize(tool, action, environment, data_class, agent_id, agent_class=…, arguments=…, context=…)`
→ `NormalizedCall`. This is the one shape both the normalizer and the evaluator agree on; it folds the tool
name, resolves the taxonomy domain + action class, and carries the agent class and session context.

`to_cedar_request(call)` maps it to the Cedar request `(principal, action, resource, context)`
(see [cedar-decision-core](cedar-decision-core.md)).

## 2. Tool-name normalization (`3.2`)

Before matching, the tool name is whitespace-collapsed and Unicode-folded
(`engine/normalize.py::_normalize_tool_name`). An unknown normalized name raises `UnknownToolError`, which
the engine maps to a **fail-closed deny** (`unknown_action`) — an obfuscated/unknown name is never allowed.

## 3. Dispatcher-bypass safety (`3.3`)

`canonicalize_command(raw, kind=…)` parses a coarse string (`bash`/`git`/`http`/`aws`) into a canonical
`(tool, action)` and normalizes it, so a smuggled action evaluates against the *same* policy as a direct call:

| Raw | Canonical |
|---|---|
| `git push --force` | `git_push` / `force_push` (action class `delete`) |
| `rm -rf /` | `execute_shell` / `exec` |

Demo: `git push --force` in production is **denied** by the base Cedar policy (destructive verb + production),
identical to a direct `git_push` call with `force_push`.

## 4. Action taxonomy (`3.4`)

The 13-domain taxonomy (`taxonomy/__init__.py`) maps a tool → domain and an action verb → action class
(`read`/`write`/`delete`/`grant`), each with a baseline risk. `register_tool` extends it at runtime (MCP-Data).
See the [taxonomy reference](../reference/taxonomy.md).

## 5. Contextual model (`3.5`)

The same tool/action scores differently across the five dimensions (tool category, action class, environment,
data sensitivity, agent class) plus session state; custom dimensions can be registered
(`engine/risk_dimensions.py`). Demonstrated by the contextual matrix in `tests/test_m3_canonical.py`:

| tool / action | environment | data class | outcome |
|---|---|---|---|
| `query_logs` / `read` | staging | internal | `allow` |
| `query_logs` / `read` | production | internal | `deny` |
| `query_logs` / `read` | production | restricted | `redact` |

## 6. WBS M3 item mapping

| Item | Where |
|---|---|
| 3.D0 | this document |
| 3.1 canonical action | `canonical.py` (§1) |
| 3.2 tool-name normalization | `engine/normalize.py` (§2) |
| 3.3 dispatcher safety | `canonical.py`, `engine/dispatcher.py` (§3) |
| 3.4 taxonomy | `taxonomy/__init__.py` (§4) |
| 3.5 contextual model | `engine/risk_dimensions.py` + Cedar context (§5) |
| 3.T/3.C/3.L/3.CR/3.D | `tests/test_m3_canonical.py` · gates · [codereview-log](../wbs/v0.1.0/codereview-log.md) · [taxonomy reference](../reference/taxonomy.md) |
