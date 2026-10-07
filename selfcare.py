#!/usr/bin/env python3
import os, sys, json, subprocess, shutil, sqlite3
from pathlib import Path
from datetime import datetime
from collections import defaultdict

HOME = Path.home()
EVO  = HOME / "evoscanner"
DB   = EVO / "knowledge.db"
BACKUPS = EVO / "BACKUPS"
LOG = EVO / "selfcare.log"
BACKUPS.mkdir(exist_ok=True)

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")

def scan_syntax():
    errors = []
    for f in list(EVO.glob("*.py")) + list((EVO/"features").glob("*.py")):
        try:
            compile(f.read_text(encoding="utf-8"), str(f), "exec")
        except SyntaxError as e:
            errors.append((f.name, e.lineno, e.msg))
        except Exception as e:
            errors.append((f.name, 0, str(e)))
    return errors

def self_repair():
    os.system("clear")
    print("\n  🔧 خودترمیمی — اسکن خطاها\n")
    log("شروع خودترمیمی")
    print("  [1/2] اسکن سینتکس...")
    errs = scan_syntax()
    if errs:
        print(f"    ⚠ {len(errs)} خطا:")
        for n, l, m in errs[:10]:
            print(f"      ❌ {n}:{l} — {m}")
    else:
        print("    ✓ همه‌ی فایل‌ها سالم")
    print("\n  [2/2] تست import پنل...")
    try:
        r = subprocess.run(["python","-c","import panel"], cwd=str(EVO),
                          capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            print("    ✓ پنل سالم")
        else:
            print(f"    ❌ خطا:\n{r.stderr[-300:]}")
    except Exception as e:
        print(f"    ❌ {e}")
    input("\n  ادامه...")

def knowledge_suggestions():
    if not DB.exists(): return []
    try:
        c = sqlite3.connect(DB)
        c.row_factory = sqlite3.Row
        sug = []
        try:
            for r in c.execute("SELECT signature, COUNT(*) n FROM pattern_instances GROUP BY signature ORDER BY n DESC LIMIT 5"):
                sug.append(("pattern", r["signature"], r["n"]))
        except: pass
        try:
            for r in c.execute("SELECT rule, confidence FROM rules WHERE status LIKE 'verified%' ORDER BY confidence DESC LIMIT 5"):
                sug.append(("rule", r["rule"][:60], r["confidence"]))
        except: pass
        return sug
    except: return []

def self_improve():
    os.system("clear")
    print("\n  ✨ خودارتقایی — پیشنهاد بهبود\n")
    log("شروع خودارتقایی")
    sug = knowledge_suggestions()
    if sug:
        print(f"  از knowledge.db ({len(sug)} مورد):")
        for t, title, val in sug:
            print(f"    [{t}] {title}  ({val})")
    else:
        print("  (دیتابیس خالی یا در دسترس نیست)")
    print("\n  پیشنهادهای کلی:")
    ideas = [
        "اضافه کردن لاگ به ماژول‌ها",
        "یکپارچه‌سازی advisor با knowledge.db",
        "افزودن export به markdown",
        "ساخت پنل Auto-Clean",
        "مرور زمان‌بندی‌شده (Cron)",
    ]
    for i, s in enumerate(ideas, 1):
        print(f"    [{i}] {s}")
    input("\n  ادامه...")

def auto_clean():
    os.system("clear")
    print("\n  🧹 خودکار-صافی\n")
    log("شروع خودکار-صافی")
    print("  [1/4] __pycache__...")
    n = 0
    for p in EVO.rglob("__pycache__"):
        if p.is_dir():
            try: shutil.rmtree(p); n += 1
            except: pass
    print(f"    ✓ {n} پوشه")
    print("  [2/4] *.pyc...")
    n = 0
    for p in EVO.rglob("*.pyc"):
        try: p.unlink(); n += 1
        except: pass
    print(f"    ✓ {n} فایل")
    print("  [3/4] آرشیو بکاپ‌ها...")
    arch = EVO / "archive" / "old_backups"
    arch.mkdir(parents=True, exist_ok=True)
    olds = sorted(BACKUPS.glob("*.py"), key=lambda p: p.stat().st_mtime, reverse=True)[5:]
    n = 0
    for p in olds:
        try: shutil.move(str(p), str(arch/p.name)); n += 1
        except: pass
    print(f"    ✓ {n} بکاپ")
    print("  [4/4] فایل‌های خالی...")
    empty = [p for p in EVO.rglob("*.py") if p.stat().st_size == 0]
    print(f"    {'⚠ ' + str(len(empty)) if empty else '✓ هیچ'}")
    input("\n  ادامه...")

def show_report():
    os.system("clear")
    print("\n  📊 گزارش\n")
    if not LOG.exists():
        print("  لاگی نیست"); input("  ادامه..."); return
    for line in LOG.read_text(encoding="utf-8").splitlines()[-30:]:
        print(f"  {line}")
    input("\n  ادامه...")

def main_menu():
    while True:
        os.system("clear")
        print("\n  ╔══════════════════════════════════════╗")
        print("  ║   ◆ SELF-CARE — ترمیم و ارتقا        ║")
        print("  ╚══════════════════════════════════════╝\n")
        print("  [1]  🔧 خودترمیمی")
        print("  [2]  ✨ خودارتقایی")
        print("  [3]  🧹 خودکار-صافی")
        print("  [4]  📊 گزارش")
        print("  [0]  بازگشت\n")
        try: c = input("  ❯ انتخاب: ").strip()
        except (EOFError, KeyboardInterrupt): return
        if c in ("0", ""): return
        elif c == "1": self_repair()
        elif c == "2": self_improve()
        elif c == "3": auto_clean()
        elif c == "4": show_report()

if __name__ == "__main__":
    main_menu()
