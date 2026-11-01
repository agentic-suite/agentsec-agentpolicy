# Exfil-sink, argument validators & tool hiding — reference (v0.1.0)

WBS M13 · CUJ-13 · R10 / R19 / R21. Design: [exfil-validators-hiding.md](../design/exfil-validators-hiding.md).

## Exfil-sink (`13.1`)

A call that sends **sensitive** data (`restricted` / `customer_pii`) to an **external-sink** tool (an `http` /
`email` / `notify` domain) with an outbound verb is denied with a reason that names the source **and** the sink:

```python
from agentpolicy.engine.engine import Engine
from agentpolicy.policy.models import default_policy

Engine(default_policy("balanced")).evaluate(
    tool_name="send_email", action="write", environment="production",
    data_class="restricted", agent_id="release-bot",
).reason_code   # "deny_exfil_sink"
```

The shipped `packs/exfil-sink` pack carries the `@id("exfil-sink-block")` Cedar rule + an incident replay.

## Argument validators (`13.2`)

Declare per-argument constraints under `tools[].args_policy`:

```yaml
tools:
  - name: run_query
    args_policy:
      sql:        { regex: '(?i)^\s*select\b' }      # SELECT-only
      limit:      { max: 1000 }                       # range cap
      mode:       { enum: [fast, safe] }              # closed set
      path:       { path_root: /srv/data }            # traversal containment
      url:        { url_allowlist: [api.example.com] }# SSRF allowlist
```

| Validator | Field | Catches |
|---|---|---|
| regex | `regex` | SELECT-only / statement shape |
| range | `min` / `max` | refund cap, row limit |
| enum | `enum` (or `allowed`) | closed value sets |
| path containment | `path_root` | `../` traversal |
| URL allowlist | `url_allowlist` | SSRF (e.g. `169.254.169.254`) |

A violation denies with `deny_argument_policy` and names the offending argument.

## Tool hiding (`13.3`)

```python
Engine(policy).capabilities("release-bot")
```

Omits tools that are `hidden_for` the agent class **and** tools the policy **unconditionally denies**. Hiding is
discovery-time only — a direct call still goes through `evaluate` and is denied by policy.
