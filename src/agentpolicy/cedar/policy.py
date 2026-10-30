"""The base Cedar policy and entity/request construction (M2 ``2.1``).

Cedar is the primary policy language (PRD 11 DD-02). This module ships the
**balanced** base policy as Cedar text plus the mapping from a canonical call
to a Cedar request ``(principal, action, resource, context)`` and its entities.

The policy is intentionally small but exercises all five outcomes jointly with
:mod:`agentpolicy.cedar.shaper`:

* reads in non-production → permit → ``allow``
* destructive verbs in production / on customer-PII → forbid → ``deny``
* irreversible verbs in production → permit → ``ask`` (human-gate class)
* sensitive reads → permit → ``redact``
* over-budget sessions → ``rate-limit`` (shaper, from session state)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agentpolicy.types import NormalizedCall

#: The balanced base policy, as Cedar.
BASE_POLICY = """
// agentpolicy base decision policy — balanced posture (v0.1.0)

@id("permit-read-nonprod")
permit (principal, action, resource)
when { context.verb == "read" && context.environment != "production" };

@id("forbid-destructive-production")
forbid (principal, action, resource)
when {
  (context.verb == "delete" || context.verb == "drop" || context.verb == "destroy"
   || context.verb == "force_push" || context.verb == "revoke") &&
  context.environment == "production"
};

@id("forbid-destructive-customer-pii")
forbid (principal, action, resource)
when {
  (context.verb == "delete" || context.verb == "drop" || context.verb == "destroy") &&
  context.data_class == "customer_pii"
};

@id("permit-write-development")
permit (principal, action, resource)
when { context.verb == "write" && context.environment == "development" };

@id("permit-sensitive-read")
permit (principal, action, resource)
when {
  context.verb == "read" &&
  (context.data_class == "restricted" || context.data_class == "customer_pii")
};

@id("permit-irreversible-production")
permit (principal, action, resource)
when {
  (context.verb == "write" || context.verb == "deploy" || context.verb == "send"
   || context.verb == "transfer" || context.verb == "grant") &&
  context.environment == "production"
};
"""


def build_entities(call: NormalizedCall) -> list[dict[str, Any]]:
    """Build the minimal Cedar entity store for a call.

    The tool is modelled as a ``Tool`` entity carrying its ``category`` so a
    policy can reference ``resource.category`` if it wants to.
    """
    return [
        {
            "uid": {"type": "Tool", "id": call.tool},
            "attrs": {"category": call.tool_category},
            "parents": [],
        }
    ]


def to_request(
    call: NormalizedCall, *, extra_context: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Map a canonical call to a Cedar authorization request."""
    context: dict[str, Any] = {
        "verb": call.action,
        "environment": call.environment,
        "data_class": call.data_class,
        "tool_category": call.tool_category,
        "action_class": call.action_class,
        "agent_class": call.agent_class,
    }
    if extra_context:
        context.update(extra_context)
    return {
        "principal": {"type": "Agent", "id": call.agent_id},
        "action": {"type": "Action", "id": call.action},
        "resource": {"type": "Tool", "id": call.tool},
        "context": context,
    }
