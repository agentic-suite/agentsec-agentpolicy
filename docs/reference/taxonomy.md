# Action Taxonomy Reference

The 13-domain taxonomy (WBS M3) maps every tool to a domain and every action verb to an action class, so a
decision is portable across harnesses. Source: `src/agentpolicy/taxonomy/__init__.py`.

## Domains

| Domain | Example verbs | Baseline risk |
|---|---|---|
| `fs` (filesystem) | read, write, delete, list, move | low→high |
| `shell` | exec, pipe | high |
| `http` | get, post, put, delete, patch | low→med |
| `db` (database) | query, execute, migrate, drop | low→critical |
| `git` (version control) | status, diff, log, commit, push, force_push | low→critical |
| `email` | read, send, delete, search | low→high |
| `cloud` (infra) | list, describe, create, update, delete, scale | low→critical |
| `secrets` | read, write, rotate, revoke | critical |
| `iam` (identity) | read_role, assign_role, revoke_role, create_key | high→critical |
| `payment` | read, refund, transfer, charge | med→critical |
| `approval` | read, approve, deny, delegate | med→critical |
| `search` | query, index, delete_index | low→med |
| `notify` | send_slack, send_teams, send_webhook, page | low→high |

## Action classes

Every verb resolves to one of four classes: `read` · `write` · `delete` · `grant`.

## API

```python
from agentpolicy.taxonomy import DOMAINS, domain_for, action_class_for, is_known_tool, register_tool

domain_for("drop_database")     # "db"
action_class_for("delete")      # "delete"
is_known_tool("made_up")        # False
register_tool("my_internal_tool", "db")   # extend at runtime (MCP-Data)
```

## Canonical action

```python
from agentpolicy.canonical import canonicalize, canonicalize_command, to_cedar_request

call = canonicalize(tool="Query_Logs", action="read",
                    environment="staging", data_class="internal", agent_id="debug-bot")
call.tool          # "query_logs" (folded)
call.tool_category # "search"
call.action_class  # "read"

call = canonicalize_command("git push --force", kind="git",
                            environment="production", data_class="internal", agent_id="release-bot")
call.action        # "force_push"
```
