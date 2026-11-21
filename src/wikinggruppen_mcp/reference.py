"""Search and describe the API reference (data/reference.json, built from Wikinggruppen's public docs)."""

import json
from functools import lru_cache
from importlib import resources


def _read(name: str) -> str:
    return resources.files("wikinggruppen_mcp").joinpath("data", name).read_text(encoding="utf-8")


@lru_cache
def reference() -> dict:
    return json.loads(_read("reference.json"))


def gotchas() -> str:
    return _read("gotchas.md")


def workflows() -> str:
    return _read("workflows.md")


def workflow_section(name: str | None) -> str:
    text = workflows()
    if not name:
        return text
    parts = text.split("\n## ")
    hits = [p for p in parts[1:] if name.lower() in p.split("\n", 1)[0].lower()]
    return "\n\n".join("## " + h for h in hits) if hits else f"No workflow matching '{name}'. Titles: " + "; ".join(p.split("\n", 1)[0] for p in parts[1:])


def list_methods(class_name: str | None = None) -> list[dict]:
    out = []
    for name, m in reference()["methods"].items():
        if class_name and m["class"].lower() != class_name.lower():
            continue
        out.append({"method": name, "kind": "read" if m["action"] == "get" else "write", "summary": (m["intro"] or m["response_intro"])[:160]})
    return out


# Methods whose docs say "use the same parameters as in the response from X" (or "as in Y"): fill them in.
# (target, source method, source key, field names to leave out)
INHERIT = {
    "Category.set": ("Category.get", "response_fields", {"path_{languageCode}"}),
    "Category.create": ("Category.get", "response_fields", {"path_{languageCode}"}),
    "Customer.set": ("Customer.get", "response_fields", set()),
    "Customer.create": ("Customer.get", "response_fields", set()),
    "NewsletterRecipient.set": ("NewsletterRecipient.get", "response_fields", set()),
    "NewsletterRecipient.create": ("NewsletterRecipient.get", "response_fields", set()),
    "OrderStatus.set": ("OrderStatus.get", "response_fields", set()),
    "PriceList.set": ("PriceList.get", "response_fields", set()),
    "PriceList.create": ("PriceList.get", "response_fields", {"id"}),
    "Stock.set": ("Stock.get", "response_fields", set()),
}


@lru_cache
def notes() -> dict:
    return json.loads(_read("notes.json"))


def connection_notes() -> list[str]:
    return notes()["_connection"]


def describe(method: str) -> dict:
    ref = reference()
    m = ref["methods"].get(method)
    if m is None:
        close = [k for k in ref["methods"] if method.lower() in k.lower()]
        raise KeyError(f"Unknown method '{method}'." + (f" Did you mean: {close}" if close else ""))
    out = {"method": method, "class": ref["classes"].get(m["class"], ""), **m}
    if method in INHERIT:
        src, key, skip = INHERIT[method]
        out["request_params"] = out["request_params"] + [p for p in ref["methods"][src][key] if p["name"] not in skip]
        out["request_params_note"] = f"Same parameters as the answer fields of {src}" + (f", without {sorted(skip)}" if skip else "") + "."
    elif method == "Article.create":
        out["request_params"] = out["request_params"] + ref["methods"]["Article.set"]["request_params"]
        out["request_params_note"] = "Same parameters as Article.set, plus the ones listed first."
    out["notes"] = notes().get(method, [])
    return out


def find_field(query: str, limit: int = 40) -> list[dict]:
    q = query.lower()
    hits = []
    for name, m in reference()["methods"].items():
        for where, key in (("request", "request_params"), ("response", "response_fields")):
            for p in m[key]:
                if q in p["name"].lower() or q in p["description"].lower():
                    hits.append({"method": name, "in": where, **p})
    return hits[:limit]
