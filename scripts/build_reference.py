"""Build src/wikinggruppen_mcp/data/reference.json from Wikinggruppen's public API docs.

    python3 scripts/build_reference.py                # fetches api.wikinggruppen.se/docs/<version>/
    python3 scripts/build_reference.py --html page.html

The docs are plain HTML: per method a "Request parameters" and a "Response properties/parameters" block
of name / type / description lines. Re-run when Wikinggruppen publishes a new version and look at the diff.
"""
import argparse
import html
import json
import pathlib
import re
import urllib.request

OUT = pathlib.Path(__file__).resolve().parent.parent / "src" / "wikinggruppen_mcp" / "data" / "reference.json"
TYPE = re.compile(r"^(string|integer|boolean|float|DateTime|date|object of \w+|array of [\w ]+)$", re.I)
HEAD = re.compile(r"^(\w+)\.(get|set|create|delete|cancel|restore)$")
CLASSES = ["Article", "Category", "Customer", "Front", "NewsletterRecipient", "Order", "OrderStatus", "PriceList", "ProductImage", "ShippingMethod", "Stock"]


def to_lines(raw: str) -> list[str]:
    raw = re.sub(r"<(script|style)[\s\S]*?</\1>", "", raw)
    raw = re.sub(r"</(p|div|tr|li|h\d|pre|table)>", "\n", raw)
    text = html.unescape(re.sub(r"<[^>]+>", "", raw))
    return [re.sub(r"\s+", " ", l).strip() for l in text.splitlines() if l.strip()]


def params(block: list[str]) -> list[dict]:
    """name / type / description triples. A line is a name when the next line is a type."""
    out: list[dict] = []
    i = 0
    while i < len(block) - 1:
        if TYPE.match(block[i + 1]) and not TYPE.match(block[i]) and block[i] not in ("Parameter", "Type", "Description"):
            p = {"name": block[i], "type": block[i + 1], "description": ""}
            i += 2
            desc = []
            while i < len(block) and not (i + 1 < len(block) and TYPE.match(block[i + 1]) and not TYPE.match(block[i])):
                if block[i].startswith("* =") or block[i].startswith("Response") or block[i].startswith("Request"):
                    break
                desc.append(block[i]); i += 1
            p["description"] = " ".join(desc)
            out.append(p)
        else:
            i += 1
    return out


def lead_text(block: list[str]) -> str:
    """The prose before the first parameter row: 'Used to ...', 'Use the same parameters as ...'."""
    out = []
    for i, l in enumerate(block):
        if i + 1 < len(block) and TYPE.match(block[i + 1]) and l not in ("Parameter", "Type", "Description"):
            break
        if l not in ("Parameter", "Type", "Description"):
            out.append(l)
    return " ".join(out)


def parse(lines: list[str]) -> dict:
    start = next(i for i, l in enumerate(lines) if l == "Method classes")
    idx = [(i, HEAD.match(l)) for i, l in enumerate(lines) if i > start and HEAD.match(l) and HEAD.match(l).group(1) in CLASSES]
    class_intro = {}
    for c in CLASSES:
        j = next((i for i, l in enumerate(lines) if i > start + 12 and l == c), None)
        if j is not None:
            k = next((i for i, _ in idx if i > j), len(lines))
            class_intro[c] = " ".join(lines[j + 1:k])
    methods = {}
    for n, (i, m) in enumerate(idx):
        end = idx[n + 1][0] if n + 1 < len(idx) else len(lines)
        body = lines[i + 1:end]
        # the next class heading (e.g. "Category") ends this slice
        for k in range(len(body) - 1, max(len(body) - 8, -1), -1):
            if body[k] in CLASSES:
                body = body[:k]
                break
        req_i = next((k for k, l in enumerate(body) if l.startswith("Request parameters")), None)
        res_i = next((k for k, l in enumerate(body) if l.startswith("Response p")), None)
        req = body[req_i + 1:res_i] if req_i is not None else []
        res = body[res_i + 1:] if res_i is not None else []
        methods[f"{m.group(1)}.{m.group(2)}"] = {
            "class": m.group(1), "action": m.group(2),
            "intro": lead_text(req),
            "request_params": params(req),
            "response_intro": lead_text(res),
            "response_fields": params(res),
        }
    return {"classes": class_intro, "methods": methods}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--html")
    ap.add_argument("--version", default="8.4.0")
    a = ap.parse_args()
    raw = open(a.html, errors="ignore").read() if a.html else urllib.request.urlopen(f"https://api.wikinggruppen.se/docs/{a.version}/").read().decode("utf-8", "ignore")
    lines = to_lines(raw)
    data = parse(lines)
    data["docs_version"] = a.version
    t = lines.index("Terms of usage")
    data["intro"] = " ".join(lines[lines.index("Wikinggruppen Webshop API Documentation", 5) + 1:t + 5])
    b = lines.index("Basics", t)
    data["basics"] = lines[b + 1:lines.index("Sample requests", b)]
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1))
    print(f"{len(data['methods'])} methods -> {OUT}")


if __name__ == "__main__":
    main()
