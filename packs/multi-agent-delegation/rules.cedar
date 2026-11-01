// multi-agent-delegation rule class (M17 17.4) — a delegated child agent
// (non-empty delegation_chain) may not act in production.
@id("multi-agent-delegation-gate")
forbid (principal, action, resource)
when {
  context.delegation_chain != "" &&
  context.environment == "production"
};
