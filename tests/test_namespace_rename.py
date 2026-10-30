"""Guard: no predecessor-namespace references remain after the M0 rename (WBS 0.2).

WBS item ``0.2`` — *Rename namespace* — has the acceptance criterion
"zero predecessor-namespace references remain" across code, tests, and configs.
This test enforces that in the shipped tree so a stray reference cannot regress
back in after the bulk port.

The predecessor's name is intentionally still allowed in agentpolicy's own
planning docs (``docs/prd``, ``docs/wbs``, ``docs/adr``), which describe the
predecessor on purpose; only code/configs are scanned here.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Code, tests, and build/config surfaces that must be free of the predecessor name.
CODE_ROOTS = ("src", "tests", "packs", "scripts", "examples")
CONFIG_FILES = (
    "pyproject.toml",
    "Makefile",
    "Dockerfile",
    "docker-compose.yml",
    ".dockerignore",
    ".github/workflows/ci.yml",
)

FORBIDDEN = re.compile(r"tooltrust", re.IGNORECASE)


def _iter_candidate_files() -> Iterator[Path]:
    self_path = Path(__file__).resolve()
    for root in CODE_ROOTS:
        base = REPO_ROOT / root
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts:
                if path.resolve() == self_path:
                    continue
                yield path
    for name in CONFIG_FILES:
        path = REPO_ROOT / name
        if path.is_file():
            yield path


def test_no_predecessor_namespace_in_code_or_config() -> None:
    offenders: list[str] = []
    for path in _iter_candidate_files():
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            if FORBIDDEN.search(line):
                offenders.append(f"{path.relative_to(REPO_ROOT)}:{lineno}: {line.strip()}")

    assert not offenders, (
        "predecessor namespace references remain:\n" + "\n".join(offenders[:50])
    )
