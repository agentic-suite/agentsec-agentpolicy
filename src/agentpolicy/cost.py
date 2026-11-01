"""Cost controls (WBS M23 ``23.4``, R8).

A ``--max-cost`` budget governor: each unit of work is *charged*; work that
would exceed the ceiling raises :class:`CostExceeded`, so a run **aborts and
reports** rather than silently overspending.
"""

from __future__ import annotations

from typing import Any


class CostExceeded(Exception):
    """The cost ceiling was exceeded."""


class CostGovernor:
    """Charge work against a ceiling (``None`` == unlimited).

    Args:
        max_cost: The cost ceiling, or ``None`` for no ceiling.
    """

    def __init__(self, max_cost: float | None = None) -> None:
        self.max_cost = max_cost
        self.spent = 0.0

    def charge(self, cost: float) -> None:
        """Charge *cost*; raise :class:`CostExceeded` if it would exceed the ceiling."""
        if self.max_cost is not None and self.spent + cost > self.max_cost:
            raise CostExceeded(
                f"cost ceiling {self.max_cost} exceeded (spent {self.spent} + {cost})"
            )
        self.spent += cost

    def report(self) -> dict[str, Any]:
        """A JSON-friendly cost report."""
        remaining = None if self.max_cost is None else max(0.0, self.max_cost - self.spent)
        return {"max_cost": self.max_cost, "spent": self.spent, "remaining": remaining}


__all__ = ["CostExceeded", "CostGovernor"]
