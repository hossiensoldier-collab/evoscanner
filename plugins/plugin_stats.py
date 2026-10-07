#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""plugin_stats — آمار سریع پروژه"""
import sqlite3, os
from pathlib import Path

PLUGIN = {
    "name": "STATS",
    "menu": 31,
    "description": "آمار سریع",
    "handler": "run",
    "version": "1.0",
}

def run():
    os.system("clear")
    EVO = Path.home() / "evoscanner"
    print("\n  ╔══════════════════════════════════════════════╗")
    print("  ║   📊 آمار سریع                                ║")
    print("  ╚══════════════════════════════════════════════╝\n")

    # فایل‌های پایتون
    py = list(EVO.glob("*.py"))
    lines = sum(len(p.read_text(encoding="utf-8").splitlines()) for p in py if p.exists())
    print(f"  📄 فایل‌های پایتون: {len(py)}")
    print(f"  📝 خطوط کد: {lines:,}")

    # دیتابیس
    db = EVO / "knowledge.db"
    if db.exists():
        try:
            c = sqlite3.connect(db)
            n = c.execute("SELECT COUNT(*) FROM resources").fetchone()[0]
            print(f"  💾 منابع: {n}")
        except: pass

    # بکاپ
    b = EVO / "BACKUPS"
    if b.exists():
        print(f"  🛡 بکاپ‌ها: {len(list(b.glob('*.py')))}")

    print()
    input("  ادامه...")

if __name__ == "__main__":
    run()
