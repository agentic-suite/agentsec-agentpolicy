# Delivery surfaces & adapters — reference (v0.1.0)

WBS M8 · CUJ-2 · R28. Design: [delivery-surfaces.md](../design/delivery-surfaces.md).

## Surfaces (one engine, N bindings)

| Surface | How | Entry |
|---|---|---|
| Library | in-process Python | `agentpolicy.api.evaluate(tool=…, action=…, environment=…, data_class=…, agent_id=…)` |
| CLI | shell | `agentpolicy evaluate …` (exit 2 on deny) |
| MCP server | MCP tools | `agentpolicy serve` → tools `agentpolicy.evaluate` / `agentpolicy.explain` |
| HTTP PDP | REST | `agentpolicy serve` → `POST /authorize` |

All four call the same engine, so the decision is identical for the same call.

```python
from agentpolicy.api import evaluate

decision = evaluate(tool="drop_database", action="delete", environment="production",
                    data_class="customer_pii", agent_id="release-bot")
print(decision.decision, decision.reason_code)   # deny deny_critical_op
```

The library surface is fail-closed: an unknown tool or malformed input yields a `deny` (`deny_unknown_tool` /
`deny_malformed_input`), never an exception and never an allow.

## Adapter registry

```python
from agentpolicy.adapters import registry

registry.available()                       # every registered adapter name
registry.validate()                        # the subset loadable here (deps installed)
adapter = registry.load("raw", engine)     # validated at load
registry.load("nope", engine)              # raises ConfigError (exit 2)
```

Load is **validated**: an unknown name, a missing optional dependency, or a missing required kwarg raises
`ConfigError` (exit 2) — never a bare `ImportError`.

| Name | Class | Extra | Framework hook |
|---|---|---|---|
| `raw` | `RawAdapter` | — | decorator `guard(...)` / `intercept(ctx)`; raises `AgentPolicyDecisionError` |
| `mcp` | `AgentPolicyMCPWrapper` | `mcp` | proxies MCP `tools/call`; returns an `isError` result on deny |
| `langgraph` | `AgentPolicyToolNode` | `langgraph` | a LangGraph tool node |
| `pydanticai` | `PydanticAIAdapter` | `pydanticai` | guardrail (`on_deny="error"` / `"retry"`) |
| `openai` | `OpenAIAdapter` | `openai-agents` | tool guardrail (`reject_content`) |
| `crewai` | `CrewAIAdapter` | `crewai` | `wrap_tool` |
| `smolagents` | `SmolagentsAdapter` | `smolagents` | `wrap_tool` |
| `autogen` | `AutoGenAdapter` | `autogen` | `wrap_tool` (sync + async) |
| `llamaindex` | `LlamaIndexAdapter` | `llamaindex` | `wrap_tool` |
| `adk` | `AdkAdapter` | `adk` | `wrap_tool` |

Install an adapter's extra, e.g. `pip install 'agentsec-agentpolicy[langgraph]'`.

## Harness compatibility (PRD 19)

A rejected call is **model-consumable** — every adapter renders the shared
`agentpolicy.adapters.base.denial_message(decision)` (`[AgentPolicy] <outcome>: <explanation> (reason_code
<code>)`), so the model can read the reason and replan (e.g. switch a destructive action to a read-only one).

| Framework | Adapter | Rejection shape | Replan-friendly |
|---|---|---|---|
| plain Python | `raw` | `AgentPolicyDecisionError(decision)` | yes (`.decision.reason_code`) |
| MCP client | `mcp` | `{"isError": true, "content": […]}` | yes |
| LangGraph | `langgraph` | `ToolMessage` with the denial message | yes |
| PydanticAI | `pydanticai` | error string / `ModelRetry` | yes |
| OpenAI Agents SDK | `openai` | `reject_content` | yes |
| CrewAI / smolagents / AutoGen / LlamaIndex / ADK | respective | error string / raised error | yes |
