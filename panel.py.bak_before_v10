#!/usr/bin/env python3
"""EvoScanner Panel v9 — بازسازی کامل"""
import json, os, subprocess, sys, time
from pathlib import Path

BASE = Path.home() / "evoscanner"
os.chdir(str(BASE))

R="\033[0m"; B="\033[1m"; D="\033[2m"
CY="\033[38;2;100;220;230m"
PU="\033[38;2;180;140;255m"
PK="\033[38;2;255;140;200m"
YL="\033[38;2;255;215;80m"
GR="\033[38;2;120;230;150m"
RD="\033[38;2;255;110;110m"
BL="\033[38;2;120;170;255m"
OR="\033[38;2;255;160;80m"
WH="\033[38;2;230;230;240m"
GY="\033[38;2;130;135;150m"


def clear():
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def ask(p, default=""):
    try:
        prompt = f"{CY}{B}❯{R} {WH}{p}{R}"
        if default:
            prompt += f" {D}[{default}]{R}"
        prompt += f"{CY} : {R}"
        s = input(prompt).strip()
        return s if s else default
    except (EOFError, KeyboardInterrupt):
        print()
        return None


def pause(msg="ادامه"):
    try:
        input(f"\n  {D}{msg}...{R}")
    except (EOFError, KeyboardInterrupt):
        print()


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


def header():
    clear()
    s = stats()
    print()
    print(f"  {CY}──────────────────────────────────────────────────{R}")
    print(f"  {PU}{B}◆{R} {WH}{B}E V O S C A N N E R{R}  {GY}v9.0{R}")
    print(f"  {CY}──────────────────────────────────────────────────{R}")
    print()
    print(f"  {GY}src{R} {YL}{s['src']:>4}{R}   "
          f"{GY}graph{R} {CY}{s['graph']:>4}{R}   "
          f"{GY}tech{R} {GR}{s['tech']:>4}{R}   "
          f"{GY}snip{R} {GR}{s['snip']:>4}{R}")
    print()


def run_cmd(*args):
    try:
        subprocess.run([sys.executable, "evoscanner_v2.py"] + list(args),
                       cwd=str(BASE))
    except KeyboardInterrupt:
        pass


def run_py(script, *args):
    try:
        subprocess.run([sys.executable, script] + list(args), cwd=str(BASE))
    except KeyboardInterrupt:
        pass


def main_menu():
    header()
    print(f"  {PU}{B}┌─ KAR{R}")
    print(f"  {GY}│{R} {CY}{B}[ 1]{R}  {WH}ASK{R}      {D}سؤال · جستجو · مشاور{R}")
    print(f"  {GY}│{R} {YL}{B}[ 2]{R}  {WH}GET{R}      {D}جذب منابع{R}")
    print(f"  {GY}│{R} {BL}{B}[ 7]{R}  {WH}GRAPH{R}    {D}کاوش گراف{R}")
    print(f"  {GY}│{R}")
    print(f"  {PU}{B}┌─ DANESH{R}")
    print(f"  {GY}│{R} {GR}{B}[ 3]{R}  {WH}LEARN{R}    {D}یادگیری{R}")
    print(f"  {GY}│{R} {GR}{B}[12]{R}  {WH}SOURCES{R}  {D}منابع جدید{R}")
    print(f"  {GY}│{R} {GR}{B}[17]{R}  {WH}IDEAS{R}    {D}پیشنهاد پروژه{R}")
    print(f"  {GY}│{R}")
    print(f"  {PU}{B}┌─ SYSTEM{R}")
    print(f"  {GY}│{R} {PK}{B}[ 4]{R}  {WH}EVOLVE{R}   {D}خودارتقایی{R}")
    print(f"  {GY}│{R} {OR}{B}[ 5]{R}  {WH}DATA{R}     {D}خروجی · snapshot{R}")
    print(f"  {GY}│{R} {BL}{B}[ 6]{R}  {WH}SERVERS{R}  {D}API · وب{R}")
    print(f"  {GY}│{R} {RD}{B}[18]{R}  {WH}CLEANUP{R}  {D}پاک‌سازی{R}")
    print(f"  {GY}└─────────────────────────────────────────────────{R}")
    print()
    print(f"  {PU}{B}◆ AUTO{R}   {D}خودکار{R}")
    print(f"  {GR}{B}★ SMART{R}  {D}تایپ آزاد{R}")
    print(f"  {RD}{B}✕ EXIT{R}   {D}خروج{R}")
    print()
    return ask("انتخاب")


def sub_ask():
    while True:
        header()
        print(f"  {CY}{B}┌─ ASK{R}")
        print(f"  {GY}│{R} {CY}{B}[ 1]{R}  {WH}SEARCH{R}  {D}جستجو{R}")
        print(f"  {GY}│{R} {CY}{B}[ 2]{R}  {WH}ASK{R}     {D}پرسش{R}")
        print(f"  {GY}│{R} {CY}{B}[ 3]{R}  {WH}RELATED{R} {D}پکیج مرتبط{R}")
        print(f"  {GY}│{R} {BL}{B}[ 4]{R}  {WH}PATH{R}    {D}مسیر گراف{R}")
        print(f"  {GY}│{R} {GR}{B}[ 5]{R}  {WH}ADVISOR{R} {D}مشاور{R}")
        print(f"  {GY}│{R} {PU}{B}[10]{R}  {WH}RAG4{R}    {D}snippet RAG{R}")
        print(f"  {GY}│{R} {RD}{B}[ 0]{R}  {WH}BACK{R}")
        print(f"  {GY}└─────────────────────────────────────────────────{R}")
        print()
        c = ask("انتخاب")
        if c in (None, "0"): return
        if c == "1":
            q = ask("جستجو")
            if q: clear(); run_cmd("search", q); pause()
        elif c == "2":
            q = ask("سؤال")
            if q: clear(); run_cmd("ask", q); pause()
        elif c == "3":
            p = ask("پکیج")
            if p: clear(); run_cmd("related", p); pause()
        elif c == "4":
            a = ask("از"); b = ask("به")
            if a and b: clear(); run_cmd("graph-path", a, b); pause()
        elif c == "5":
            t = ask("کار", "web framework")
            if t:
                clear()
                run_py("-c", f"""
import sys
sys.path.insert(0, "features")
from evoscanner_v2 import KB
import advisor
advisor.advise(KB(), {t!r})
""")
                pause()
        elif c == "10":
            q = ask("سؤال")
            if q: clear(); run_py("feature_rag_v4.py", q); pause()


def sub_get():
    while True:
        header()
        print(f"  {YL}{B}┌─ GET{R}")
        print(f"  {GY}│{R} {YL}{B}[ 1]{R}  {WH}RUN{R}      {D}چرخه{R}")
        print(f"  {GY}│{R} {YL}{B}[ 2]{R}  {WH}ENRICH{R}   {D}README{R}")
        print(f"  {GY}│{R} {CY}{B}[ 3]{R}  {WH}REBUILD{R}  {D}گراف{R}")
        print(f"  {GY}│{R} {GR}{B}[ 4]{R}  {WH}SOURCES{R}  {D}منابع جدید{R}")
        print(f"  {GY}│{R} {RD}{B}[ 0]{R}  {WH}BACK{R}")
        print(f"  {GY}└─────────────────────────────────────────────────{R}")
        print()
        c = ask("انتخاب")
        if c in (None, "0"): return
        if c == "1":
            n = ask("تعداد", "2")
            clear(); run_cmd("reset-health"); run_cmd("run", n); run_cmd("rebuild"); pause()
        elif c == "2":
            n = ask("تعداد", "50")
            clear(); run_cmd("enrich", n); run_cmd("rebuild"); pause()
        elif c == "3":
            clear(); run_cmd("rebuild"); pause()
        elif c == "4":
            clear(); run_cmd("offline"); pause()


def sub_learn():
    while True:
        header()
        print(f"  {GR}{B}┌─ LEARN{R}")
        print(f"  {GY}│{R} {GR}{B}[ 1]{R}  {WH}EXTRACT{R}  {D}استخراج{R}")
        print(f"  {GY}│{R} {GR}{B}[ 2]{R}  {WH}STATS{R}    {D}آمار{R}")
        print(f"  {GY}│{R} {GR}{B}[ 3]{R}  {WH}PATH{R}     {D}مسیر{R}")
        print(f"  {GY}│{R} {GR}{B}[ 4]{R}  {WH}GOALS{R}    {D}اهداف{R}")
        print(f"  {GY}│{R} {RD}{B}[ 0]{R}  {WH}BACK{R}")
        print(f"  {GY}└─────────────────────────────────────────────────{R}")
        print()
        c = ask("انتخاب")
        if c in (None, "0"): return
        if c == "1": clear(); run_py("learn.py", "extract"); pause()
        elif c == "2": clear(); run_py("learn.py", "stats"); pause()
        elif c == "3":
            t = ask("موضوع", "graphics")
            clear(); run_py("learn.py", "path", t); pause()
        elif c == "4":
            g = ask("هدف", "backend")
            clear(); run_cmd("goal", g); pause()


def sub_evolve():
    while True:
        header()
        print(f"  {PK}{B}┌─ EVOLVE{R}")
        print(f"  {GY}│{R} {PK}{B}[ 1]{R}  {WH}AGENTS{R}      {D}۴ ایجنت{R}")
        print(f"  {GY}│{R} {PK}{B}[ 2]{R}  {WH}META{R}        {D}خودبازنویس{R}")
        print(f"  {GY}│{R} {PK}{B}[ 3]{R}  {WH}METADATA{R}    {D}فراداده{R}")
        print(f"  {GY}│{R} {PK}{B}[ 4]{R}  {WH}CAPABILITY{R}  {D}توانایی{R}")
        print(f"  {GY}│{R} {PU}{B}[ 5]{R}  {WH}ANALYZE{R}     {D}تحلیل پروژه{R}")
        print(f"  {GY}│{R} {OR}{B}[ 6]{R}  {WH}SNAPSHOT{R}    {D}پشتیبان{R}")
        print(f"  {GY}│{R} {PU}{B}[ 8]{R}  {WH}DEPS{R}        {D}گراف وابستگی{R}")
        print(f"  {GY}│{R} {PU}{B}[ 9]{R}  {WH}ORACLE{R}      {D}PageRank · Community{R}")
        print(f"  {GY}│{R} {PU}{B}[10]{R}  {WH}ANALYTICS{R}   {D}Betweenness · Cycle{R}")
        print(f"  {GY}│{R} {PU}{B}[11]{R}  {WH}ADVANCED{R}    {D}Influence · Predict{R}")
        print(f"  {GY}│{R} {RD}{B}[ 0]{R}  {WH}BACK{R}")
        print(f"  {GY}└─────────────────────────────────────────────────{R}")
        print()
        c = ask("انتخاب")
        if c in (None, "0"): return
        elif c == "1": clear(); run_cmd("agents"); pause()
        elif c == "2": clear(); run_py("feature_meta.py", "cycle"); pause()
        elif c == "3": clear(); run_py("feature_metadata.py", "extract"); pause()
        elif c == "4": clear(); run_py("feature_capability.py"); pause()
        elif c == "5":
            clear()
            run_py("-c", """
import sys
sys.path.insert(0, ".")
import feature_meta
p = feature_meta.analyze_project()
print(f"Files: {len(p['files'])}")
print(f"Lines: {p['total_lines']:,}")
for o in p.get("opportunities", []):
    print(f"  - {o['type']}: {o['detail']}")
""")
            pause()
        elif c == "6": clear(); run_py("feature_snapshot.py", "build"); pause()
        elif c == "8":
            print()
            print("  [1] build  [2] stats  [3] requires  [4] breaks")
            sub = ask("انتخاب", "2")
            if sub == "1":
                clear(); run_py("feature_deps.py", "build", "--limit=100"); pause()
            elif sub == "2":
                clear(); run_py("feature_deps.py", "stats"); pause()
            elif sub == "3":
                p = ask("پکیج")
                if p:
                    clear(); run_py("feature_deps.py", "requires", p); pause()
            elif sub == "4":
                p = ask("پکیج")
                if p:
                    clear(); run_py("feature_deps.py", "breaks", p); pause()
        elif c == "9":
            print()
            print("  [1] rank   [2] order   [3] community")
            print("  [4] path   [5] anomaly [6] stats")
            sub = ask("انتخاب", "1")
            if sub == "1":
                clear(); run_py("feature_oracle.py", "rank"); pause()
            elif sub == "2":
                p = ask("پکیج‌ها")
                if p:
                    pkgs = [x.strip() for x in p.split(",") if x.strip()]
                    clear(); run_py("feature_oracle.py", "order", *pkgs); pause()
            elif sub == "3":
                clear(); run_py("feature_oracle.py", "community"); pause()
            elif sub == "4":
                a = ask("از"); b = ask("به")
                if a and b:
                    clear(); run_py("feature_oracle.py", "path", a, b); pause()
            elif sub == "5":
                clear(); run_py("feature_oracle.py", "anomaly"); pause()
            elif sub == "6":
                clear(); run_py("feature_oracle.py", "stats"); pause()
        elif c == "10":
            print()
            print("  [1] betweenness [2] kcore [3] cycles [4] simrank")
            sub = ask("انتخاب", "3")
            if sub == "1":
                clear(); run_py("feature_analytics.py", "betweenness"); pause()
            elif sub == "2":
                clear(); run_py("feature_analytics.py", "kcore"); pause()
            elif sub == "3":
                clear(); run_py("feature_analytics.py", "cycles"); pause()
            elif sub == "4":
                p = ask("پکیج")
                if p:
                    clear(); run_py("feature_analytics.py", "simrank", p); pause()
        elif c == "11":
            print()
            print("  [1] influence [2] spread [3] community")
            print("  [4] predict   [5] predict-all")
            sub = ask("انتخاب", "1")
            if sub == "1":
                k = ask("تعداد seed", "5")
                clear(); run_py("feature_advanced.py", "influence", str(k)); pause()
            elif sub == "2":
                p = ask("پکیج")
                if p:
                    clear(); run_py("feature_advanced.py", "spread", p); pause()
            elif sub == "3":
                clear(); run_py("feature_advanced.py", "community"); pause()
            elif sub == "4":
                m = ask("روش", "adamic_adar")
                clear(); run_py("feature_advanced.py", "predict", m); pause()
            elif sub == "5":
                clear(); run_py("feature_advanced.py", "predict-all"); pause()


def autopilot():
    clear()
    s1 = stats()
    print()
    print(f"  {PU}{B}◆ AUTOPILOT{R}")
    print()
    plan = []
    if s1["src"] < 400: plan.append(("enrich 50", ["enrich", "50"]))
    if s1["tech"] < 200: plan.append(("extract", "py:learn.py:extract"))
    plan.append(("rebuild", ["rebuild"]))
    plan.append(("meta", "py:feature_meta.py:cycle"))
    plan.append(("snapshot", "py:feature_snapshot.py:build"))
    for i, (n, _) in enumerate(plan, 1):
        print(f"    {i}. {n}")
    print()
    pause("Enter")
    for i, (name, action) in enumerate(plan, 1):
        print(f"\n  [{i}/{len(plan)}] {name}")
        if isinstance(action, list):
            run_cmd(*action)
        elif action.startswith("py:"):
            parts = action.split(":")
            run_py(parts[1], *parts[2:])
        print(f"  {GR}✓{R}")
    s2 = stats()
    print()
    print(f"  src {s1['src']} → {s2['src']}  ({s2['src']-s1['src']:+d})")
    print(f"  tech {s1['tech']} → {s2['tech']}  ({s2['tech']-s1['tech']:+d})")
    pause()


def smart():
    clear()
    print()
    print(f"  {GR}{B}★ SMART MODE{R}")
    print()
    text = ask("چی می‌خواهی؟")
    if not text: return
    p = text.split()
    f = p[0].lower()
    if f in ("search", "s", "جستجو"):
        q = " ".join(p[1:]) or ask("جستجو")
        if q: clear(); run_cmd("search", q); pause()
    elif f in ("ask", "a", "بپرس"):
        q = " ".join(p[1:]) or ask("سؤال")
        if q: clear(); run_cmd("ask", q); pause()
    elif f in ("run", "چرخه"):
        n = p[1] if len(p) > 1 else "2"
        clear(); run_cmd("reset-health"); run_cmd("run", n); run_cmd("rebuild"); pause()
    elif f in ("extract", "استخراج"):
        clear(); run_py("learn.py", "extract"); pause()
    elif f in ("stats", "آمار"):
        clear(); run_cmd("stats"); pause()
    else:
        clear(); run_cmd("search", text); pause()


def main():
    while True:
        try:
            c = main_menu()
            if c is None or c.strip().lower() in ("q", "exit", "0", "خروج"):
                clear()
                print(f"\n  {CY}Bedrood 👋{R}\n")
                return
            c = c.strip().lower()
            if c in ("a", "auto", "خودکار"): autopilot()
            elif c in ("s", "smart", "هوش"): smart()
            elif c == "1": sub_ask()
            elif c == "2": sub_get()
            elif c == "3": sub_learn()
            elif c == "4": sub_evolve()
            elif c in ("5", "13", "14", "15", "23"):
                clear(); run_py("feature_snapshot.py", "build"); pause()
            elif c == "7":
                clear(); run_cmd("top", "25"); pause()
            elif c == "18":
                clear(); run_py("feature_cleanup.py", "report"); pause()
            else:
                clear(); run_cmd("search", c); pause()
        except KeyboardInterrupt:
            print(); continue
        except Exception as e:
            print(f"\n  {RD}خطا: {e}{R}\n"); pause()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        clear()
        print("\nBye\n")
