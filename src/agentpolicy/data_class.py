"""Data-class derivation (WBS M15 ``15.3``, CUJ-21 / R34).

Derive a resource's ``data_class`` deterministically instead of hand-tagging
everything: an explicit **tag** wins, then the first matching **glob**, then a
**schema hint**. A **conflict fails loudly** — two rules of the same precedence
matching with different classes raises :class:`DataClassConflictError`, never a
silent pick.
"""

from __future__ import annotations

import fnmatch
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from agentpolicy.errors import AgentPolicyError

#: Reason code for an unresolvable data-class derivation.
REASON_DATA_CLASS_CONFLICT = "deny_data_class_conflict"


class DataClassConflictError(AgentPolicyError):
    """Two derivation rules of the same precedence disagreed on the class."""

    reason_code = REASON_DATA_CLASS_CONFLICT


@dataclass(frozen=True)
class DataClassRule:
    """A glob rule mapping a resource pattern to a data class."""

    pattern: str
    data_class: str

    def matches(self, resource: str) -> bool:
        """Whether *resource* matches this glob (``fnmatch`` semantics)."""
        return fnmatch.fnmatch(resource, self.pattern)


def derive_data_class(
    resource: str,
    rules: Sequence[DataClassRule],
    *,
    resource_tags: Sequence[str] = (),
    tag_map: Mapping[str, str] | None = None,
    schema_hint: str | None = None,
) -> str | None:
    """Resolve *resource* to a data class, or ``None`` when nothing matches.

    Precedence: **tag** (``tag_map`` on any of ``resource_tags``) → **glob**
    (``rules``, first precedence block) → **schema hint**.

    Args:
        resource: The resource path/id (e.g. a file path or a table name).
        rules: Glob rules, in declaration order.
        resource_tags: The tags the resource carries.
        tag_map: tag name → data class.
        schema_hint: A data class implied by the resource's schema.

    Returns:
        The resolved data class, or ``None``.

    Raises:
        DataClassConflictError: two tags, or two globs, resolve to different
            classes — the derivation is ambiguous and must not guess.
    """
    if tag_map and resource_tags:
        classes = {tag_map[tag] for tag in resource_tags if tag in tag_map}
        if len(classes) > 1:
            raise DataClassConflictError(
                f"resource {resource!r} carries conflicting tags → {sorted(classes)}"
            )
        if classes:
            return classes.pop()

    matched = {rule.data_class for rule in rules if rule.matches(resource)}
    if len(matched) > 1:
        raise DataClassConflictError(
            f"resource {resource!r} matches conflicting glob rules → {sorted(matched)}"
        )
    if matched:
        return matched.pop()

    return schema_hint


def rule_from_dict(data: Mapping[str, Any]) -> DataClassRule:
    """Build a :class:`DataClassRule` from a mapping."""
    return DataClassRule(pattern=str(data["pattern"]), data_class=str(data["data_class"]))


__all__ = [
    "REASON_DATA_CLASS_CONFLICT",
    "DataClassConflictError",
    "DataClassRule",
    "derive_data_class",
    "rule_from_dict",
]
