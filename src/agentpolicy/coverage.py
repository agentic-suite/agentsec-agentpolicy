"""Action-space coverage report (WBS M21 ``21.3``, CUJ-31 / R45).

Cross the canonical **taxonomy verbs** with (a) the policy **rules** and (b) the
**fleet inventory** (the verbs the fleet actually exercised), yielding four
quadrants:

* covered + exercised (good),
* covered + never exercised (**dead** rule — lint's cousin),
* **uncovered + exercised (the dangerous quadrant, named loudly)**,
* uncovered + never exercised (declare out-of-scope or accept).

The honesty contract is ``gap_unexplained == 0``: every dangerous verb is either
covered or explicitly declared ``out_of_scope``.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from agentpolicy.policy.models import Policy
from agentpolicy.taxonomy import DOMAIN_VERBS

COVERED_EXERCISED = "covered_exercised"
COVERED_NEVER = "covered_never"
UNCOVERED_EXERCISED = "uncovered_exercised"
UNCOVERED_NEVER = "uncovered_never"


def canonical_verbs() -> tuple[str, ...]:
    """The canonical verb space: the union of every domain's verbs, sorted."""
    verbs = {verb for verbs in DOMAIN_VERBS.values() for verb in verbs}
    return tuple(sorted(verbs))


def covered_verbs(policy: Policy) -> frozenset[str]:
    """The verbs the policy references (a wildcard ``action: "*"`` covers all)."""
    if any(rule.action == "*" for rule in policy.rules):
        return frozenset(canonical_verbs())
    return frozenset(
        rule.action for rule in policy.rules if rule.action in set(canonical_verbs())
    )


def inventory_from_events(events: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    """Count exercised verbs from a window of agentwatch decision events."""
    counts: Counter[str] = Counter()
    for event in events:
        action = event.get("action")
        verb = action.get("verb") if isinstance(action, Mapping) else None
        if isinstance(verb, str) and verb:
            counts[verb] += 1
    return dict(counts)


def _as_counts(inventory: Mapping[str, int] | Iterable[str] | None) -> dict[str, int]:
    if inventory is None:
        return {}
    if isinstance(inventory, Mapping):
        return {str(k): int(v) for k, v in inventory.items()}
    return dict(Counter(str(v) for v in inventory))


@dataclass(frozen=True)
class CoverageRow:
    """One verb's coverage quadrant."""

    verb: str
    covered: bool
    exercised: int
    quadrant: str

    def to_dict(self) -> dict[str, Any]:
        """JSON-friendly representation."""
        return {
            "verb": self.verb, "covered": self.covered,
            "exercised": self.exercised, "quadrant": self.quadrant,
        }


@dataclass(frozen=True)
class CoverageReport:
    """The action-space coverage report (four quadrants)."""

    rows: tuple[CoverageRow, ...]
    dangerous: tuple[str, ...]
    dead: tuple[str, ...]
    exercised: tuple[str, ...]
    covered: tuple[str, ...]
    gap_unexplained: int

    def to_dict(self) -> dict[str, Any]:
        """JSON-friendly representation."""
        return {
            "rows": [row.to_dict() for row in self.rows],
            "dangerous": list(self.dangerous),
            "dead": list(self.dead),
            "exercised": list(self.exercised),
            "covered": list(self.covered),
            "gap_unexplained": self.gap_unexplained,
        }


def coverage_report(
    policy: Policy,
    *,
    inventory: Mapping[str, int] | Iterable[str] | None = None,
    out_of_scope: Iterable[str] = (),
) -> CoverageReport:
    """Build the coverage report for *policy* versus the fleet *inventory*."""
    counts = _as_counts(inventory)
    covered = covered_verbs(policy)
    scope = {verb for verb in out_of_scope}
    verbs = sorted(set(canonical_verbs()) | set(counts))
    rows: list[CoverageRow] = []
    dangerous: list[str] = []
    dead: list[str] = []
    for verb in verbs:
        is_covered = verb in covered
        exercised = counts.get(verb, 0)
        if is_covered and exercised > 0:
            quadrant = COVERED_EXERCISED
        elif is_covered:
            quadrant = COVERED_NEVER
        elif exercised > 0:
            quadrant = UNCOVERED_EXERCISED
        else:
            quadrant = UNCOVERED_NEVER
        rows.append(CoverageRow(verb, is_covered, exercised, quadrant))
        if quadrant == COVERED_NEVER:
            dead.append(verb)
        if quadrant == UNCOVERED_EXERCISED and verb not in scope:
            dangerous.append(verb)
    return CoverageReport(
        rows=tuple(rows),
        dangerous=tuple(dangerous),
        dead=tuple(dead),
        exercised=tuple(sorted(counts)),
        covered=tuple(sorted(covered)),
        gap_unexplained=len(dangerous),
    )


__all__ = [
    "COVERED_EXERCISED",
    "COVERED_NEVER",
    "UNCOVERED_EXERCISED",
    "UNCOVERED_NEVER",
    "CoverageReport",
    "CoverageRow",
    "canonical_verbs",
    "coverage_report",
    "covered_verbs",
    "inventory_from_events",
]
