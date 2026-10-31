"""``agentpolicy explain`` — explain a tool call's decision, offline.

Evaluates the call through the canonicalizer + Cedar decision core (no server,
no network) and prints the full explain artifact: the outcome, the machine
reason code, the matched rule/clause, the factor breakdown, and the one change
that would flip the outcome (WBS M5 ``5.4``). ``--json`` prints the agentwatch-
ready artifact verbatim.
"""

from __future__ import annotations

import argparse
import json
from typing import Any

from agentpolicy.canonical import canonicalize
from agentpolicy.cedar import CedarEvaluator
from agentpolicy.cli.errors import CliError
from agentpolicy.explain import build_artifact


def add_parser(subparsers: Any) -> None:
    """Register the ``agentpolicy explain`` subcommand parser.

    Args:
        subparsers: The ``add_subparsers()`` action from the parent parser.
    """
    parser = subparsers.add_parser(
        "explain",
        help="explain why a tool call received its decision",
        description="Evaluate a tool call offline and print the full explain artifact.",
    )
    parser.add_argument("--tool", required=True, help="Tool name (e.g., deploy_service)")
    parser.add_argument("--action", required=True, help="Action verb (e.g., read, write)")
    parser.add_argument("--env", required=True, help="Environment (e.g., staging, production)")
    parser.add_argument("--data", required=True, help="Data class (e.g., internal, restricted)")
    parser.add_argument("--agent", required=True, help="Agent identity (e.g., release-bot)")
    parser.add_argument("--json", action="store_true", help="Emit the explain artifact as JSON")
    parser.set_defaults(func=_explain)


def _explain(args: argparse.Namespace) -> int:
    """Evaluate and explain a tool call's decision.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code 0 on success, 1 on error.
    """
    try:
        call = canonicalize(
            tool=args.tool,
            action=args.action,
            environment=args.env,
            data_class=args.data,
            agent_id=args.agent,
        )
        evaluator = CedarEvaluator()
        decision = evaluator.evaluate(call)
        artifact = build_artifact(decision, call, evaluator=evaluator)
    except Exception as exc:
        raise CliError(str(exc)) from exc

    if args.json:
        print(json.dumps(artifact.to_dict(), indent=2))
        return 0

    print()
    print(f"  Decision      {artifact.decision.upper()}")
    print(f"  Reason        {artifact.reason_code}")
    print(f"  Criticality   {artifact.criticality}")
    print(f"  Clause        {artifact.clause}")
    print()
    print(f"  {artifact.explanation}")
    print()
    if artifact.factors:
        print("  Factor breakdown:")
        for f in artifact.factors:
            bar = "█" * int(min(f.contribution * 20, 20))
            print(f"    {f.dimension:16s} {bar} ({f.contribution:.2f})  {f.value}")
    if artifact.suggested_change:
        print()
        print(f"  To change this: {artifact.suggested_change}")
    print()

    return 0
