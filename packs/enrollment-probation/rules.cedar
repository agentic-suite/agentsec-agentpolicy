// enrollment-probation rule class (M16 16.2) — a probationary agent's write
// is gated until a human classifies the agent.
@id("enrollment-probation-gate")
forbid (principal, action, resource)
when {
  context.agent_class == "probation" &&
  (context.verb == "write" || context.verb == "deploy" || context.verb == "send"
   || context.verb == "grant" || context.verb == "transfer") &&
  context.environment == "production"
};
