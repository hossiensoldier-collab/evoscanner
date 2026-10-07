#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""deep_test.py — تست داخلی همه‌ی زیرمنوهای پنل"""
import subprocess, os, re
from pathlib import Path

EVO = Path.home() / "evoscanner"
PANEL = EVO / "panel.py"

# (مسیر ورودی‌ها، توضیح)
# هر تاپل: لیست ورودی‌هایی که به پنل می‌دیم تا برسیم به یه صفحه
CASES = [
    # منوی اصلی
    (["1","0","0"],   "ASK"),
    (["2","0","0"],   "GET"),
    (["3","0","0"],   "LEARN"),
    (["4","0","0"],   "EVOLVE"),
    (["5","0","0"],   "DATA"),
    (["6","0","0"],   "SERVERS"),
    (["7","0","0"],   "GRAPH"),
    (["8","0","0"],   "SOURCES"),
    (["9","0","0"],   "IDEAS"),
    (["10","0","0"],  "DASHBOARD"),
    (["11","0","0"],  "HISTORY"),
    (["12","0","0"],  "SEARCH"),
    (["13","0","0"],  "TASKS"),
    (["14","0","0"],  "SETTINGS"),
    (["15","0","0"],  "ENGINES"),
    (["16","0","0"],  "DUE"),
    (["17","0","0"],  "SELF-CARE"),
    (["18","0","0"],  "AUTO-HEAL"),
    (["19","0","0"],  "HEALTH"),

    # داخل ASK (1)
    (["1","1","0","0"],   "ASK → 1"),
    (["1","2","0","0"],   "ASK → 2"),
    (["1","3","0","0"],   "ASK → 3"),
    (["1","4","0","0"],   "ASK → 4"),
    (["1","5","0","0"],   "ASK → 5"),
    (["1","6","0","0"],   "ASK → 6"),

    # داخل GET (2)
    (["2","1","0","0"],   "GET → 1"),
    (["2","2","0","0"],   "GET → 2"),
    (["2","3","0","0"],   "GET → 3"),
    (["2","4","0","0"],   "GET → 4"),
    (["2","5","0","0"],   "GET → 5"),

    # داخل LEARN (3)
    (["3","1","0","0"],   "LEARN → 1"),
    (["3","2","0","0"],   "LEARN → 2"),
    (["3","3","0","0"],   "LEARN → 3"),
    (["3","4","0","0"],   "LEARN → 4"),

    # داخل EVOLVE (4)
    (["4","1","0","0"],   "EVOLVE → 1 (AGENTS)"),
    (["4","2","0","0"],   "EVOLVE → 2 (META)"),
    (["4","3","0","0"],   "EVOLVE → 3 (METADATA)"),
    (["4","4","0","0"],   "EVOLVE → 4 (CAPABILITY)"),
    (["4","5","0","0"],   "EVOLVE → 5 (ANALYZE)"),
    (["4","6","0","0"],   "EVOLVE → 6 (SNAPSHOT)"),
    (["4","8","0","0"],   "EVOLVE → 8 (DEPS)"),
    (["4","9","0","0"],   "EVOLVE → 9 (ORACLE)"),
    (["4","10","0","0"],  "EVOLVE → 10 (ANALYTICS)"),
    (["4","11","0","0"],  "EVOLVE → 11 (ADVANCED)"),

    # داخل DATA (5)
    (["5","1","0","0"],   "DATA → 1"),
    (["5","2","0","0"],   "DATA → 2"),
    (["5","3","0","0"],   "DATA → 3"),
    (["5","4","0","0"],   "DATA → 4"),

    # داخل SERVERS (6)
    (["6","1","0","0"],   "SERVERS → 1"),
    (["6","2","0","0"],   "SERVERS → 2"),
    (["6","3","0","0"],   "SERVERS → 3"),

    # داخل GRAPH (7)
    (["7","1","0","0"],   "GRAPH → 1 (TOP)"),
    (["7","6","0","0"],   "GRAPH → 6 (CAT)"),

    # داخل ENGINES (15)
    (["15","1","0","0","0"],  "ENGINES → 1 (DUE)"),
    (["15","2","0","0","0"],  "ENGINES → 2 (FORGE)"),
    (["15","3","0","0","0"],  "ENGINES → 3 (SACRED)"),
    (["15","4","0","0","0"],  "ENGINES → 4 (QASD)"),

    # داخل DUE (16)
    (["16","4","0","0"],   "DUE → 4 (Classes)"),

    # داخل SELF-CARE (17)
    (["17","1","0","0"],   "SELF-CARE → 1 (ترمیم)"),
    (["17","2","0","0"],   "SELF-CARE → 2 (ارتقا)"),
    (["17","3","0","0"],   "SELF-CARE → 3 (صافی)"),
    (["17","4","0","0"],   "SELF-CARE → 4 (گزارش)"),

    # داخل SETTINGS (14)
    (["14","1","0","0"],   "SETTINGS → 1"),
    (["14","2","0","0"],   "SETTINGS → 2"),
    (["14","3","0","0"],   "SETTINGS → 3"),
]

ERROR_PATTERNS = [
    r"Traceback \(most recent call last\)",
    r"NameError:", r"ImportError:", r"ModuleNotFoundError:",
    r"AttributeError:", r"SyntaxError:", r"TypeError:",
    r"KeyError:", r"IndexError:", r"ValueError:",
    r"FileNotFoundError:", r"File \"[^\"]+\", line \d+",
    r"خطا:.*not defined",
]

def has_error(out):
    for p in ERROR_PATTERNS:
        if re.search(p, out):
            return True, p
    return False, None

def test_case(inputs, label):
    stdin = "\n".join(inputs) + "\n"
    try:
        r = subprocess.run(
            ["python", str(PANEL)],
            cwd=str(EVO), input=stdin,
            capture_output=True, text=True, timeout=6,
        )
        out = (r.stdout or "") + (r.stderr or "")
        return {"label": label, "code": r.returncode, "out": out, "timeout": False, "inputs": inputs}
    except subprocess.TimeoutExpired as e:
        out = ""
        if e.stdout: out += e.stdout if isinstance(e.stdout,str) else e.stdout.decode("utf-8","ignore")
        if e.stderr: out += e.stderr if isinstance(e.stderr,str) else e.stderr.decode("utf-8","ignore")
        return {"label": label, "code": -1, "out": out, "timeout": True, "inputs": inputs}
    except Exception as e:
        return {"label": label, "code": -2, "out": str(e), "timeout": False, "inputs": inputs}

def main():
    os.system("clear")
    print("\n  === DEEP TEST — زیرمنوها ===\n")
    print(f"  تست {len(CASES)} مسیر...\n")
    results = []
    for inputs, label in CASES:
        print(f"  {label:35}...", end=" ", flush=True)
        r = test_case(inputs, label)
        err, pat = has_error(r["out"])
        r["err"] = err
        r["pat"] = pat
        if r["timeout"]:
            print("TIMEOUT")
        elif err:
            print(f"FAIL: {pat}")
        elif r["code"] != 0:
            print(f"EXIT {r['code']}")
        else:
            print("OK")
        results.append(r)

    print("\n  === خلاصه ===\n")
    ok = [r for r in results if not r["err"] and not r["timeout"] and r["code"]==0]
    fail = [r for r in results if r["err"]]
    tmo = [r for r in results if r["timeout"]]
    ex = [r for r in results if r["code"] != 0 and not r["timeout"] and not r["err"]]
    print(f"  OK:       {len(ok)}")
    print(f"  FAIL:     {len(fail)}")
    print(f"  TIMEOUT:  {len(tmo)}")
    print(f"  EXIT≠0:   {len(ex)}\n")

    if fail:
        print("  === خطاها ===\n")
        for r in fail:
            print(f"  ✗ {r['label']}")
            print(f"      الگو: {r['pat']}")
            for line in r["out"].splitlines()[-6:]:
                print(f"      | {line}")
            print()

    if tmo:
        print("  === timeout ===\n")
        for r in tmo:
            print(f"  ⏱ {r['label']}  inputs={r['inputs']}")
        print()

    # ذخیره گزارش
    rep = EVO / "deep_test_report.txt"
    with rep.open("w", encoding="utf-8") as f:
        f.write("DEEP PANEL TEST\n" + "="*60 + "\n\n")
        for r in results:
            st = "OK" if (not r["err"] and not r["timeout"] and r["code"]==0) else "FAIL"
            f.write(f"[{st}] {r['label']}  inputs={r['inputs']}\n")
            if r["err"]: f.write(f"     ERR: {r['pat']}\n")
            if r["timeout"]: f.write(f"     TIMEOUT\n")
            f.write("\n")
    print(f"  گزارش: {rep}\n")

if __name__ == "__main__":
    main()
