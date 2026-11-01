"""Redact-and-allow and secrets-in-arguments (WBS M7 ``7.3``/``7.4``).

Real redaction with **receipts**. Two entry points:

* :func:`redact_text` / :func:`redact_output` — scan a *value* (tool output, or a
  string argument) for known secret/PII patterns and replace each match,
  returning the scrubbed text plus one :class:`RedactionReceipt` per class with
  the count and the location. The raw value is never returned.
* :func:`redact_argument_values` — scan **argument values** (free text) so a
  secret pasted into ``args["command"]`` is caught *before the call leaves*; it
  composes with the M5 key-based audit redactor (named fields).

The patterns are the single source shipped by
:mod:`agentpolicy.engine.output_inspector` — one pattern set, no drift.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from agentpolicy.audit.redact import redact_arguments
from agentpolicy.engine.output_inspector import _PII_PATTERNS, _SECRET_PATTERNS

#: The value pattern sets, keyed by redaction class.
CLASS_PATTERNS: dict[str, list[tuple[str, str]]] = {
    "secret": _SECRET_PATTERNS,
    "pii": _PII_PATTERNS,
}

#: Classes scrubbed by default.
DEFAULT_CLASSES: tuple[str, ...] = ("secret", "pii")


@dataclass(frozen=True)
class RedactionReceipt:
    """What a scrub removed: the class, how many, and where.

    Attributes:
        redaction_class: ``secret`` / ``pii`` (the "class" of the receipt).
        count: How many matches of this class were removed.
        locations: Where they were found (a field path or ``"output"``).
    """

    redaction_class: str
    count: int
    locations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        """JSON-friendly receipt shape (``class`` / ``count`` / ``locations``)."""
        return {
            "class": self.redaction_class,
            "count": self.count,
            "locations": list(self.locations),
        }


def redact_text(
    text: str,
    *,
    classes: tuple[str, ...] = DEFAULT_CLASSES,
    location: str = "output",
) -> tuple[str, list[RedactionReceipt]]:
    """Scrub secrets/PII from *text*, returning ``(scrubbed, receipts)``.

    Args:
        text: The value to scrub.
        classes: Which classes to scrub (default: secret + pii).
        location: The location label recorded on the receipts.

    Returns:
        The scrubbed text and one receipt per matched class (empty when clean).
    """
    if not text:
        return text, []
    scrubbed = text
    receipts: list[RedactionReceipt] = []
    for redaction_class in classes:
        total = 0
        for pattern, _label in CLASS_PATTERNS.get(redaction_class, []):
            scrubbed, count = re.subn(
                pattern, f"[REDACTED-{redaction_class.upper()}]", scrubbed
            )
            total += count
        if total:
            receipts.append(
                RedactionReceipt(redaction_class, total, (location,))
            )
    return scrubbed, receipts


def redact_output(text: str, *, location: str = "output") -> tuple[str, list[RedactionReceipt]]:
    """Redact-and-allow: scrub a tool result before it reaches the model."""
    return redact_text(text, location=location)


def redact_argument_values(
    arguments: dict[str, Any] | None,
    *,
    extra_keys: set[str] | None = None,
) -> tuple[dict[str, Any] | None, list[RedactionReceipt]]:
    """Scrub secrets/PII pasted into argument **values**, before the call leaves.

    Composes two protections: the M5 key-based redactor strips named sensitive
    fields (``token``, ``password``, …); this function additionally scans the
    remaining **string values** for secret/PII patterns and scrubs them, with
    receipts. The raw value is never returned.

    Args:
        arguments: The call's argument dict (or ``None``).
        extra_keys: Additional sensitive key names for the key-based pass.

    Returns:
        ``(scrubbed_arguments, receipts)``. Returns the original ``None`` for no
        arguments; receipts are empty when nothing matched.
    """
    if arguments is None:
        return None, []
    key_redacted, _ = redact_arguments(arguments, extra_keys)
    receipts: list[RedactionReceipt] = []

    def walk(value: Any, path: str) -> Any:
        if isinstance(value, dict):
            return {
                k: walk(v, f"{path}.{k}" if path else str(k)) for k, v in value.items()
            }
        if isinstance(value, list):
            return [walk(v, f"{path}[{i}]") for i, v in enumerate(value)]
        if isinstance(value, str):
            scrubbed, found = redact_text(value, location=path or "arguments")
            receipts.extend(found)
            return scrubbed
        return value

    scrubbed_args = walk(key_redacted, "")
    return scrubbed_args, receipts


__all__ = [
    "CLASS_PATTERNS",
    "DEFAULT_CLASSES",
    "RedactionReceipt",
    "redact_argument_values",
    "redact_output",
    "redact_text",
]
