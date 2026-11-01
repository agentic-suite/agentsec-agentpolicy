# AgentPolicy v0.1.0 Release Notes

**Released:** 2026-11-01
**Package:** `agentsec-agentpolicy` · **Version:** 0.1.0
**License:** Apache-2.0

AgentPolicy is a deterministic policy decision point for tool-using AI
agents. It scores every tool invocation across five risk dimensions and returns
one of four decisions — **allow, audit, escalate, deny** — with a fully
explainable, auditable, fail-closed policy. This is the first stable release.

---

## What shipped

### The decision pipeline

```
 Tool Call → NORMALIZE → SCORE → DECIDE → EXPLAIN → AUDIT
```

Every call produces a complete `Decision` (verdict, criticality, reason code,
human explanation, risk factors, escalation id). Any stage that fails closes to
a **deny** — never an exception surfacing, and never a silent allow.

| Decision | Meaning | Example |
|----------|---------|---------|
| **Allow** | Execute normally | read of internal data in staging |
| **Audit** | Allow + enhanced logging | delete in staging by a trusted agent |
| **Escalate** | Human approval required | write/deploy in production |
| **Deny** | Blocked with reason | delete in production, PII access |

### Integration options

- **Raw Python** — `@engine.guard` decorator + session context manager.
- **Framework adapters** — LangGraph, PydanticAI, OpenAI Agents SDK, CrewAI,
  AutoGen, LlamaIndex, SmolAgents, Google ADK.
- **MCP** — an MCP server exposing `evaluate`, `explain`, and
  `session_status` (SSE transport); plus a client wrapper for MCP
  `tools/call` proxying.
- **Docker** — containerized server with health endpoint and SSE integration
  tests (`docker compose up`).

### Security posture

- **Adversarial normalization** (F-89 P0): NFKC + case-fold + confusable
  transliteration blocks Unicode / homoglyph tool-name obfuscation.
- **Fail-closed by default**: unknown tool, blank input, or malformed call →
  deny.
- **Shadow / dry-run mode** to preview policy without blocking.
- **Policy presets**: balanced / strict / permissive, YAML `agentpolicy.yaml`,
  OPA/Rego backend, hot-reload.
- **Audit trail**: JSONL / SQLite / Postgres sinks with a tamper-evident hash
  chain and `agentpolicy audit` CLI.
- **Governance**: OWASP Agentic Top 10 mapping (5/10 covered in v0.1),
  security baseline, arg validators (path-traversal, URL), output inspector
  (secrets / PII / injection), and tool scanning.

### Field validation

- **83-agent roster** across 10 agent frameworks.
- **Decision matrix**: 2,490 assertions, Plan A 83/83 (100% green), plus 100
  adversarial assertions.
- **Model replan round-trip**: deny → different tool → allow, with a CI-safe
  deterministic (scripted) mode (8/8) and an optional live LLM mode.
- **SWE-bench integration** (`agentpolicy swebench`) replays coding-agent
  benchmarks with per-task violation traces.

### CLI

```bash
agentpolicy init --posture balanced
agentpolicy evaluate ...        # one-shot decision
agentpolicy explain ...         # human-readable reasoning
agentpolicy check FILE          # policy check
agentpolicy diff A.yaml B.yaml  # policy diff
agentpolicy scan TARGET         # tool scanning
agentpolicy audit               # audit trail
agentpolicy report              # governance reports
agentpolicy test                # test runner
agentpolicy field-test          # field matrix + replan sweep
agentpolicy swebench            # SWE-bench benchmark
```

See the [CLI reference](api.md) for full usage.

---

## Demo

A runnable [demo agent](../examples.md) shows the full decision
spectrum in one session — allow → audit → escalate → deny → replan — plus an
adversarial variant that correctly denies prompt injection and Unicode
obfuscation. Run:

```bash
python examples/demo-agent/demo.py
python examples/demo-agent/demo_adversarial.py
```

---

## Quality gates (v0.1.0)

| Gate | Result |
|------|--------|
| Unit + integration tests | 564 passing |
| Field test matrix | 2,490 / 2,490 passing (100%) |
| Replan round-trip | 8/8 (scripted) |
| Ruff | 0 errors |
| Mypy (--strict) | 0 errors |
| Test coverage baseline | 85% (raised in v0.2) |

---

## Known limitations

- **OWASP Agentic Top 10**: 5/10 risks covered in v0.1.0; remaining 5 (arg
  validation, rate limiting, output inspection depth, child delegation,
  tool hiding) target v0.2+.
- **OpenSSF Silver / Sigstore / PyPI publish** are staged for this release
  gate and not yet live.
- **Live replan** field sweep needs a local LLM endpoint (omlx); the
  scripted (CI-safe) path is the default.

---

## Compatibility matrix (harness × enforcer)

How agentpolicy is reached, per harness, and where the decision is enforced. A
cell is marked supported **only** when it is field-tested (M24) or shipped and
verified; an untested surface is named *not supported*, never claimed.

| Harness | Reached via | Enforcer | v0.1.0 |
|---|---|---|---|
| **Claude Code** | `PreToolUse` hook → `agentpolicy evaluate` | in-process hook | ✅ field-tested LIVE (M24) |
| **Codex CLI** | `config.toml` provider + sandbox | in-process / sandbox | ✅ field-tested LIVE (M24) |
| **MCP clients** | MCP server surface / **agentgate** proxy | agentgate (MCP) | ✅ (MCP self-test) |
| **LangGraph** | library adapter (tool node) | in-process adapter | ✅ field-tested LIVE |
| **PydanticAI** | library adapter (`@guard`) | in-process adapter | ✅ field-tested LIVE |
| **OpenAI Agents SDK** | library adapter (guardrail) | in-process adapter | ✅ field-tested LIVE |
| **CrewAI** | library adapter (tool wrapper) | in-process adapter | ✅ field-tested LIVE |
| **AutoGen** | library adapter | in-process adapter | ✅ field-tested LIVE |
| **smolagents** | library adapter | in-process adapter | ✅ field-tested LIVE |
| **LlamaIndex** | library adapter | in-process adapter | ✅ field-tested LIVE |
| **Google ADK** | library adapter (LiteLlm) | in-process adapter | ✅ field-tested LIVE |
| **GitHub Copilot** (agent mode) | enterprise/process layer | **agentseatbelt** (confinement) | documented lower-layer (not field-tested) |
| **Cursor** | — | — | ❌ **not supported** (GUI IDE; no headless surface) |
| **Gemini CLI** | — | — | ❌ **not supported** (classifier-only local routing; sunset OAuth) |

**Enforcers:** `agentgate` (MCP proxy) and `agentseatbelt`/`agentkernel`
(confinement) are harness-agnostic decision callers; the in-process adapters are
per-framework. Every supported row is described in
[PRD 19](../prd/19-harness-compatibility.md).

---

## What's coming in v0.2.0

- Remaining OWASP coverage (9/10) and AgentPolicy **Hardened** baseline.
- Session/context state, escalation round-trip, tool hiding/hardening.
- Distributed policy sync and OpenSSF Silver / Gold aspiration.

---

## Links

- [CHANGELOG](../../CHANGELOG.md)
- [API Reference](api.md)
- [Architecture](../architecture/architecture-v0.1.0.md)
- [Demo Agent](../examples.md)
- [PRD](../design/PRD.md)
- [WBS](../wbs/v0.1.0/wbs-v0.1.0-index.md)
