"""``agentpolicy draft`` — draft a candidate Cedar rule from a sentence (WBS M19).

Advisory and **authoring-time only**: the CLI writes a candidate pack
(``rules.cedar`` + ``tests.yaml`` + ``metadata.yaml``) and stops. The decision
path is never changed by drafting, and a draft is never auto-pinned.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from agentpolicy.cli.errors import CliError
from agentpolicy.draft import DraftError, draft


def add_parser(subparsers: Any) -> None:
    """Register the ``agentpolicy draft`` subcommand parser."""
    parser = subparsers.add_parser(
        "draft", help="draft a candidate Cedar rule from a sentence (advisory)",
        description=(
            "Generate a candidate Cedar rule + tests for human review (never auto-applied)."
        ),
    )
    parser.add_argument("sentence", help="the policy intent, in one sentence")
    parser.add_argument("--out", default=None, help="write the candidate pack to this directory")
    parser.add_argument("--json", action="store_true")
    parser.set_defaults(func=_draft)


def _draft(args: argparse.Namespace) -> int:
    try:
        candidate = draft(args.sentence)
    except DraftError as exc:
        raise CliError(str(exc)) from exc
    if args.out:
        target = Path(args.out).expanduser()
        target.mkdir(parents=True, exist_ok=True)
        (target / "rules.cedar").write_text(candidate.cedar, encoding="utf-8")
        (target / "tests.yaml").write_text(candidate.tests_yaml(), encoding="utf-8")
        (target / "metadata.yaml").write_text(
            "name: candidate\n"
            "version: 0.1.0\n"
            f"description: {json.dumps('NL draft: ' + args.sentence)}\n"
            "reviewed: false\n",
            encoding="utf-8",
        )
    if args.json:
        print(json.dumps(candidate.to_dict(), indent=2, sort_keys=True))
        return 0
    print(candidate.cedar)
    if args.out:
        print(f"candidate written to {args.out} (awaiting human review)")
    return 0


__all__ = ["add_parser"]
