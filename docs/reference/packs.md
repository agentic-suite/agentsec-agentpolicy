# Rule Packs Reference

Rule packs are versioned, incident-anchored rule sets (WBS M4). Format + loader: `src/agentpolicy/pack_format.py`.

## Catalog

| Pack | Domains | Trust | Anchored to |
|---|---|---|---|
| `destructive-commands` | db, shell, cloud, git | launch | incident-register#6 (the "Replit rule") |
| `secret-in-output` | secrets, db | launch | incident-register#9 |
| `mcp-allowlist` | mcp | launch | incident-register#11 |
| `cloud-read` | cloud | community | — |
| `db-queries` | db | community | — |
| `fs-basics` | fs | community | — |
| `http-crud` | http | community | — |
| `shell-safe` | shell | community | — |

## Format

```
packs/<name>/
  metadata.yaml     # name, version, description, incident_ref, min_agentpolicy, license, trust, domains
  rules.cedar       # Cedar rules appended to the base policy (Cedar packs)
  tests.yaml        # version + fixtures: [{name, tool, action, environment, data_class, agent_id, [context], expect}]
```

A **Cedar pack** has `rules.cedar`; a **legacy catalog pack** has `tools.yaml`. `pack validate` / `pack test`
auto-detect the format.

## CLI

```sh
agentpolicy pack validate packs/destructive-commands   # exit 0 ok / 2 malformed
agentpolicy pack test     packs/destructive-commands   # replay fixtures; exit 0 all-pass
agentpolicy pack list                                  # catalog
agentpolicy pack info     destructive-commands
```

## Authoring a Cedar pack

1. Create `packs/<slug>/metadata.yaml` with a `name` equal to the directory slug and an `incident_ref`.
2. Add `rules.cedar` (Cedar `permit`/`forbid`; the base policy is always included).
3. Add `tests.yaml` fixtures — one per incident replay — with the expected outcome
   (`allow`/`deny`/`ask`/`rate-limit`/`redact`).
4. `agentpolicy pack validate <dir>` then `agentpolicy pack test <dir>`.

## OPA/Rego peer backend

```python
from agentpolicy.policy.opa import opa_evaluate
decision = opa_evaluate(call, "policy.rego", opa_binary="opa")
```

An unreachable/erroring OPA raises `OpaUnavailableError` (reason `deny_opa_backend_down`) — a deny, so an
outage never allows.
