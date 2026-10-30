"""The mandatory human-gate class (M2 ``2.3``).

Irreversible actions **default to ``ask``** rather than a hard deny. The gate
class is a shipped policy module; widening or narrowing it is a
**logged amendment** (never a silent config change), so the safety-relevant
default is auditable.

The gate verbs are exactly the irreversible/effectful verbs; destructive verbs
(``delete``/``drop``/``destroy``) are *not* in the gate class — they are hard
denied by the Cedar policy.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agentpolicy.types import NormalizedCall

logger = logging.getLogger("agentpolicy.cedar.gates")

#: Irreversible verbs that require a human gate in production.
HUMAN_GATE_VERBS: frozenset[str] = frozenset(
    {"write", "deploy", "send", "transfer", "grant", "approve"}
)

#: Environments where the gate class applies.
HUMAN_GATE_ENVIRONMENTS: frozenset[str] = frozenset({"production"})


def is_human_gate(call: NormalizedCall) -> bool:
    """Whether *call* falls in the mandatory human-gate class."""
    return call.environment in HUMAN_GATE_ENVIRONMENTS and call.action in HUMAN_GATE_VERBS


def amendment_record(
    *, action: str, added: frozenset[str] = frozenset(), removed: frozenset[str] = frozenset()
) -> dict[str, object]:
    """Build a reasoned record for a change to the gate class.

    Shape: ``{kind, action, added, removed, at, verb_set}``. Callers persist
    this to the audit log so a gate-class change is *logged*, never silent.
    """
    return {
        "kind": "gate_class_amendment",
        "action": action,
        "added": sorted(added),
        "removed": sorted(removed),
        "at": datetime.now(UTC).isoformat(),
        "verb_set": sorted(HUMAN_GATE_VERBS),
    }


def log_amendment(record: dict[str, object]) -> None:
    """Emit a gate-class amendment to the structured log (and thus the audit trail)."""
    logger.warning("gate-class amended: %s", json.dumps(record, sort_keys=True))
