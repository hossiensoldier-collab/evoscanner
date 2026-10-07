"""Recommend packages based on what you already use"""
from pathlib import Path
import json

BASE = Path.home() / "evoscanner"


def _load_graph():
    try:
        return json.loads((BASE / "graph.json").read_text())
    except Exception:
        return {"cooc": {}, "nodes": {}, "edges": {}}


def for_packages(pkgs, n=10):
    """پیشنهاد بر اساس چند پکیج که داری"""
    g = _load_graph()
    cooc = g.get("cooc", {})
    have = set(p.lower() for p in pkgs)

    scores = {}
    for pair, w in cooc.items():
        a, b = pair.split("|", 1)
        if a.startswith("cat:") or b.startswith("cat:"):
            continue
        if a in have and b not in have:
            scores[b] = scores.get(b, 0) + w
        elif b in have and a not in have:
            scores[a] = scores.get(a, 0) + w

    out = sorted(scores.items(), key=lambda x: -x[1])
    return out[:n]


def for_code(code, n=10):
    """پیشنهاد بر اساس importهای کد"""
    import re
    imports = re.findall(r'^(?:import|from)\s+([a-z][a-z0-9_]+)',
                         code, re.M)
    if not imports:
        return []
    return for_packages(list(set(imports)), n=n)


def from_file(path, n=10):
    try:
        code = Path(path).read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        print(f"  خطا: {e}")
        return []
    return for_code(code, n=n)


def show(pkgs, n=10):
    print()
    print("=" * 62)
    print(f"  🎯 پیشنهاد بر اساس: {', '.join(pkgs[:5])}")
    print("=" * 62)
    print()

    recs = for_packages(pkgs, n=n)
    if not recs:
        print("  ⚠ چیزی پیدا نشد. اول منابع بیشتری جمع کن.")
        return

    print(f"  {'پکیج':<28s} {'وزن':>6s}")
    print("  " + "─" * 40)
    for pkg, w in recs:
        bar = "#" * min(w, 25)
        print(f"  {pkg:<28s} {w:>6d}  {bar}")


def show_from_code(code, n=10):
    import re
    imports = re.findall(r'^(?:import|from)\s+([a-z][a-z0-9_]+)',
                         code, re.M)
    if not imports:
        print("\n  ⚠ هیچ import پیدا نشد")
        return
    print(f"\n  importها: {', '.join(sorted(set(imports))[:10])}")
    show(list(set(imports)), n=n)
