"""MCP server package for agentsec-agentpolicy.

Exposes the core server components for programmatic use and provides the
``agentpolicy serve`` CLI command.
"""

from agentpolicy.server.analytics_routes import register_analytics_routes
from agentpolicy.server.audit_routes import register_audit_routes
from agentpolicy.server.baselines_routes import register_baselines_routes
from agentpolicy.server.cli import add_parser as _serve_add_parser
from agentpolicy.server.dashboard import register_dashboard_route
from agentpolicy.server.escalation_routes import register_escalation_routes
from agentpolicy.server.mcp_tools import register_tools
from agentpolicy.server.pdp_routes import register_pdp_routes
from agentpolicy.server.seed import register_seed_route
from agentpolicy.server.server_core import ServerCore
from agentpolicy.server.session_store import SessionState, SessionStore
from agentpolicy.server.sessions_routes import register_sessions_routes

__all__ = [
    "ServerCore",
    "SessionState",
    "SessionStore",
    "_serve_add_parser",
    "register_analytics_routes",
    "register_audit_routes",
    "register_baselines_routes",
    "register_dashboard_route",
    "register_escalation_routes",
    "register_pdp_routes",
    "register_seed_route",
    "register_sessions_routes",
    "register_tools",
]
