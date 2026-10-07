#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cortex_chain.py — CORTEX چند-مرحله‌ای"""
import os, sys, json, time
from pathlib import Path
from datetime import datetime

EVO = Path.home() / "evoscanner"
sys.path.insert(0, str(EVO))

import cortex

def run_chain(goals, pause_between=True):
    """چند هدف رو زنجیره‌ای اجرا کن"""
    os.system("clear")
    print()
    print("  ╔══════════════════════════════════════════════╗")
    print("  ║   🔗 CORTEX CHAIN — چند-مرحله‌ای             ║")
    print("  ╚══════════════════════════════════════════════╝\n")
    print(f"  {len(goals)} مرحله:\n")
    for i, g in enumerate(goals, 1):
        print(f"    {i}. {g}")
    print()

    results = []
    for i, goal in enumerate(goals, 1):
        print(f"\n  ┌─ مرحله {i}/{len(goals)}: {goal} ─────")
        state = cortex.perceive()
        steps = cortex.plan(goal)
        print(f"  PLAN: {' → '.join(s[0] for s in steps)}\n")

        results_act = []
        for name, desc in steps:
            fn = cortex.ACT.get(name)
            if not fn:
                results_act.append(None); continue
            try:
                r = fn(goal, state)
            except Exception as e:
                r = f"⚠ {e}"
            results_act.append(r)
            s = str(r).split("\n")[0][:60] if r else "(خالی)"
            print(f"    ▸ {name}: {s}")

        fb = cortex.reflect(steps, results_act)
        print(f"\n  REFLECT: {fb['score']}% ({fb['ok']}/{fb['total']})")
        results.append({"goal": goal, "score": fb["score"], "steps": steps})

        # ذخیره در حافظه
        mem = cortex.load_mem()
        mem["sessions"].append({
            "ts": datetime.now().isoformat(),
            "goal": f"[CHAIN {i}] {goal}",
            "score": fb["score"],
            "steps": [s[0] for s in steps],
        })
        for name, _ in steps:
            if name not in mem["skills"]:
                mem["skills"][name] = {"used": 0, "success": 0}
            mem["skills"][name]["used"] += 1
            if fb["score"] >= 60:
                mem["skills"][name]["success"] += 1
        cortex.save_mem(mem)

        if pause_between and i < len(goals):
            input(f"\n  [Enter برای مرحله بعد]")

    # خلاصه
    print()
    print("  ╔══════════════════════════════════════════════╗")
    print("  ║   📊 خلاصه زنجیره                            ║")
    print("  ╚══════════════════════════════════════════════╝\n")
    avg = sum(r["score"] for r in results) / len(results) if results else 0
    for i, r in enumerate(results, 1):
        bar = "█" * (r["score"] // 10) + "░" * (10 - r["score"] // 10)
        print(f"  {i}. {bar} {r['score']:>3}%  {r['goal'][:45]}")
    print(f"\n  🎯 میانگین: {avg:.0f}%")

    input("\n  ادامه...")


def main_menu():
    while True:
        os.system("clear")
        print()
        print("  ╔══════════════════════════════════════════════╗")
        print("  ║   🔗 CORTEX CHAIN                            ║")
        print("  ╚══════════════════════════════════════════════╝\n")
        print("  [1]  زنجیره‌ی آماده: تحلیل کامل")
        print("  [2]  زنجیره‌ی آماده: بهبود + تست")
        print("  [3]  زنجیره‌ی آماده: یادگیری + پژوهش")
        print("  [4]  زنجیره‌ی دلخواه")
        print("  [0]  بازگشت\n")

        try: c = input("  ❯ انتخاب: ").strip()
        except (EOFError, KeyboardInterrupt): return

        if c in ("0", ""): return
        elif c == "1":
            run_chain(["تحلیل پروژه", "بهبود پنل"])
        elif c == "2":
            run_chain(["بهبود پنل", "تست پروژه"])
        elif c == "3":
            run_chain(["پژوهش درباره transformers", "یادگیری asyncio"])
        elif c == "4":
            print("\n  هر هدف رو با کاما جدا کن")
            g = input("  ❯ اهداف: ").strip()
            if g:
                goals = [x.strip() for x in g.split(",") if x.strip()]
                if goals: run_chain(goals)


if __name__ == "__main__":
    main_menu()
