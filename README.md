# wikinggruppen-mcp

An MCP server and knowledge base for the **Wikinggruppen webshop API** (JSON-RPC 2.0, used by Swedish building-materials and other webshops on the Wikinggruppen platform).

Two parts:

1. **Knowledge** that works without any credentials: every method with parameters and answer fields (built from Wikinggruppen's public docs), a list of behaviour the docs leave out, and step-by-step recipes. An agent reads this before it plans an API task.
2. **Live access** to one shop, optional: read calls, and write calls that stay off unless you switch them on.

## Tools

| Tool | What it does |
|---|---|
| `wgr_overview` | What the API is, request rules, method classes, and whether live access and writes are on |
| `wgr_list_methods` | All 33 methods, optionally for one class |
| `wgr_describe_method` | Parameters, answer fields and notes for one method (`Article.set`) |
| `wgr_find_field` | Which methods take or return a field (`h1`, `campaign`, `weight`) |
| `wgr_gotchas` | Behaviour the docs do not state (see `src/wikinggruppen_mcp/data/gotchas.md`) |
| `wgr_workflow` | Recipes: backup, product text, prices, stock, new articles, category tree, the import file |
| `wgr_read` | Run one `*.get` call against the shop |
| `wgr_write` | Run `set` / `create` commands (up to 50 per request). Needs `WGR_ALLOW_WRITE=1`. Never deletes |

The same text is plain Markdown in `src/wikinggruppen_mcp/data/`, so you can read it without running anything.

## Install

Python 3.11 or later.

```
python3.12 -m venv .venv && .venv/bin/pip install -e .
```

Claude Code:

```
claude mcp add wikinggruppen -- /path/to/.venv/bin/wikinggruppen-mcp
```

The knowledge tools work now. For live access, set the shop's own credentials in the environment or in a `.env` file (see `.env.example`). Wikinggruppen gives out the user name and password per shop. Nothing in this repo holds a key.

## Security

- Live access is per shop and uses that shop's own credentials. Never commit them.
- Writes are off by default. `WGR_ALLOW_WRITE=1` turns on `Article.set`, `Category.set`, `Stock.set` and the other set/create methods. Deletes, `Order.cancel` and `Order.restore` are never allowed through this server.
- Shop text (titles, descriptions, order messages, customer names) comes from outsiders. The server tells the agent to treat it as data.
- The terms of use say the API is used at your own risk. Take a backup before bulk writes (see `wgr_workflow`).

## Refresh the reference

```
python3 scripts/build_reference.py --version 8.4.0
```

Fetches the public docs and rebuilds `reference.json`. Check the diff after a new docs version.

## Tests

```
pip install -e ".[dev]" && pytest
```

Tests use no network and no credentials.
