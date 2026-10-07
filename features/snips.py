"""Snippets library — save, search, tag"""
import json
from datetime import datetime
from pathlib import Path

BASE = Path.home() / "evoscanner"
USER_SNIPS = BASE / "user_snippets.json"


def load():
    if USER_SNIPS.exists():
        try:
            return json.loads(USER_SNIPS.read_text())
        except Exception:
            pass
    return []


def save(items):
    USER_SNIPS.write_text(
        json.dumps(items, indent=2, ensure_ascii=False))


def add(title, code, tags=None, source=""):
    items = load()
    items.append({
        "title": title,
        "code": code,
        "tags": tags or [],
        "source": source,
        "ts": datetime.now().isoformat(),
    })
    save(items)
    return len(items)


def search(term):
    items = load()
    t = term.lower()
    return [x for x in items
            if t in x["title"].lower()
            or t in x["code"].lower()
            or any(t in tag.lower() for tag in x.get("tags", []))]


def list_all(limit=30):
    return load()[-limit:]


def show_one(item, idx=None):
    print(f"\n{'─' * 55}")
    if idx is not None:
        print(f"  [{idx}] {item['title']}")
    else:
        print(f"  {item['title']}")
    if item.get("tags"):
        print(f"  Tags: {', '.join(item['tags'])}")
    if item.get("source"):
        print(f"  Source: {item['source']}")
    print(f"  {item['ts'][:16]}")
    print()
    for line in item["code"].split("\n")[:30]:
        print(f"    {line}")
    if item["code"].count("\n") > 30:
        print(f"    ... (+{item['code'].count(chr(10)) - 30} خط)")
    print()


def delete(idx):
    items = load()
    if 0 <= idx < len(items):
        items.pop(idx)
        save(items)
        return True
    return False
