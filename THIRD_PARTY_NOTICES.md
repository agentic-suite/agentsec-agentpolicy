# Third-Party Notices

agentpolicy is distributed under the **Apache License 2.0** (see [`LICENSE`](LICENSE)).

It incorporates source code from the following third-party project.

---

## agent-tooltrust (the predecessor policy engine)

- **Project:** agent-tooltrust — *a pre-execution, deterministic policy decision point for tool-using AI
  agents: contextual risk and permission engine — allow, audit, escalate, deny.*
- **Source:** `https://github.com/agentic-suite/agent-tooltrust` (archived; retained **private, never deleted**)
- **Version:** v0.2.0
- **Commit (SHA):** `31655747ee4290b80adb04b2a300dd991b80e018`
- **Copyright:** © 2026 Debashish Ghosal
- **License:** MIT

agentpolicy's M0 (WBS `0.1`) is a bulk port of the agent-tooltrust codebase — the `src/agentpolicy`
package, the test suite, rule packs, tooling, packaging, and a docs subset — renamed from the predecessor's
namespace and CLI. Behavior is preserved; later milestones re-point the decision engine to Cedar.

### MIT License (as shipped by agent-tooltrust)

```
MIT License

Copyright (c) 2026 Debashish Ghosal

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

See the source tree for the authoritative copy of the MIT license as shipped upstream.
See [`docs/architecture/porting-plan-v0.1.0.md`](docs/architecture/porting-plan-v0.1.0.md) for the full
porting plan and inventory.
