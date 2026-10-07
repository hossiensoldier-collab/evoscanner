#!/usr/bin/env python3
import os, re, shutil
from pathlib import Path
from datetime import datetime

EVO = Path.home() / "evoscanner"
BACKUPS = EVO / "BACKUPS"
BACKUPS.mkdir(exist_ok=True)

def backup(f):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = BACKUPS / f"{f.name}.{ts}.autoheal"
    shutil.copy2(f, dest)
    return dest

def diagnose(panel):
    issues = []
    src = panel.read_text(encoding="utf-8")
    for m in re.finditer(r'\{([A-Z])\}', src):
        name = m.group(1)
        if f"{name} =" not in src and f"class {name}" not in src and f"C.{name}" not in src:
            line_no = src[:m.start()].count("\n") + 1
            issues.append({"type": "undefined", "name": name, "line": line_no})
    if re.search(r'try:\s*\n\s*pass\s*\n\s*except', src):
        issues.append({"type": "silent_try"})
    return issues

def fix_undefined(panel, issues):
    src = panel.read_text(encoding="utf-8")
    fixed = 0
    for issue in issues:
        if issue["type"] == "undefined":
            old = "{" + issue["name"] + "}"
            new = "{C." + issue["name"] + "}"
            if old in src:
                src = src.replace(old, new)
                fixed += 1
    if fixed > 0:
        backup(panel)
        panel.write_text(src, encoding="utf-8")
    return fixed

def run():
    os.system("clear")
    print("\n  AUTO-HEAL\n")
    panel = EVO / "panel.py"
    if not panel.exists():
        print("  panel.py نیست"); input("  ادامه..."); return
    print(f"  تشخیص {panel.name}...")
    issues = diagnose(panel)
    if not issues:
        print("  هیچ مشکلی نیست"); input("\n  ادامه..."); return
    print(f"\n  {len(issues)} مورد:")
    for i, iss in enumerate(issues, 1):
        if iss["type"] == "undefined":
            print(f"    [{i}] {iss['name']} (خط {iss['line']}) -> C.{iss['name']}")
        elif iss["type"] == "silent_try":
            print(f"    [{i}] try/except خالی")
    fixable = [i for i in issues if i["type"] == "undefined"]
    if fixable:
        ans = input("\n  تعمیر؟ (y/n): ").strip().lower()
        if ans == "y":
            n = fix_undefined(panel, fixable)
            print(f"  {n} مورد اصلاح شد")
    input("\n  ادامه...")

if __name__ == "__main__":
    run()
