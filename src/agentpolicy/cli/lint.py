"""``agentpolicy lint`` — rule/policy lint (WBS M9 ``9.4``).

Prints findings (unused/shadowed/over-permissive/cross-pack-conflict/literal-
secret) with locations and exits 1 when any finding exists, so it is CI-failable.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from agentpolicy.cli.errors import CliError
from agentpolicy.errors import PolicyParseError
from agentpolicy.lint import lint_policy
from agentpolicy.policy.loader import load_policy_text


def add_parser(subparsers: Any) -> None:
    """Register the ``agentpolicy lint`` subcommand parser."""
    parser = subparsers.add_parser(
        "lint",
        help="lint a policy for unused/shadowed/over-permissive/secret findings",
        description="Report policy lint findings with locations (CI-failable).",
    )
    parser.add_argument(
        "policy", nargs="?", default="agentpolicy.yaml",
        help="policy file to lint (default: ./agentpolicy.yaml)",
    )
    parser.add_argument("--json", action="store_true", help="emit findings as JSON")
    parser.set_defaults(func=_run)


def _run(args: argparse.Namespace) -> int:
    path = Path(args.policy)
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CliError(f"cannot read policy: {exc}") from exc
    try:
        policy = load_policy_text(raw)
    except PolicyParseError as exc:
        raise CliError(f"cannot load policy: {exc}") from exc

    findings = lint_policy(policy, text=raw)
    if args.json:
        print(json.dumps([f.to_dict() for f in findings], indent=2))
    elif not findings:
        print("no lint findings")
    else:
        for finding in findings:
            print(f"  {finding.severity}: {finding.code} at {finding.location}: {finding.message}")
    return 1 if findings else 0
