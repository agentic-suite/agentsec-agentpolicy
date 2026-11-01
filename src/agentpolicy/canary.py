"""Canary rollout (WBS M10 ``10.4``, CUJ-4 / R30).

Flip enforcement gradually: shadow mode → canary (enforce for a configurable
**session percentage**) → full enforce. Selection is **deterministic** — the
same session id lands in the same bucket on every run and every machine (a
stable hash of the session id), so a canary is reproducible and a session never
flickers between enforced and shadowed.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

#: The conventional rollout stages (5% → 50% → 100%).
STAGES: tuple[int, ...] = (5, 50, 100)


def _bucket(session_id: str) -> int:
    """A stable bucket in ``[0, 100)`` for a session id."""
    digest = hashlib.sha256(session_id.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % 100


def canary_selected(session_id: str, percent: int) -> bool:
    """Whether *session_id* is inside the enforced canary cohort.

    Args:
        session_id: The session (or agent) identity.
        percent: The rollout percentage (0 = off, 100 = everyone).

    Returns:
        True when the session is in the canary cohort.

    Raises:
        ValueError: *percent* is outside ``[0, 100]``.
    """
    if not 0 <= percent <= 100:
        raise ValueError(f"canary percent must be in [0, 100], got {percent}")
    if percent <= 0:
        return False
    if percent >= 100:
        return True
    return _bucket(session_id) < percent


@dataclass(frozen=True)
class CanaryConfig:
    """The canary rollout knob.

    Attributes:
        percent: The enforced cohort size (0..100).
    """

    percent: int = 0

    def __post_init__(self) -> None:
        if not 0 <= self.percent <= 100:
            raise ValueError(f"canary percent must be in [0, 100], got {self.percent}")

    def enforces(self, session_id: str | None) -> bool:
        """Whether this session's decision should be enforced (not shadowed).

        A missing session id is treated as *not* selected, so an unidentified
        caller stays in shadow (the safe default) until the rollout completes.
        """
        if session_id is None:
            return self.percent >= 100
        return canary_selected(session_id, self.percent)

    def to_dict(self) -> dict[str, object]:
        """JSON-friendly representation."""
        return {"percent": self.percent, "stages": list(STAGES)}


__all__ = ["STAGES", "CanaryConfig", "canary_selected"]
