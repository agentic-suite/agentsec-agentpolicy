"""CLI error types (user-facing, no traceback).

Reserved exit codes (WBS M1 1.2 / 1.3):

* ``0`` — success
* ``1`` — general CLI failure (:class:`CliError`)
* ``2`` — invalid configuration or policy; **fail closed** (:class:`ConfigError`)
"""

from __future__ import annotations


class CliError(Exception):
    """A user-facing CLI failure (shown as ``agentpolicy: error: ...``).

    Carries the process exit code the CLI should return (:data:`exit_code`).
    """

    exit_code: int = 1


class ConfigError(CliError):
    """Invalid configuration or policy — fail closed with exit code 2.

    Raised when a policy/config file is missing, unparseable, or violates the
    schema, so a broken configuration is never silently accepted.
    """

    exit_code: int = 2
