"""Narrow-only policy layering (WBS M21 ``21.1`` / ``21.2``, CUJ-30 / R44).

A central **org baseline** plus **project** and **session** overlays, where a
child layer may only **restrict** — the AWS SCP pattern, enforced at load, never
a runtime surprise.

* :func:`compose` returns the **effective policy**: rules are concatenated
  parent-first, so the decision cascade (deny > allow > escalate) makes a **deny
  in any layer win** (union of restrictions, intersection of permits).
* :func:`narrow_only_violations` returns one finding per child ``allow`` rule that
  grants a scope the parent never allowed (a widening). The scope-containment
  test reuses :func:`agentpolicy.lint._broadens` (one definition, no drift).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from agentpolicy.lint import _broadens
from agentpolicy.policy.models import Policy

#: The layer order (outermost floor first).
LAYERS: tuple[str, ...] = ("org", "project", "session")


@dataclass(frozen=True)
class Layer:
    """One named policy layer (``org`` / ``project`` / ``session``)."""

    name: str
    policy: Policy

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("layer name must be a non-blank string")


def compose(layers: Sequence[Layer]) -> Policy:
    """Return the effective policy: the intersection of the layers.

    Rules are concatenated parent-first, so a deny in any layer wins. The
    non-rule fields (environments / data classes / agents) come from the **org**
    layer, so a child cannot re-weight the floor's risk model either.

    Raises:
        ValueError: *layers* is empty.
    """
    if not layers:
        raise ValueError("compose needs at least one layer")
    base = layers[0].policy
    rules = tuple(rule for layer in layers for rule in layer.policy.rules)
    return Policy(
        version=base.version,
        posture=base.posture,
        environments=base.environments,
        data_classes=base.data_classes,
        risk_weights=base.risk_weights,
        rules=rules,
        agents=base.agents,
        default_agent=base.default_agent,
        tool_visibility=base.tool_visibility,
        args_policy=base.args_policy,
        data_class_rules=base.data_class_rules,
    )


def narrow_only_violations(parent: Policy, child: Policy) -> list[str]:
    """Return one finding per child ``allow`` rule that widens the parent.

    A child ``deny`` / ``escalate`` / narrowed ``allow`` is never a violation
    (restricting is the point). An ``allow`` rule that is not covered by some
    parent ``allow`` rule ("``parent_r`` matches at least everything
    ``child_r`` matches") grants new scope and is a violation.

    Returns:
        A list of human-readable findings (empty == the child only narrows).
    """
    parent_allows = [rule for rule in parent.rules if rule.decision == "allow"]
    violations: list[str] = []
    for i, rule in enumerate(child.rules):
        if rule.decision != "allow":
            continue
        if not any(_broadens(allow, rule) for allow in parent_allows):
            violations.append(
                f"rules[{i}]: allow rule ({rule.tool}/{rule.action}/{rule.environment}/"
                f"{rule.data_class}) widens the parent policy; a child layer may only narrow"
            )
    return violations


__all__ = ["LAYERS", "Layer", "compose", "narrow_only_violations"]
