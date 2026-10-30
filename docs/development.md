# Development

How to work on **agentpolicy**. (Ported tree — see
[porting-plan-v0.1.0.md](architecture/porting-plan-v0.1.0.md).)

## Prerequisites

- Python **3.11+** (CI uses 3.13)
- [`uv`](https://docs.astral.sh/uv/) (recommended) or plain `venv`/`pip`

## Setup

```sh
python -m venv .venv && . .venv/bin/activate
pip install -e .                                  # editable install (core deps)
pip install pytest pytest-cov hypothesis ruff mypy types-PyYAML asyncpg httpx fastmcp mcp
```

Framework adapters are optional extras (`pip install -e ".[langgraph]"`, `.[crewai]`, …). They are only needed
for the field tests and the corresponding adapter tests.

## Quality gates

```sh
pytest                                            # ported suite (default config; `field` excluded)
pytest --cov=agentpolicy --cov-report=term-missing   # coverage, gate ≥ 95% (fail_under = 95)
ruff check .                                      # zero violations
mypy --strict src/                                # strict-clean
```

### Test markers / jobs

- The default config (`-ra -m 'not field'`) runs the fast suite and **excludes** `field` tests.
- `pytest -m field` runs the field tests — they drive real framework packages and need the vendor checkouts
  from `scripts/download_field_agents.sh`; they run in their own CI job.
- Docker-dependent tests (`test_docker_smoke`, `test_sse_integration`, `test_docker_console`, `tests/ui`) skip
  when no Docker daemon is reachable and are exercised by the docker CI jobs.

## Project layout (ported tree)

```
src/agentpolicy/
  engine/    decision pipeline: normalize → score → decide → explain → audit
  policy/    policy model + loader + schema, posture presets, packs, OPA/Rego backend
  audit/     JSONL/SQLite/Postgres sinks, redaction, replay, tamper-evident hash chain
  cli/       `agentpolicy` command surface
  adapters/  raw, MCP, LangGraph, PydanticAI, OpenAI Agents, CrewAI, … framework guards
  server/    MCP server + HTTP PDP routes, dashboards, session store
  analytics/ cross-session analyzer
  field/     field-test harness + report
  integrations/  OPAL sync, SWE-bench
tests/       ported suite + field/ + ui/
packs/       5 shipped rule packs
```

## Conventions

- Conventional Commits, **DCO-signed** (`git commit -s`).
- One ticket at a time (RED → GREEN); run the milestone gates once at milestone end.
- No ML/network in any decision path.
