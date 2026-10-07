"""Autopilot — خودش تصمیم می‌گیرد چه کار کند"""
import json
import subprocess
import sys
import time
from pathlib import Path

BASE = Path.home() / "evoscanner"
os_dir = BASE

C = {
    "R": "\033[0;31m", "G": "\033[0;32m", "Y": "\033[1;33m",
    "Cy": "\033[0;36m", "M": "\033[0;35m",
    "W": "\033[1;37m", "D": "\033[0m",
    "Bold": "\033[1m", "Dim": "\033[2m",
}


def stats():
    st = {"src": 0, "graph": 0, "tech": 0, "snip": 0}
    try:
        import sqlite3
        db = sqlite3.connect(BASE / "knowledge.db")
        st["src"] = db.execute("SELECT COUNT(*) FROM resources").fetchone()[0]
        for k, t in [("tech", "techniques"), ("snip", "snippets")]:
            try:
                st[k] = db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            except Exception:
                pass
        db.close()
    except Exception:
        pass
    try:
        g = json.loads((BASE / "graph.json").read_text())
        st["graph"] = sum(1 for v in g["nodes"].values()
                          if v.get("type") == "entity")
    except Exception:
        pass
    return st


def run(cmd_args):
    try:
        subprocess.run([sys.executable, "evoscanner_v2.py"] + cmd_args,
                       cwd=str(BASE))
        return True
    except KeyboardInterrupt:
        return False
    except Exception:
        return False


def run_py(script, *args):
    try:
        subprocess.run([sys.executable, script] + list(args),
                       cwd=str(BASE))
        return True
    except Exception:
        return False


def step(n, total, text):
    print()
    print(f"  {C['M']}[{n}/{total}]{C['D']} {C['Bold']}{C['W']}{text}{C['D']}")
    print(f"  {C['Dim']}{'─' * 50}{C['D']}")


def decide():
    """تصمیم می‌گیرد چه کار کند"""
    s = stats()
    plan = []

    # منطق تصمیم
    if s["src"] < 300:
        plan.append(("chرخه کشف منابع", ["run", "3"]))
        plan.append(("بازسازی گراف", ["rebuild"]))
    elif s["src"] < 500:
        plan.append(("enrich README", ["enrich", "50"]))
        plan.append(("بازسازی گراف", ["rebuild"]))
    else:
        plan.append(("chرخه بیشتر", ["run", "2"]))

    if s["tech"] < 100:
        plan.append(("استخراج دانش", "python:learn.py:extract"))

    if s["graph"] < 600:
        plan.append(("بازسازی گراف", ["rebuild"]))

    # همیشه: چرخه یادگیری
    plan.append(("چرخه خودکار Meta", "python:feature_meta.py:cycle"))

    # همیشه: پشتیبان
    plan.append(("ساخت snapshot", "python:feature_snapshot.py:build"))

    return plan


def autopilot():
    print()
    print(f"  {C['Cy']}╔══════════════════════════════════════════════════╗{C['D']}")
    print(f"  {C['Cy']}║{C['D']} {C['M']}{C['Bold']}◆ AUTOPILOT{C['D']}"
          f"{C['Dim']}  خودش تصمیم می‌گیرد{C['D']}"
          f"{' ' * 15}{C['Cy']}║{C['D']}")
    print(f"  {C['Cy']}╚══════════════════════════════════════════════════╝{C['D']}")

    s = stats()
    print()
    print(f"  {C['Dim']}وضعیت فعلی:{C['D']}")
    print(f"    resources: {C['Y']}{s['src']}{C['D']}   "
          f"graph: {C['Cy']}{s['graph']}{C['D']}   "
          f"tech: {C['G']}{s['tech']}{C['D']}   "
          f"snip: {C['G']}{s['snip']}{C['D']}")

    plan = decide()
    print()
    print(f"  {C['Dim']}برنامه:{C['D']}")
    for i, (name, _) in enumerate(plan, 1):
        print(f"    {i}. {name}")

    print()
    try:
        input(f"  {C['Dim']}Enter برای شروع...{C['D']}")
    except (EOFError, KeyboardInterrupt):
        return

    for i, (name, action) in enumerate(plan, 1):
        step(i, len(plan), name)
        if isinstance(action, list):
            run(action)
        elif isinstance(action, str) and action.startswith("python:"):
            parts = action.split(":")
            run_py(parts[1], *parts[2:])
        print(f"  {C['G']}✓{C['D']} تمام")

    # خلاصه
    s2 = stats()
    print()
    print(f"  {C['Cy']}╔══════════════════════════════════════════════════╗{C['D']}")
    print(f"  {C['Cy']}║{C['D']} {C['G']}{C['Bold']}✓ AUTOPILOT تمام شد{C['D']}"
          f"{' ' * 25}{C['Cy']}║{C['D']}")
    print(f"  {C['Cy']}╚══════════════════════════════════════════════════╝{C['D']}")
    print()

    def diff(a, b):
        d = b - a
        col = C['G'] if d > 0 else (C['R'] if d < 0 else C['Dim'])
        sign = "+" if d > 0 else ""
        return f"{col}{sign}{d}{C['D']}"

    print(f"    resources: {s['src']} → {C['Y']}{s2['src']}{C['D']}  "
          f"({diff(s['src'], s2['src'])})")
    print(f"    graph:     {s['graph']} → {C['Cy']}{s2['graph']}{C['D']}  "
          f"({diff(s['graph'], s2['graph'])})")
    print(f"    tech:      {s['tech']} → {C['G']}{s2['tech']}{C['D']}  "
          f"({diff(s['tech'], s2['tech'])})")
    print(f"    snip:      {s['snip']} → {C['G']}{s2['snip']}{C['D']}  "
          f"({diff(s['snip'], s2['snip'])})")
    print()
    try:
        input(f"  {C['Dim']}Enter...{C['D']}")
    except (EOFError, KeyboardInterrupt):
        pass


if __name__ == "__main__":
    import os
    try:
        autopilot()
    except KeyboardInterrupt:
        print()

