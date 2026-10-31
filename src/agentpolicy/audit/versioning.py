"""Policy versioning + the review flag (WBS M6 ``6.4``).

Every decision records the ``policy_version`` and ``policy_hash`` that governed
it, so *"which policy governed this?"* is answerable from the audit trail alone.
A policy change is **reviewed** when its content hash is pinned in a reviewed
set; an unreviewed change is **flagged** (``unreviewed_policy_change``) rather
than silently accepted.

The hash is the M5 :func:`agentpolicy.cedar.policy.policy_hash` — one hash
function, no drift between the explain artifact and the audit record.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agentpolicy.cedar import policy as policy_mod

#: The flag raised when a decision was governed by an unreviewed policy change.
UNREVIEWED_CHANGE = "unreviewed_policy_change"


@dataclass(frozen=True)
class PolicyRevision:
    """The pinned provenance record for a policy.

    Attributes:
        version: The human-facing policy version.
        policy_hash: The content hash (``sha256:<hex>``).
        reviewed: Whether this revision was reviewed.
        reviewed_by: The reviewer identity, when reviewed.
        reviewed_at: ISO-8601 review timestamp, when reviewed.
    """

    version: str
    policy_hash: str
    reviewed: bool = False
    reviewed_by: str | None = None
    reviewed_at: str | None = None

    def __post_init__(self) -> None:
        if not self.version or not self.version.strip():
            raise ValueError("version must be a non-blank string")
        if not self.policy_hash or not self.policy_hash.strip():
            raise ValueError("policy_hash must be a non-blank string")

    def to_dict(self) -> dict[str, Any]:
        """JSON-friendly representation."""
        return {
            "version": self.version,
            "policy_hash": self.policy_hash,
            "reviewed": self.reviewed,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at,
        }


def policy_revision(
    policies: str,
    *,
    version: str,
    reviewed: bool = False,
    reviewed_by: str | None = None,
    reviewed_at: str | None = None,
) -> PolicyRevision:
    """Build the pinned revision for a policy set.

    Args:
        policies: The Cedar policy text.
        version: The human-facing policy version.
        reviewed: Whether the change has been reviewed.
        reviewed_by: The reviewer identity.
        reviewed_at: ISO-8601 review timestamp.

    Returns:
        A :class:`PolicyRevision` carrying the M5 ``policy_hash``.
    """
    return PolicyRevision(
        version=version,
        policy_hash=policy_mod.policy_hash(policies),
        reviewed=reviewed,
        reviewed_by=reviewed_by,
        reviewed_at=reviewed_at,
    )


def is_reviewed(revision: PolicyRevision, reviewed_hashes: set[str]) -> bool:
    """Whether *revision* is reviewed (explicitly, or its hash is pinned)."""
    return revision.reviewed or revision.policy_hash in reviewed_hashes


def review_warning(revision: PolicyRevision, reviewed_hashes: set[str]) -> str | None:
    """Return the unreviewed-change flag, or ``None`` when the revision is reviewed."""
    if is_reviewed(revision, reviewed_hashes):
        return None
    return UNREVIEWED_CHANGE


__all__ = [
    "UNREVIEWED_CHANGE",
    "PolicyRevision",
    "is_reviewed",
    "policy_revision",
    "review_warning",
]
