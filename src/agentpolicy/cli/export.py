"""``agentpolicy export`` — one policy → harness formats (WBS M9 ``9.5``)."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from agentpolicy.cli.errors import CliError
from agentpolicy.errors import PolicyParseError
from agentpolicy.export import TARGETS, render_export
from agentpolicy.policy.loader import load_policy
from agentpolicy.policy.models import default_policy


def add_parser(subparsers: Any) -> None:
    """Register the ``agentpolicy export`` subcommand parser."""
    parser = subparsers.add_parser(
        "export",
        help="export a policy as Cedar source or a policyweave artifact",
        description="Compile one policy outward for a harness/policyweave target.",
    )
    parser.add_argument("--policy", default=None, help="policy file (default: balanced preset)")
    parser.add_argument(
        "--format", choices=list(TARGETS), default="policyweave",
        help="export target (default: policyweave)",
    )
    parser.add_argument("-o", "--output", default=None, help="write to a file (default: stdout)")
    parser.set_defaults(func=_run)


def _run(args: argparse.Namespace) -> int:
    try:
        policy = load_policy(args.policy) if args.policy else default_policy("balanced")
    except PolicyParseError as exc:
        raise CliError(f"cannot load policy: {exc}") from exc
    text = render_export(policy, target=args.format)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"wrote {args.output}")
    else:
        print(text, end="" if text.endswith("\n") else "\n")
    return 0
