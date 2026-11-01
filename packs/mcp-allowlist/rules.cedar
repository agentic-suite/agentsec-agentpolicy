// rule pack: mcp-allowlist
// incident_ref: incident-register#11
// A call whose MCP server is not allowlisted is default-denied.

@id("mcp-allowlist-deny-unlisted")
forbid (principal, action, resource)
when {
  context.tool_category == "mcp" &&
  context.mcp_listed == false
};
