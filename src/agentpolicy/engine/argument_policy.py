"""Stage 1b of the pipeline — argument-level policy (M1 #142, DD-15).

Tool-selection policy decides *whether* a tool may be called; argument-level
policy constrains *how* it may be called. A per-tool ``args_policy`` declares
required arguments, forbidden substrings, numeric bounds, and allowed values.
Evaluation is pure and deterministic (regex/allowlist/range — never an LLM
judgment), so identical inputs produce identical decisions every run.

Semantics (documented, per DD-15):
- ``required``: the argument must be present in the call.
- ``forbid``: any pattern that appears as a *substring* of the argument's
  string form is a violation; the empty string additionally matches only the
  empty value, so specifying ``forbid: [""]`` rejects blank while allowing
  real content.
- ``min`` / ``max``: inclusive numeric bounds on the argument.
- ``allowed``: the value must be one of the listed strings.
- A missing non-required argument and any argument with no corresponding spec
  pass through — the schema constrains, it does not allowlist.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse


@dataclass(frozen=True)
class ArgumentSpec:
    """Declarative constraints on one tool-call argument.

    Attributes:
        required: The argument must be present (non-``None``).
        forbid: Substrings that must not appear in the argument.
        min: Inclusive lower numeric bound.
        max: Inclusive upper numeric bound.
        allowed: The exact values the argument may take (when non-empty).
        regex: A regular expression the argument's string form must match
            (``search`` semantics — anchor with ``^``/``$`` as needed).
        enum: The closed set of allowed values (semantic synonym of ``allowed``,
            named for readability).
        path_root: A filesystem root the argument (a path) must stay contained in
            (realpath containment — defeats ``../`` traversal).
        url_allowlist: The hosts a URL argument may resolve to (SSRF allowlist).
    """

    required: bool = False
    forbid: tuple[str, ...] = ()
    min: float | None = None
    max: float | None = None
    allowed: tuple[str, ...] = ()
    regex: str | None = None
    enum: tuple[str, ...] = ()
    path_root: str | None = None
    url_allowlist: tuple[str, ...] = ()


def _forbidden(value: Any, forbid: tuple[str, ...]) -> bool:
    text = str(value)
    for pattern in forbid:
        if pattern == "":
            if text == "":
                return True
        elif pattern in text:
            return True
    return False


def _out_of_range(value: Any, spec: ArgumentSpec) -> bool:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    if spec.min is not None and number < spec.min:
        return True
    if spec.max is not None and number > spec.max:
        return True
    return False


def _not_allowed(value: Any, spec: ArgumentSpec) -> bool:
    if not spec.allowed:
        return False
    return str(value) not in spec.allowed


def _regex_violation(value: Any, spec: ArgumentSpec) -> bool:
    if spec.regex is None:
        return False
    return re.search(spec.regex, str(value)) is None


def _enum_violation(value: Any, spec: ArgumentSpec) -> bool:
    if not spec.enum:
        return False
    return str(value) not in spec.enum


def _path_violation(value: Any, spec: ArgumentSpec) -> bool:
    """True when a path argument escapes ``path_root`` (realpath containment)."""
    if spec.path_root is None:
        return False
    root = os.path.realpath(os.path.expanduser(spec.path_root))
    candidate = os.path.realpath(os.path.join(root, str(value)))
    return os.path.commonpath([root, candidate]) != root


def _url_violation(value: Any, spec: ArgumentSpec) -> bool:
    """True when a URL argument's host is not on the allowlist (SSRF guard)."""
    if not spec.url_allowlist:
        return False
    host = urlparse(str(value)).hostname or ""
    return host not in spec.url_allowlist


def check_arguments(
    tool: str,
    arguments: dict[str, Any] | None,
    args_policy: dict[str, dict[str, ArgumentSpec]],
) -> str | None:
    """Validate a tool call's arguments against the per-tool policy.

    Args:
        tool: The canonical tool name.
        arguments: The call's argument mapping (may be ``None``).
        args_policy: Tool → {argument → spec}.

    Returns:
        The name of the first violating argument, or ``None`` if the call
        passes argument-level policy.
    """
    specs = args_policy.get(tool)
    if not specs:
        return None
    arguments = arguments or {}
    for name, spec in specs.items():
        if name not in arguments or arguments[name] is None:
            if spec.required:
                return name
            continue
        value = arguments[name]
        if _forbidden(value, spec.forbid):
            return name
        if _out_of_range(value, spec):
            return name
        if _not_allowed(value, spec):
            return name
        if _regex_violation(value, spec):
            return name
        if _enum_violation(value, spec):
            return name
        if _path_violation(value, spec):
            return name
        if _url_violation(value, spec):
            return name
    return None
