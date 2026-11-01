// rule pack: secret-in-output
// incident_ref: incident-register#9
// Sensitive reads are permitted so the decision is an allow, but the shaper
// turns them into a `redact` outcome — secrets/PII are scrubbed from the result.

@id("secret-in-output-redact-permit")
permit (principal, action, resource)
when {
  context.verb == "read" &&
  (context.data_class == "restricted" || context.data_class == "customer_pii")
};
