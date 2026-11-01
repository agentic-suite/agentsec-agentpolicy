"""Policy lint (WBS M9 ``9.4``, CUJ-17 / R12).

Deterministic, no-ML checks over a loaded :class:`~agentpolicy.policy.models.Policy`
and its raw text. Each finding carries a machine code, a severity, a human
message, and a **location** so a CI job can fail and a human can jump to the
line. See ``docs/reference/postures-and-lint.md``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from agentpolicy.engine.output_inspector import _PII_PATTERNS, _SECRET_PATTERNS
from agentpolicy.policy.models import Policy, Rule
from agentpolicy.taxonomy import is_known_tool

#: Finding codes.
UNREACHABLE_RULE = "unreachable_rule"
OVER_PERMISSIVE_ALLOW = "over_permissive_allow"
UNKNOWN_TOOL_RULE = "unknown_tool_rule"
OUTCOME_CONFLICT = "outcome_conflict"
LITERAL_SECRET = "literal_secret"  # noqa: S105 - a finding code, not a password

_FIELDS = ("tool", "action", "environment", "data_class")


@dataclass(frozen=True)
class Finding:
    """One lint finding.

    Attributes:
        code: The machine-readable finding code.
        severity: ``error`` (must fix) or ``warning``.
        message: A human explanation.
        location: Where the finding is (e.g. ``rules[2]`` or ``text``).
    """

    code: str
    severity: str
    message: str
    location: str

    def to_dict(self) -> dict[str, Any]:
        """JSON-friendly representation."""
        return {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "location": self.location,
        }


def _broadens(broader: Rule, narrower: Rule) -> bool:
    """Whether *broader* matches at least everything *narrower* matches.

    True when, for every constraint field, *broader* is a wildcard or equals
    *narrower*'s value, and *broader* carries no extra condition gate.
    """
    if broader.conditions:
        return False
    return all(
        getattr(broader, field) == "*" or getattr(broader, field) == getattr(narrower, field)
        for field in _FIELDS
    )


def _constraints(rule: Rule) -> tuple[Any, ...]:
    return tuple([*(getattr(rule, field) for field in _FIELDS), tuple(rule.conditions)])


def lint_policy(policy: Policy, *, text: str = "") -> list[Finding]:
    """Lint a policy; return every finding (empty == clean).

    Args:
        policy: The loaded policy.
        text: The raw policy text (for the literal-secret scan).

    Returns:
        A list of :class:`Finding`, ordered by location.
    """
    findings: list[Finding] = []
    rules = policy.rules

    for i, rule in enumerate(rules):
        location = f"rules[{i}]"
        if rule.decision == "allow" and all(
            getattr(rule, field) == "*" for field in _FIELDS
        ) and not rule.conditions:
            findings.append(
                Finding(
                    OVER_PERMISSIVE_ALLOW, "error",
                    "allow rule has no constraints (permits every action)", location,
                )
            )
        if rule.tool != "*" and not is_known_tool(rule.tool):
            findings.append(
                Finding(
                    UNKNOWN_TOOL_RULE, "warning",
                    f"rule names tool {rule.tool!r} which is not in the taxonomy", location,
                )
            )
        for j in range(i):
            earlier = rules[j]
            if earlier.decision == rule.decision and _broadens(earlier, rule):
                findings.append(
                    Finding(
                        UNREACHABLE_RULE, "warning",
                        f"rule is shadowed by the broader rules[{j}] and can never fire",
                        location,
                    )
                )
                break

    for i, rule in enumerate(rules):
        key = _constraints(rule)
        for j in range(i):
            other = rules[j]
            if _constraints(other) == key and other.decision != rule.decision:
                findings.append(
                    Finding(
                        OUTCOME_CONFLICT, "error",
                        f"rule conflicts with rules[{j}] "
                        f"({other.decision!r} vs {rule.decision!r}) on identical constraints",
                        f"rules[{i}]",
                    )
                )
                break

    findings.extend(_scan_secrets(text))
    for i, rule in enumerate(rules):
        findings.extend(_scan_secrets(rule.reason, location=f"rules[{i}].reason"))
    return findings


def lint_text(text: str) -> list[Finding]:
    """Scan raw policy text for literal secrets/PII."""
    return _scan_secrets(text)


def _scan_secrets(text: str, *, location: str = "text") -> list[Finding]:
    if not text:
        return []
    findings: list[Finding] = []
    for label, patterns in (("secret", _SECRET_PATTERNS), ("pii", _PII_PATTERNS)):
        for pattern, name in patterns:
            if re.search(pattern, text):
                findings.append(
                    Finding(
                        LITERAL_SECRET, "error",
                        f"{label} literal ({name}) found in policy — pin it to a secret store",
                        location,
                    )
                )
    return findings


__all__ = [
    "LITERAL_SECRET",
    "OUTCOME_CONFLICT",
    "OVER_PERMISSIVE_ALLOW",
    "UNKNOWN_TOOL_RULE",
    "UNREACHABLE_RULE",
    "Finding",
    "lint_policy",
    "lint_text",
]
