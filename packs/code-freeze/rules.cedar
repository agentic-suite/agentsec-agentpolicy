// code-freeze rule class (M15 15.2) — a write during a declared freeze is blocked.
@id("code-freeze-block")
forbid (principal, action, resource)
when {
  context.freeze_id != "" &&
  (context.verb == "write" || context.verb == "deploy" || context.verb == "send") &&
  context.environment == "production"
};
