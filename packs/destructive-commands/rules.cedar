// rule pack: destructive-commands  (the "Replit rule")
// incident_ref: incident-register#6
// Blocks destructive / irreversible verbs in production outright.

@id("destructive-command-gate")
forbid (principal, action, resource)
when {
  context.environment == "production" &&
  (context.verb == "delete" || context.verb == "drop" || context.verb == "destroy"
   || context.verb == "force_push" || context.verb == "revoke")
};
