# wikinggruppen-mcp

Simon's own generic tool (started 2026-11-22). He owns it, not a client. Public repo (since 2026-11-22): github.com/Sim1Sim1/wikinggruppen-mcp. See README.md for the tools.

- **Knowledge first, live access second.** The value is `data/gotchas.md`, `data/workflows.md` and `data/reference.json`. Claude should call `wgr_gotchas` and `wgr_workflow` before planning any task against a Wikinggruppen shop.
- **No client data and no credentials in the repo.** Keep the text generic: no shop names, no article numbers, no counts that identify a client. A lesson learned on one shop goes in as a general rule. `.env` is gitignored.
- **Writes stay off by default** (`WGR_ALLOW_WRITE=1`), only set/create, never delete, cancel or restore.
- **`reference.json` is generated** by `scripts/build_reference.py` from the public docs. Do not edit it by hand. Fix the parser instead.
- **Add to gotchas.md when a call behaves differently from the docs**, with how sure we are. Add to workflows.md when a task has been done once and worked.
- **The venv lives outside JeanClaude** at `~/.local/share/wikinggruppen-mcp/.venv` (keeps it out of the Drive backup). Python 3.11 or later (uses 3.12), mcp 2.x (`FastMCP` is `MCPServer`).
- Shop-specific work stays in its own client folder and points here for API knowledge.
