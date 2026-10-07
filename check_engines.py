#!/usr/bin/env python3
"""چک می‌کنه v10 به کدوم موتورها وصله"""
import os, sys, subprocess
from pathlib import Path

HOME = Path.home()
EVO = HOME / "evoscanner"

engines = {
    "due":         HOME / "due" / "due.py",
    "knowledgeforge": HOME / "knowledgeforge" / "knowledgeforge.py",
    "knowledge.db": HOME / "knowledgeforge" / "knowledge.db",
    "sacred":      HOME / "sacred" / "sacred.py",
    "pqasd":       HOME / "pqasd" / "pqasd" / "PQASD.py",
    "evoscanner_v2": EVO / "evoscanner_v2.py",
    "graph":       EVO / "graph.py",
    "rag":         EVO / "rag.py",
    "selfmod":     EVO / "selfmod.py",
    "feature_meta": EVO / "feature_meta.py",
    "feature_analytics": EVO / "feature_analytics.py",
}

print("═══ موجودیت موتورها ═══")
for name, p in engines.items():
    if p.exists():
        size = p.stat().st_size
        print(f"  ✅ {name:20} {size:>10,}B  {p}")
    else:
        print(f"  ❌ {name:20} پیدا نشد  {p}")

print()
print("═══ v10 به چی import می‌ده ═══")
panel = EVO / "panel_v10_GOOD.py"
if panel.exists():
    import re
    txt = panel.read_text()
    imports = re.findall(r'^\s*(?:import|from)\s+([\w\.]+)', txt, re.M)
    for m in sorted(set(imports)):
        print(f"  → {m}")

print()
print("═══ v10 کدوم اسکریپت‌ها رو صدا می‌زنه ═══")
if panel.exists():
    txt = panel.read_text()
    calls = re.findall(r'["\']([\w\.]+\.py)["\']', txt)
    for c in sorted(set(calls)):
        print(f"  ▸ {c}")
    # subprocess.run/hunter/evolve ...
    cmds = re.findall(r'run_py\(["\']([\w\.]+)', txt)
    for c in sorted(set(cmds)):
        print(f"  ▸ run_py: {c}")

print()
print("═══ due.py چی صادر می‌کنه ═══")
due = HOME / "due" / "due.py"
if due.exists():
    import re
    txt = due.read_text()
    classes = re.findall(r'^class\s+(\w+)', txt, re.M)
    print(f"  تعداد کلاس: {len(classes)}")
    print(f"  {', '.join(classes[:20])}...")

print()
print("═══ knowledgeforge دیتابیس چقدر پره ═══")
import sqlite3
db = HOME / "knowledgeforge" / "knowledge.db"
if db.exists():
    c = sqlite3.connect(db)
    for t in ["sources","artifacts","evidence","nodes","edges","rules","pattern_instances"]:
        try:
            n = c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            print(f"  {t:20} {n:>8,}")
        except Exception as e:
            print(f"  {t:20} ERR: {e}")
