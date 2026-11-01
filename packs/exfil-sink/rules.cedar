// exfil-sink rule class (M13 13.1) — taint-lite, no ML.
// A sensitive value flowing to an external-sink tool is an exfiltration chain.
@id("exfil-sink-block")
forbid (principal, action, resource)
when {
  (context.verb == "send" || context.verb == "post" || context.verb == "write"
   || context.verb == "publish" || context.verb == "upload") &&
  (context.tool_category == "http" || context.tool_category == "email"
   || context.tool_category == "notify") &&
  (context.data_class == "restricted" || context.data_class == "customer_pii")
};
