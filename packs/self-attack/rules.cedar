// self-attack rule class (M22 22.1) — an attack on agentpolicy's own decision
// surface is blocked. The attack class travels in context.self_attack; every
// marked call is forbidden (a benign call carries an empty marker).
@id("self-attack-block")
forbid (principal, action, resource)
when { context.self_attack != "" };
