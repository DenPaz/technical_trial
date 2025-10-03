import json
from pathlib import Path

IN = Path("cookies_raw.json")
OUT = Path("cookies.json")

raw = json.loads(IN.read_text(encoding="utf-8"))

cookie_dict = {
    c["name"]: c["value"]
    for c in raw
    if isinstance(c, dict)
    and c.get("name") is not None
    and c.get("value") is not None
    and any(
        d in (c.get("domain") or "")
        for d in (".x.com", "x.com", ".twitter.com", "twitter.com")
    )
}

OUT.write_text(json.dumps(cookie_dict, indent=2), encoding="utf-8")
print(f"Wrote {OUT} with {len(cookie_dict)} cookies: {sorted(cookie_dict.keys())}")
