#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""engines.py — Wrapper برای موتورهای مستقل evoscanner"""
import os, subprocess, json
from pathlib import Path

HOME = Path.home()
DUE    = HOME / "due" / "due.py"
FORGE  = HOME / "knowledgeforge" / "knowledgeforge.py"
FORGEDB= HOME / "knowledgeforge" / "knowledge.db"
SACRED = HOME / "sacred" / "sacred.py"
QASD   = HOME / "pqasd" / "pqasd" / "PQASD.py"

class C:
    R="\033[0m"; B="\033[1m"; D="\033[2m"
    CY="\033[38;2;100;220;230m"
    PU="\033[38;2;180;140;255m"
    YL="\033[38;2;255;215;80m"
    GR="\033[38;2;120;230;150m"
    RD="\033[38;2;255;110;110m"
    OR="\033[38;2;255;160;80m"
    GY="\033[38;2;130;135;150m"

def clear(): os.system("clear")
def pause(m="ادامه"):
    try: input(f"\n  {C.D}{m}...{C.R}")
    except (EOFError, KeyboardInterrupt): pass

def ask(prompt="انتخاب", default=""):
    try:
        v = input(f"\n  {C.CY}❯{C.R} {prompt}" + (f" [{default}]" if default else "") + f" {C.CY}:{C.R} ").strip()
        return v or default
    except (EOFError, KeyboardInterrupt): return None

def header(t):
    print(f"\n  {C.PU}{C.B}╭─ {t}{C.R}")

def run_script(path, *args):
    if not path.exists():
        print(f"  {C.RD}✕ پیدا نشد: {path}{C.R}"); pause(); return
    try:
        subprocess.run(["python3", str(path), *args], cwd=str(path.parent))
    except KeyboardInterrupt:
        print(f"\n  {C.YL}لغو شد{C.R}")
    pause()

def run_bg(path, *args):
    if not path.exists():
        print(f"  {C.RD}✕ پیدا نشد: {path}{C.R}"); return
    subprocess.Popen(["python3", str(path), *args], cwd=str(path.parent))

# ═══════════════════════════════════════════════════
def due_menu():
    while True:
        clear()
        header("DUE — موتور خودارتقایی")
        p = DUE
        if p.exists():
            n = sum(1 for _ in p.open())
            print(f"  {C.GY}مسیر: {p}{C.R}")
            print(f"  {C.GR}خطوط: {n}{C.R}  {C.GY}· ۵۱ کلاس · {p.stat().st_size:,}B{C.R}")
        print()
        print(f"  {C.CY}[1]{C.R} Analyze           تحلیل یک فایل پایتون")
        print(f"  {C.CY}[2]{C.R} GSL               استخراج GSL")
        print(f"  {C.CY}[3]{C.R} Usage             راهنما (Usage)")
        print(f"  {C.CY}[4]{C.R} Classes           لیست ۵۱ کلاس")
        print(f"  {C.CY}[5]{C.R} Interactive       اجرای تعاملی")
        print(f"  {C.RD}[0]{C.R} BACK")
        c = ask()
        if c in (None, "0"): return
        if c == "1":
            f = ask("فایل پایتون", str(HOME/"evoscanner"/"panel.py"))
            if f: run_script(p, "analyze", f)
        elif c == "2":
            f = ask("فایل پایتون", str(HOME/"evoscanner"/"panel.py"))
            if f: run_script(p, "gsl", f)
        elif c == "3": run_script(p)
        elif c == "4":
            import re
            classes = re.findall(r'^class\s+(\w+)', p.read_text(), re.M)
            clear(); header(f"DUE — {len(classes)} کلاس")
            for i, cl in enumerate(classes, 1):
                print(f"  {C.GR}{i:3}{C.R}  {C.CY}{cl}{C.R}")
            pause()
        elif c == "5": run_script(p)

def forge_menu():
    while True:
        clear()
        header("FORGE — موتور دانش")
        print(f"  {C.GY}DB: {FORGEDB} ({FORGEDB.stat().st_size:,}B){C.R}\n")
        # آمار DB
        try:
            import sqlite3
            c = sqlite3.connect(FORGEDB)
            stats = {t: c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                     for t in ["sources","artifacts","evidence","nodes","edges","rules"]}
            print(f"  {C.GR}sources={stats['sources']}  nodes={stats['nodes']}  edges={stats['edges']}  rules={stats['rules']}{C.R}\n")
        except Exception as e:
            print(f"  {C.RD}DB err: {e}{C.R}\n")
        print(f"  {C.CY}[1]{C.R} Help              راهنما")
        print(f"  {C.CY}[2]{C.R} Stats             آمار")
        print(f"  {C.CY}[3]{C.R} Top nodes         نودهای برتر")
        print(f"  {C.CY}[4]{C.R} Rules             قواعد")
        print(f"  {C.CY}[5]{C.R} Interactive       تعاملی")
        print(f"  {C.RD}[0]{C.R} BACK")
        c = ask()
        if c in (None, "0"): return
        if c == "1": run_script(FORGE, "--help")
        elif c == "2": run_script(FORGE, "stats")
        elif c == "3": run_script(FORGE, "top")
        elif c == "4": run_script(FORGE, "rules")
        elif c == "5": run_script(FORGE)

def sacred_menu():
    while True:
        clear()
        header("SACRED — فارسی ← شکل ← کد")
        print(f"  {C.GY}مسیر: {SACRED}{C.R}\n")
        print(f"  {C.CY}[1]{C.R} Help              راهنما")
        print(f"  {C.CY}[2]{C.R} Ask               سؤال")
        print(f"  {C.CY}[3]{C.R} Translate         ترجمه (به Rust/JS/...)")
        print(f"  {C.CY}[4]{C.R} Analyze           تحلیل فایل")
        print(f"  {C.CY}[5]{C.R} Scan              اسکن دایرکتوری")
        print(f"  {C.CY}[6]{C.R} Shapes            اشکال")
        print(f"  {C.CY}[7]{C.R} REPL              حالت تعاملی")
        print(f"  {C.RD}[0]{C.R} BACK")
        c = ask()
        if c in (None, "0"): return
        if c == "1": run_script(SACRED, "--help")
        elif c == "2":
            q = ask("سؤال")
            if q: run_script(SACRED, "ask", q)
        elif c == "3":
            q = ask("متن"); t = ask("زبان", "rust")
            if q: run_script(SACRED, "translate", q, "--to", t)
        elif c == "4":
            f = ask("فایل")
            if f: run_script(SACRED, "analyze", f)
        elif c == "5":
            d = ask("دایرکتوری", str(HOME/"evoscanner"))
            if d: run_script(SACRED, "scan", d)
        elif c == "6": run_script(SACRED, "shapes")
        elif c == "7": run_script(SACRED, "repl")

def qasd_menu():
    while True:
        clear()
        header("QASD — هندسه مقدس")
        print(f"  {C.GY}مسیر: {QASD}{C.R}\n")
        print(f"  {C.CY}[1]{C.R} Run         اجرا")
        print(f"  {C.CY}[2]{C.R} GUI         رابط وب (127.0.0.1:8787)")
        print(f"  {C.RD}[0]{C.R} BACK")
        c = ask()
        if c in (None, "0"): return
        if c == "1": run_script(QASD)
        elif c == "2":
            gui = HOME/"pqasd"/"start_gui.py"
            if gui.exists():
                run_bg(gui)
                print(f"  {C.GR}✓ GUI در http://127.0.0.1:8787{C.R}")
            else:
                print(f"  {C.RD}✕ start_gui.py پیدا نشد{C.R}")
            pause()

def engines_menu():
    while True:
        clear()
        header("ENGINES — موتورهای مستقل")
        print(f"  {C.GY}موتورهای خارج از evoscanner{C.R}\n")
        print(f"  {C.PU}[1]{C.R} DUE      {C.CY}خودارتقایی{C.R}      {C.GY}4556 خط{C.R}")
        print(f"  {C.PU}[2]{C.R} FORGE    {C.CY}دانش SQLite{C.R}     {C.GY}730 node{C.R}")
        print(f"  {C.PU}[3]{C.R} SACRED   {C.CY}فارسی → کد{C.R}")
        print(f"  {C.PU}[4]{C.R} QASD     {C.CY}هندسه مقدس{C.R}")
        print(f"  {C.RD}[0]{C.R} BACK")
        c = ask()
        if c in (None, "0"): return
        if c == "1": due_menu()
        elif c == "2": forge_menu()
        elif c == "3": sacred_menu()
        elif c == "4": qasd_menu()

if __name__ == "__main__":
    engines_menu()
