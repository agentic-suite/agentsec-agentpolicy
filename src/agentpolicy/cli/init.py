"""``agentpolicy init`` — scaffold a populated policy (WBS M9 ``9.2``).

Writes the commented posture preset (never a blank policy) and, when a scaffold
directory is requested, an adapter stub plus a QUICKSTART so the operator has a
runnable first step.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from agentpolicy.cli.errors import CliError
from agentpolicy.policy.postures import available_postures, init_policy


def add_parser(subparsers: Any) -> None:
    """Register the ``agentpolicy init`` subcommand parser.

    Args:
        subparsers: The ``add_subparsers()`` action from the parent parser.
    """
    parser = subparsers.add_parser(
        "init",
        help="write a posture preset as agentpolicy.yaml",
        description="Generate a commented agentpolicy.yaml (+ optional adapter/quickstart).",
    )
    parser.add_argument(
        "--posture",
        choices=available_postures(),
        default="balanced",
        help="posture preset to write (default: balanced)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="output path (default: ./agentpolicy.yaml)",
    )
    parser.add_argument(
        "--adapter",
        default=None,
        help="adapter name to reference in the scaffold (default: raw)",
    )
    parser.add_argument(
        "--scaffold-dir",
        default=None,
        help="also write an adapter stub + QUICKSTART.md into this directory",
    )
    parser.set_defaults(func=_run)


def _adapter_stub(adapter: str) -> str:
    """A minimal adapter guard the operator can extend."""
    return (
        f'"""Scaffolded agentpolicy guard (adapter: {adapter})."""\n'
        "\n"
        "from agentpolicy.adapters import registry\n"
        "from agentpolicy.api import default_engine\n"
        "\n"
        f"ADAPTER = registry.load({adapter!r}, default_engine())\n"
        "\n"
        "\n"
        "def guard(tool_name: str, action: str, environment: str, data_class: str,"
        " agent_id: str):\n"
        '    """Evaluate a tool call; a deny raises AgentPolicyDecisionError."""\n'
        "    return ADAPTER.guard(\n"
        "        tool_name=tool_name, action=action, environment=environment,\n"
        "        data_class=data_class, agent_id=agent_id,\n"
        "    )\n"
    )


def _quickstart(policy_path: Path, posture: str, adapter: str) -> str:
    """A short, copy-pasteable first-run guide."""
    return (
        "# Quickstart\n\n"
        f"Policy: `{policy_path}` (posture `{posture}`).\n\n"
        "1. Validate the policy:\n\n"
        f"   ```sh\n   agentpolicy check {policy_path}\n   ```\n\n"
        "2. Try a decision:\n\n"
        "   ```sh\n"
        "   agentpolicy evaluate --tool query_logs --action read \\\n"
        "       --env staging --data internal --agent debug-bot\n"
        "   ```\n\n"
        f"3. Wire your harness with the `{adapter}` adapter — see `adapter.py`.\n"
    )


def _run(args: argparse.Namespace) -> int:
    path = init_policy(args.posture, args.output)
    print(f"wrote {path}")
    if args.adapter and not args.scaffold_dir:
        raise CliError("--adapter requires --scaffold-dir")
    if args.scaffold_dir:
        adapter = args.adapter or "raw"
        directory = Path(args.scaffold_dir)
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "adapter.py").write_text(_adapter_stub(adapter), encoding="utf-8")
        (directory / "QUICKSTART.md").write_text(
            _quickstart(Path(path), args.posture, adapter), encoding="utf-8"
        )
        print(f"wrote {directory / 'adapter.py'}")
        print(f"wrote {directory / 'QUICKSTART.md'}")
    return 0
