#!/usr/bin/env python3
import os, sqlite3
from pathlib import Path
from datetime import datetime

EVO = Path.home() / "evoscanner"
HOME = Path.home()

def check():
    os.system("clear")
    print("\n  === EvoScanner — وضعیت سلامت ===\n")
    print("  پنل:")
    p = EVO / "panel.py"
    if p.exists():
        try:
            compile(p.read_text(encoding="utf-8"), str(p), "exec")
            lines = len(p.read_text(encoding="utf-8").splitlines())
            print(f"     OK  panel.py  {lines} خط · {p.stat().st_size:,}B")
        except Exception as e:
            print(f"     ERR {e}")
    print("\n  ماژول‌ها:")
    for m in ["selfcare.py","autoheal.py","selfrun.py","engines.py","health.py",
              "panel_test.py","deep_test.py","advisor.py","compare.py",
              "project_ideas.py","evoscanner_v2.py"]:
        f = EVO / m
        print(f"     {'OK ' if f.exists() else '-- '} {m:22} {f.stat().st_size:>7,}B" if f.exists() else f"     --  {m:22} گم")
    print("\n  موتورهای مستقل:")
    for name, p in [("due",HOME/"due"/"due.py"),
                    ("knowledgeforge",HOME/"knowledgeforge"/"knowledgeforge.py"),
                    ("sacred",HOME/"sacred"/"sacred.py"),
                    ("pqasd",HOME/"pqasd"/"pqasd"/"PQASD.py")]:
        print(f"     {'OK ' if p.exists() else '-- '} {name:18} {p.stat().st_size:>9,}B" if p.exists() else f"     --  {name:18} گم")
    print("\n  دیتابیس:")
    db = EVO / "knowledge.db"
    if db.exists():
        try:
            c = sqlite3.connect(db)
            tables = c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            print(f"     OK  knowledge.db  {len(tables)} جدول · {db.stat().st_size:,}B")
            try:
                n = c.execute("SELECT COUNT(*) FROM resources").fetchone()[0]
                print(f"     OK  منابع: {n}")
            except: pass
        except Exception as e:
            print(f"     ERR {e}")
    print("\n  بکاپ‌ها:")
    b = EVO / "BACKUPS"
    if b.exists():
        n = len(list(b.glob("*.py")))
        latest = sorted(b.glob("panel*.py"), key=lambda p: p.stat().st_mtime, reverse=True)
        print(f"     OK  {n} فایل")
        if latest:
            t = datetime.fromtimestamp(latest[0].stat().st_mtime)
            print(f"     آخرین: {latest[0].name}")
            print(f"             {t:%Y-%m-%d %H:%M}")
    print("\n  لاگ‌ها:")
    for log in ["selfrun.log","selfcare.log"]:
        f = EVO / log
        if f.exists():
            print(f"     {log}: {len(f.read_text(encoding='utf-8').splitlines())} خط")
        else:
            print(f"     {log}: نیست")
    print("\n  =======================================")
    input("  ادامه...")

if __name__ == "__main__":
    check()
