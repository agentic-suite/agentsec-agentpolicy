# agentpolicy — M0 Porting Plan & Ported-Tree Architecture (v0.1.0)

**BLUF:** M0 makes agentpolicy self-contained by bulk-porting the predecessor policy engine
(`agent-tooltrust`, MIT) into this repository, renaming the namespace and tool, and getting the ported
suite green. This document is the **design of record for the port** (WBS `0.D0`) and describes the
**ported tree** (WBS `0.7`/`0.D`). Later milestones (M2–M23) re-point the decision mechanics from the
predecessor's bespoke Python risk scorer to a **Cedar PDP**; M0 deliberately does **not** change behavior.

> Status: **Done** — ported on branch `feat-0.1.0`. Source SHA recorded below.

---

## 1. Source & provenance

| Field | Value |
|---|---|
| Predecessor | `agent-tooltrust` — contextual risk & permission engine for tool-using AI agents |
| Repository | `agentic-suite/agent-tooltrust` (archived; retained **private, never deleted**) |
| License | MIT |
| **Source commit (SHA)** | `31655747ee4290b80adb04b2a300dd991b80e018` (`Add deprecation notice pointing to successor`) |
| Source short desc | `v0.2.0-7-g3165574` |

History is preserved non-destructively: the predecessor is added as a git remote and fetched, so its full
history (62 commits) is present in this repository's object database under `refs/remotes/predecessor/main`.
No existing agentpolicy history was rewritten. MIT attribution lives in [`THIRD_PARTY_NOTICES.md`](../../THIRD_PARTY_NOTICES.md).

---

## 2. What was ported (inventory)

| Artifact | Ported | Notes |
|---|---|---|
| `src/agentpolicy/` | 100 modules, ~14.1k LOC | `engine`, `policy`, `audit`, `cli`, `adapters`, `server`, `analytics`, `field`, `integrations`, `taxonomy`, `types`, `mcp_data` |
| `tests/` | 88 modules (+ `field/`, `ui/`) | unit + integration + fault-injection + golden fixtures |
| `packs/` | 5 packs | `cloud-read`, `db-queries`, `fs-basics`, `http-crud`, `shell-safe` |
| `scripts/` | field-agent runner + downloader | — |
| `examples/` | demo agent + adversarial variant | — |
| Packaging/build | `pyproject.toml`, `Makefile`, `Dockerfile`, `docker-compose.yml`, `.dockerignore` | adapted (see §4) |
| CI | `.github/workflows/ci.yml` + issue/PR templates | replaced the placeholder CI |
| Docs subset | `docs/architecture`, `docs/design`, `docs/reference`, `docs/explanation`, `docs/test`, `docs/real-agent-integration`, `docs/fixtures`, `docs/SECURITY_BASELINE.md`, `docs/examples.md` | predecessor's subsystem/API docs |
| **Not ported** | predecessor `docs/wbs`, `docs/field-test` | agentpolicy has its own WBS/field-test trees |

## 3. Namespace & tool rename

Case-correct, whole-tree (233 files) replacement:

| Before | After |
|---|---|
| `agent_tooltrust` (package) | `agentpolicy` |
| CLI `tooltrust` | `agentpolicy` |
| dist `agent-tooltrust` | `agentsec-agentpolicy` |
| `ToolTrust` / `Agent ToolTrust` | `AgentPolicy` |
| `TOOLTRUST_*` (env) | `AGENTPOLICY_*` |
| `tooltrust.yaml`, `~/.tooltrust/`, `/etc/tooltrust/` | `agentpolicy.yaml`, `~/.agentpolicy/`, `/etc/agentpolicy/` |
| `tooltrust:latest`, `ToolTrustMCPWrapper`, `ToolTrustDecisionError`, `parse_tooltrust_yaml` | `agentpolicy:latest`, `AgentPolicyMCPWrapper`, `AgentPolicyDecisionError`, `parse_agentpolicy_yaml` |
| files `tooltrust_mcp.py`, `results/tooltrust-mcp/` | `agentpolicy_mcp.py`, `results/agentpolicy-mcp/` |
| URLs `deghosal-2026/agent-tooltrust`, `anomalyco/agent-tooltrust` | `agentic-suite/agentsec-agentpolicy` |

**Deliberately unchanged:** agentpolicy's own `docs/prd/`, `docs/wbs/`, `docs/adr/` name the predecessor on
purpose. Enforced by [`tests/test_namespace_rename.py`](../../tests/test_namespace_rename.py) (zero
predecessor-namespace references in code/config).

## 4. Packaging

- Distribution `agentsec-agentpolicy`, wheel packages `["src/agentpolicy"]`, console entry point
  `agentpolicy = "agentpolicy.cli:main"`.
- **Project version set to `0.1.0`** (the port carried the predecessor's `0.2.0`; corrected).
- `pip install -e .` verified: installs `agentsec-agentpolicy==0.1.0`; `agentpolicy --help` lists the surface.

## 5. Ported-tree architecture (unchanged from the predecessor)

```
 Tool Call → NORMALIZE → SCORE → DECIDE → EXPLAIN → AUDIT
```

| Package | Responsibility |
|---|---|
| `engine/` | decision pipeline: `normalize`, `score`, `decide`, `explain`, `fail_closed`, `escalation`, budgets, obligations, deny-storm, delegation, argument policy |
| `policy/` | policy model + loader + schema, posture presets, packs, OPA/Rego backend |
| `audit/` | JSONL/SQLite/Postgres sinks, redaction, replay, tamper-evident hash chain |
| `cli/` | `agentpolicy` command surface (`evaluate`, `explain`, `check`, `init`, `audit`, `pack`, `report`, `doctor`, `serve`, `field-test`, …) |
| `adapters/` | raw, MCP, LangGraph, PydanticAI, OpenAI Agents, CrewAI, smolagents, LlamaIndex, AutoGen, ADK |
| `server/` | MCP server + HTTP PDP routes (`/authorize`), dashboards, session store |
| `analytics/` | cross-session analyzer |
| `field/` | field-test harness + report |
| `integrations/` | OPAL sync, SWE-bench |

## 6. Gates (M0 exit criteria)

| Gate | Result |
|---|---|
| Ported suite (`pytest`) | **1084 passed, 18 skipped, 1 deselected** |
| Coverage | **≥ 95%** (`fail_under = 95`) |
| `ruff` | **zero violations** |
| `mypy --strict src/` | **clean (100 files)** |

## 7. Known port findings (recorded, not fixed in M0)

- **Shipped packs use the predecessor's older YAML shape** (`environments: {development: 0.0}` as bare
  floats) which the current `PolicyDocument` schema rejects, so `agentpolicy pack validate`/`load_policy`
  fail on `packs/*/tools.yaml`. Verified **pre-existing** (the predecessor's own loader rejects them).
  Pack content is owned by **M4 (rule packs)**.
- **Field tests** (`-m field`) are excluded by the default pytest config and require real framework
  packages + vendor checkouts; they run in their own CI job.
- **Docker-dependent tests** (`test_docker_smoke`, `test_sse_integration`, `test_docker_console`, `ui`)
  skip when no Docker daemon is reachable and run in the docker CI job.

## 8. WBS M0 item mapping

| Item | Where |
|---|---|
| 0.D0 design docs first | this document |
| 0.1 port tree · 0.2 rename · 0.4 packaging | §2, §3, §4 |
| 0.3 preserve history | §1 (SHA + fetched ref) |
| 0.5 suite green · 0.T/0.C/0.L gates | §6 |
| 0.6 provenance · 0.7/0.D docs | `THIRD_PARTY_NOTICES.md`, `CHANGELOG.md`, this document |
