"""Guard the hand-maintained field-test report against automated overwrite.

The canonical field-test report (``docs/field-test/<version>/FIELD_TEST_REPORT.md``)
is **hand-maintained** — a journal updated by a human, deliberately never rebuilt
by a script (a lossy automated rewrite has destroyed its notes before). Any
automation that writes a field-test report must first ask this module.

Usage::

    from agentpolicy.field.report_guard import refuse_overwrite

    if refuse_overwrite(path):
        ... # do NOT write; tell the operator to edit by hand
"""

from __future__ import annotations

from pathlib import Path

#: The marker a hand-maintained report carries (first line / anywhere).
HAND_MAINTAINED_MARKER = "HAND-MAINTAINED"


def is_hand_maintained(path: str | Path) -> bool:
    """Whether *path* exists and carries the hand-maintained marker."""
    try:
        file = Path(path).expanduser()
        return file.is_file() and HAND_MAINTAINED_MARKER in file.read_text(encoding="utf-8")
    except OSError:
        return False


def refuse_overwrite(path: str | Path, *, force: bool = False) -> bool:
    """Whether a write to *path* must be REFUSED.

    True when *path* is a hand-maintained report and *force* is not set. A caller
    that gets True must not write the file (write a sibling draft or stop).
    """
    return is_hand_maintained(path) and not force


__all__ = ["HAND_MAINTAINED_MARKER", "is_hand_maintained", "refuse_overwrite"]
