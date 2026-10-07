#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""panel_test.py — تست خودکار همه‌ی گزینه‌های پنل"""
import subprocess, os, re
from pathlib import Path

EVO = Path.home() / "evoscanner"
PANEL = EVO / "panel.py"

OPTIONS = [
    ("1","ASK"), ("2","GET"), ("3","LEARN"), ("4","EVOLVE"),
    ("5","DATA"), ("6","SERVERS"), ("7","GRAPH"), ("8","SOURCES"),
    ("9","IDEAS"), ("10","DASHBOARD"), ("11","HISTORY"),
    ("12","SEARCH"), ("13","TASKS"), ("14","SETTINGS"),
    ("15","ENGINES"), ("16","DUE"), ("17","SELF-CARE"), ("18","AUTO-HEAL"),
]

ERROR_PATTERNS = [
    r"Traceback \(most recent call last\)",
    r"NameError:", r"ImportError:", r"ModuleNotFoundError:",
    r"AttributeError:", r"SyntaxError:", r"TypeError:",
    r"KeyError:", r"IndexError:",
]

def has_error(out):
    for p in ERROR_PATTERNS:
        if re.search(p, out):
            return True, p
    return False, None

def test_one(num, name):
    inputs = [num, "0", "0", "0", "0"]
    stdin = "\n".join(inputs) + "\n"
    try:
        r = subprocess.run(
            ["python", str(PANEL)],
            cwd=str(EVO), input=stdin,
            capture_output=True, text=True, timeout=8,
        )
        out = (r.stdout or "") + (r.stderr or "")
        return {"num":num, "name":name, "code":r.returncode, "out":out, "timeout":False}
    except subprocess.TimeoutExpired as e:
        out = ""
        if e.stdout: out += e.stdout if isinstance(e.stdout,str) else e.stdout.decode("utf-8","ignore")
        if e.stderr: out += e.stderr if isinstance(e.stderr,str) else e.stderr.decode("utf-8","ignore")
        return {"num":num, "name":name, "code":-1, "out":out, "timeout":True}
    except Exception as e:
        return {"num":num, "name":name, "code":-2, "out":str(e), "timeout":False}

def main():
    os.system("clear")
    print("\n  === TEST PANEL v10 ===\n")
    print(f"  تست {len(OPTIONS)} گزینه...\n")
    results = []
    for num, name in OPTIONS:
        print(f"  [{num:>3}] {name:12}...", end=" ", flush=True)
        r = test_one(num, name)
        err, pat = has_error(r["out"])
        r["err"] = err
        r["pat"] = pat
        if r["timeout"]:
            print("TIMEOUT")
        elif err:
            print(f"FAIL: {pat}")
        elif r["code"] != 0:
            print(f"EXIT: {r['code']}")
        else:
            print("OK")
        results.append(r)
    print("\n  === خلاصه ===\n")
    ok = [r for r in results if not r["err"] and not r["timeout"] and r["code"]==0]
    fail = [r for r in results if r["err"] or (r["code"]!=0 and not r["timeout"])]
    tmo = [r for r in results if r["timeout"]]
    print(f"  OK:       {len(ok)}")
    print(f"  FAIL:     {len(fail)}")
    print(f"  TIMEOUT:  {len(tmo)}\n")
    if fail:
        print("  === مشکل‌دار ===\n")
        for r in fail:
            print(f"  [{r['num']}] {r['name']}  err={r['pat']}  exit={r['code']}")
            for line in r["out"].splitlines()[-6:]:
                print(f"      | {line}")
            print()
    if tmo:
        print("  === timeout ===\n")
        for r in tmo:
            print(f"  [{r['num']}] {r['name']}")
    rep = EVO / "panel_test_report.txt"
    with rep.open("w", encoding="utf-8") as f:
        f.write("PANEL TEST\n" + "="*40 + "\n")
        for r in results:
            st = "OK" if (not r["err"] and not r["timeout"] and r["code"]==0) else "FAIL"
            f.write(f"[{st}] {r['num']:>3} {r['name']}")
            if r["err"]: f.write(f"  ERR:{r['pat']}")
            if r["timeout"]: f.write("  TIMEOUT")
            f.write("\n")
    print(f"\n  گزارش: {rep}\n")

if __name__ == "__main__":
    main()
