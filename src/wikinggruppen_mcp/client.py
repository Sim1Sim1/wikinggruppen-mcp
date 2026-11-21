"""Live calls to one shop's API. Reads are open, writes need WGR_ALLOW_WRITE=1 and are limited to set/create."""

import base64
import json
import urllib.request

from .config import require, writes_allowed

READ_SUFFIX = ".get"
# set/create only. No delete, no Order.cancel/restore: those are not undoable with a backup of the shop's data.
WRITE_METHODS = {
    "Article.set", "Article.create", "Category.set", "Category.create", "Stock.set",
    "PriceList.set", "PriceList.create", "Customer.set", "Customer.create", "Order.set",
    "OrderStatus.set", "OrderStatus.create", "NewsletterRecipient.set", "NewsletterRecipient.create",
    "ProductImage.create",
}
MAX_COMMANDS = 50


class WgrError(Exception):
    pass


def call(commands: list[dict]) -> list[dict]:
    """commands: [{"method": "Article.get", "params": {...}}]. Returns one {"ok", "result"|"error"} per command, in order.

    Ids start at 1: the API answers id 0 without an id.
    """
    if not commands:
        return []
    if len(commands) > MAX_COMMANDS:
        raise WgrError(f"At most {MAX_COMMANDS} commands per request")
    url, user, password = require("WGR_API_URL"), require("WGR_API_USER"), require("WGR_API_PASSWORD")
    forward = __import__("os").environ.get("WGR_FORWARD_URL")
    headers = {"Content-Type": "application/json",
               "Authorization": "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode()}
    if forward:
        headers["Api-Url"] = url
    body = json.dumps([{"jsonrpc": "2.0", "id": i + 1, "method": c["method"], "params": c.get("params", {})}
                       for i, c in enumerate(commands)]).encode()
    req = urllib.request.Request(forward or url, data=body, headers=headers, method="POST")
    try:
        raw = json.load(urllib.request.urlopen(req, timeout=90))
    except urllib.error.HTTPError as e:
        raise WgrError(f"The shop answered HTTP {e.code}: {e.read().decode('utf-8', 'ignore')[:200]}") from None
    by_id = {r.get("id"): r for r in (raw if isinstance(raw, list) else [raw])}
    out = []
    for i, c in enumerate(commands):
        r = by_id.get(i + 1)
        if r is None:
            out.append({"ok": False, "error": f"No answer to {c['method']}"})
        elif "error" in r:
            out.append({"ok": False, "error": r["error"].get("message", str(r["error"]))})
        else:
            out.append({"ok": True, "result": r.get("result")})
    return out


def check_read(method: str) -> None:
    if not method.endswith(READ_SUFFIX):
        raise WgrError(f"{method} is not a read method. Use wgr_write for set/create.")


def check_write(method: str) -> None:
    if not writes_allowed():
        raise WgrError("Writes are off. Set WGR_ALLOW_WRITE=1 in the server's environment to allow them.")
    if method not in WRITE_METHODS:
        raise WgrError(f"{method} is not allowed through this tool. Allowed: {sorted(WRITE_METHODS)}. Deletes and cancels are never allowed.")
