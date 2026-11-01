# Delivery Surfaces & Adapters — Design (M8, v0.1.0)

**BLUF:** M8 exposes **one decision engine through every surface** — an in-process **library** call, the **CLI**,
an **MCP server**, and a local **HTTP PDP** — plus a **validated adapter registry** for harnesses/frameworks. All
surfaces call the same engine and return the **same decision**; a denial is **model-consumable** (a replan-able
rejection). This is the design of record (`8.D0`); it delivers **CUJ-2** (R28) and the PRD 19 harness
compatibility table.

> Status: **Done** — branch `feat-0.1.0`. Modules: `agentpolicy/api.py` (library), `adapters/registry.py`
> (registry), `server/` (MCP + HTTP), `cli/evaluate.py` (CLI).

---

## 1. Surface contract (one engine, N bindings)

Every surface is a thin binding over the same decision engine (`Engine` →
canonicalize → score → decide → explain), so a caller gets the same `Decision`
regardless of transport:

| Surface | Entry point | Returns |
|---|---|---|
| Library (`8.1`) | `agentpolicy.api.evaluate(...)` | `Decision` |
| CLI (`8.1`) | `agentpolicy evaluate …` | table / JSON, exit 2 on deny |
| MCP server (`8.2`) | tools `agentpolicy.evaluate` / `agentpolicy.explain` | tool result (the decision dict) |
| HTTP (`8.3`) | `POST /authorize` | JSON decision (HTTP 200; 400 on malformed input) |

**Same decision everywhere.** The surfaces do not score independently: the MCP
tools and the HTTP PDP both call `ServerCore.evaluate`, which calls the same
`Engine` the library surface (`api.evaluate`) and the CLI use — so the decision is
identical across transports (proved by the M8 parity test).

`agentpolicy.api.evaluate(...)` is the documented **15-line path**:

```python
from agentpolicy.api import evaluate

decision = evaluate(tool="drop_database", action="delete", environment="production",
                    data_class="customer_pii", agent_id="release-bot")
decision.decision      # "deny"
decision.reason_code   # "deny_critical_op"
```

It is **fail-closed**: the engine's `fail_closed` decorator turns an unknown tool /
malformed input / policy failure into a `deny` with the matching reason code —
never an exception and never an allow.

## 2. Adapter registry (`8.4`)

One registry (`agentpolicy/adapters/registry.py`) maps an adapter **name** to its class, the **extra** that
supplies its dependency, and a builder:

| Name | Class | Extra | Dependency |
|---|---|---|---|
| `raw` | `RawAdapter` | — | — |
| `mcp` | `AgentPolicyMCPWrapper` | `mcp` | `mcp` (client) |
| `langgraph` | `AgentPolicyToolNode` | `langgraph` | `langgraph`, `langchain-core` |
| `pydanticai` | `PydanticAIAdapter` | `pydanticai` | `pydantic-ai` |
| `openai` | `OpenAIAdapter` | `openai-agents` | `openai-agents` |
| `crewai` | `CrewAIAdapter` | `crewai` | `crewai` |
| `smolagents` | `SmolagentsAdapter` | `smolagents` | `smolagents` |
| `autogen` | `AutoGenAdapter` | `autogen` | `autogen-agentchat` |
| `llamaindex` | `LlamaIndexAdapter` | `llamaindex` | `llama-index-core` |
| `adk` | `AdkAdapter` | `adk` | `google-adk` |

* `available()` → every registered name.
* `get(name)` → the entry, or `ConfigError` for an unknown name.
* `load(name, engine, **kwargs)` → an adapter instance; **validated at load**: an unknown name, a name whose
  extra is not installed, or missing required kwargs (e.g. an MCP client) raises `ConfigError` (exit 2) — never a
  bare `ImportError` or an `AttributeError` deep in a call. This is the M8 acceptance: *unknown adapter →
  `ConfigError`*.
* `validate()` → the subset whose dependencies are importable (for doctor/CI).

## 3. Wiring into an enforcer (`8.5`)

Adapters wrap a tool so the decision runs **before** the tool does. On a non-allow outcome they reject in a way
the model can **replan** from:

* `adapters/base.py.denial_message(decision)` — the shared, model-consumable rejection sentence
  (`[AgentPolicy] deny: <explanation> (reason_code <code>)`).
* `RawAdapter.guard` raises `AgentPolicyDecisionError(decision)` (carrying `.decision`); the MCP wrapper returns
  an MCP `isError` result; the LangGraph/OpenAI/PydanticAI adapters return a tool message / rejection / retry
  respectively.

A reference enforcer is the `raw` adapter over `Engine`/`CedarEvaluator`: catch the rejection, read
`decision.reason_code`, and replan (e.g. switch a destructive action to a read-only alternative — the M5
`suggested_change`).

## 4. Harness compatibility (PRD 19)

See the [adapters reference](../reference/adapters.md) for the full table (framework → adapter → hook →
dependency). The registry is the single source that table is generated from.

## 5. WBS M8 item mapping

| Item | Where |
|---|---|
| 8.D0 design docs first | this document |
| 8.1 library surface | `agentpolicy/api.py`; `agentpolicy/__init__.py` |
| 8.2 MCP surface | `server/mcp_tools.py` (shipped) |
| 8.3 HTTP surface | `server/pdp_routes.py` (shipped) |
| 8.4 adapter registry | `agentpolicy/adapters/registry.py`; `adapters/__init__.py` |
| 8.5 wire into an enforcer | `adapters/base.py` (`denial_message`), `adapters/raw.py` |
| 8.T/8.C/8.L/8.CR/8.D | tests · coverage · ruff/mypy · [codereview-log](../wbs/v0.1.0/codereview-log.md) · [adapters reference](../reference/adapters.md) |
