"""Compare two packages side by side"""
import sqlite3
from pathlib import Path

BASE = Path.home() / "evoscanner"
DB = BASE / "knowledge.db"


def pkg_info(kb, pkg):
    """اطلاعات یک پکیج از منابع + گراف"""
    info = {
        "name": pkg,
        "resources": [],
        "score": 0.0,
        "stars": 0,
        "category": "?",
        "related": [],
        "peers": [],
        "snippets": 0,
    }
    pkg_l = pkg.lower()

    # منابعی که این پکیج در عنوان/محتوا دارند
    rows = kb.conn.execute(
        """SELECT title, url, source, score FROM resources
           WHERE LOWER(title) LIKE ? OR LOWER(content) LIKE ?
           ORDER BY score DESC LIMIT 10""",
        (f"%{pkg_l}%", f"%{pkg_l}%")).fetchall()
    info["resources"] = rows
    if rows:
        info["score"] = sum(r[3] for r in rows) / len(rows)
        # بزرگ‌ترین مخزن = stars تقریبی
        for title, url, source, score in rows:
            if source == "github" and "/" in title:
                info["stars"] = max(info["stars"], int(score * 10000))
                break

    # دسته
    try:
        g = __import__("json").loads((BASE / "graph.json").read_text())
        node = g["nodes"].get(pkg_l, {})
        cats = node.get("cats", {})
        if cats:
            info["category"] = max(cats, key=cats.get)
        # مرتبط‌ها
        cooc = g.get("cooc", {})
        JUNK = {"build", "pip", "click", "user", "core", "setup",
                "install", "make", "docs", "test", "tests", "code"}
        rels = []
        for pair, w in cooc.items():
            a, b = pair.split("|", 1)
            if a.startswith("cat:") or b.startswith("cat:"):
                continue
            if a in JUNK or b in JUNK:
                continue
            if a == pkg_l: rels.append((b, w))
            elif b == pkg_l: rels.append((a, w))
        rels.sort(key=lambda x: -x[1])
        info["related"] = rels[:8]
    except Exception:
        pass

    # snippets
    try:
        n = kb.conn.execute(
            "SELECT COUNT(*) FROM snippets WHERE LOWER(purpose) LIKE ?",
            (f"%{pkg_l}%",)).fetchone()[0]
        info["snippets"] = n
    except Exception:
        pass

    return info


def compare(kb, pkg_a, pkg_b):
    a = pkg_info(kb, pkg_a)
    b = pkg_info(kb, pkg_b)

    print()
    print("=" * 65)
    print(f"  {pkg_a.upper():<28s} vs {pkg_b.upper():<28s}")
    print("=" * 65)
    print()

    def row(label, va, vb):
        print(f"  {label:<20s}  {str(va):<24s}  {str(vb):<24s}")

    row("Package", a["name"], b["name"])
    row("Category", a["category"], b["category"])
    row("Resources found", len(a["resources"]), len(b["resources"]))
    row("Avg score", f"{a['score']:.2f}", f"{b['score']:.2f}")
    row("Est. stars", f"{a['stars']:,}", f"{b['stars']:,}")
    row("Snippets", a["snippets"], b["snippets"])
    row("Related count", len(a["related"]), len(b["related"]))

    print()
    print(f"  --- {pkg_a} related ---")
    for n, w in a["related"][:5]:
        print(f"    {n:30s} {w}")
    print(f"  --- {pkg_b} related ---")
    for n, w in b["related"][:5]:
        print(f"    {n:30s} {w}")

    # برنده
    print()
    scores_a = len(a["resources"]) + a["snippets"] + len(a["related"])
    scores_b = len(b["resources"]) + b["snippets"] + len(b["related"])
    if scores_a > scores_b:
        print(f"  🏆 Winner: {pkg_a} ({scores_a} vs {scores_b})")
    elif scores_b > scores_a:
        print(f"  🏆 Winner: {pkg_b} ({scores_b} vs {scores_a})")
    else:
        print(f"  🤝 Tie ({scores_a})")
    print()
