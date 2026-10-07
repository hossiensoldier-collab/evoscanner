#!/usr/bin/env python3
"""EvoScanner Panel v7 — بازنویسی کامل"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

BASE = Path.home() / "evoscanner"
os.chdir(str(BASE))

# ═══════════════════════════════════════════════════
#  رنگ‌ها
# ═══════════════════════════════════════════════════

R = "\033[0m"           # reset
B = "\033[1m"           # bold
D = "\033[2m"           # dim
I = "\033[3m"           # italic

# رنگ‌های 24bit سایبرپانک آرام
BK = "\033[38;2;15;17;23m"       # back-ish
CY = "\033[38;2;100;220;230m"    # cyan
PU = "\033[38;2;180;140;255m"    # purple
PK = "\033[38;2;255;140;200m"    # pink
YL = "\033[38;2;255;215;80m"     # yellow
GR = "\033[38;2;120;230;150m"    # green
RD = "\033[38;2;255;110;110m"    # red
BL = "\033[38;2;120;170;255m"    # blue
OR = "\033[38;2;255;160;80m"     # orange
WH = "\033[38;2;230;230;240m"    # white
GY = "\033[38;2;130;135;150m"    # gray


def clear():
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def ask(prompt, default=""):
    try:
        p = f"{CY}{B}❯{R} {WH}{prompt}{R}"
        if default:
            p += f" {D}[{default}]{R}"
        p += f"{CY} : {R}"
        s = input(p).strip()
        return s if s else default
    except (EOFError, KeyboardInterrupt):
        print()
        return None


def pause(msg="Enter"):
    try:
        input(f"\n  {D}{msg}...{R}")
    except (EOFError, KeyboardInterrupt):
        print()


def get_stats():
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


# ═══════════════════════════════════════════════════
#  Header
# ═══════════════════════════════════════════════════

def header():
    clear()
    s = get_stats()

    print()
    print(f"  {CY}──────────────────────────────────────────────────{R}")
    print(f"  {PU}{B}◆{R} {WH}{B}E V O S C A N N E R{R}  {GY}v7.0{R}")
    print(f"  {PU}◆{R} {D}Self-Evolving Knowledge System{R}")
    print(f"  {CY}──────────────────────────────────────────────────{R}")
    print()

    print(f"  {GY}src{R} {YL}{s['src']:>4}{R}   "
          f"{GY}graph{R} {CY}{s['graph']:>4}{R}   "
          f"{GY}tech{R} {GR}{s['tech']:>4}{R}   "
          f"{GY}snip{R} {GR}{s['snip']:>4}{R}")
    print()


def next_hints():
    s = get_stats()
    hints = []

    if s["src"] < 300:
        hints.append(("GET", "2·1", "chرخه منابع"))
    if s["tech"] < 100:
        hints.append(("LEARN", "3·1", "extract"))
    if s["graph"] < 600:
        hints.append(("GET", "2·3", "rebuild"))

    try:
        snaps = list((BASE / "snapshots").glob("snapshot_*.md"))
        if not snaps:
            hints.append(("EVOLVE", "4·5", "snapshot"))
    except Exception:
        pass

    if not hints:
        hints.append(("AUTO", "a", "اجرای خودکار"))
        hints.append(("SMART", "s", "تایپ آزاد"))

    print(f"  {PU}{B}▸ NEXT{R}")
    for tag, key, desc in hints[:3]:
        col = {"GET": YL, "LEARN": GR, "EVOLVE": PK,
               "AUTO": PU, "SMART": CY}.get(tag, GY)
        print(f"    {col}{tag:6s}{R} {WH}{key:8s}{R} {D}{desc}{R}")
    print()


# ═══════════════════════════════════════════════════
#  Menu
# ═══════════════════════════════════════════════════

def mi(num, title, sub, color=CY):
    n = str(num) if num != 0 else "0"
    print(f"  {GY}│{R} {color}{B}[{n:>2}]{R}  "
          f"{WH}{B}{title:<14s}{R} {D}{sub}{R}")


def group(text):
    print(f"  {PU}{B}┌─ {text}{R}")


def end_group():
    print(f"  {GY}│{R}")


def menu():
    header()
    next_hints()

    group("KAR")
    mi(1, "ASK", "سؤال · جستجو · مشاور", CY)
    mi(2, "GET", "جذب منابع · چرخه", YL)
    mi(7, "GRAPH", "کاوش گراف", BL)
    end_group()

    group("DANESH")
    mi(3, "LEARN", "یادگیری · مسیر", GR)
    mi(12, "SOURCES", "منابع گسترده", GR)
    mi(17, "IDEAS", "پیشنهاد پروژه", GR)
    end_group()

    group("SYSTEM")
    mi(4, "EVOLVE", "خودارتقایی · AI", PK)
    mi(5, "DATA", "خروجی · snapshot", OR)
    mi(6, "SERVERS", "API · وب", BL)
    mi(18, "CLEANUP", "پاک‌سازی", RD)
    end_group()

    group("INTEGRATION")
    mi(13, "TOKEN", "GitHub", OR)
    mi(14, "AI-AGENT", "LLM خودکار", PK)
    mi(15, "AI-BRIDGE", "پرامپت برای AI", PK)
    mi(23, "SNAPSHOT", "export برای AI", OR)
    end_group()

    print(f"  {PU}{B}└─────────────────────────────────────────────────{R}")
    print()
    print(f"  {PU}{B}◆ AUTO{R}  {D}خودش تصمیم می‌گیرد{R}")
    print(f"  {GR}{B}★ SMART{R} {D}تایپ آزاد{R}")
    print(f"  {RD}{B}✕ EXIT{R}  {D}خروج{R}")
    print()

    return ask("انتخاب")


# ═══════════════════════════════════════════════════
#  Submenus
# ═══════════════════════════════════════════════════

def sub_header(title, color=CY):
    header()
    print(f"  {color}{B}┌─ {title}{R}")
    print(f"  {GY}│{R}")


def sub_end():
    print(f"  {PU}{B}└─────────────────────────────────────────────────{R}")
    print()


def run_cmd(*args):
    try:
        subprocess.run([sys.executable, "evoscanner_v2.py"] + list(args),
                       cwd=str(BASE))
    except KeyboardInterrupt:
        pass


def run_py(script, *args):
    try:
        subprocess.run([sys.executable, script] + list(args),
                       cwd=str(BASE))
    except KeyboardInterrupt:
        pass


def sub_ask():
    while True:
        sub_header("ASK · سؤال و جستجو", CY)
        mi(1, "SEARCH", "جستجو", CY)
        mi(2, "ASK", "پرسش RAG", CY)
        mi(3, "RELATED", "پکیج مرتبط", CY)
        mi(4, "PATH", "مسیر گراف", BL)
        mi(5, "ADVISOR", "مشاور پکیج", GR)
        mi(6, "IDEAS", "پیشنهاد پروژه", GR)
        mi(7, "COMPARE", "مقایسه دو پکیج", CY)
        mi(8, "RAG2", "چندمرحله‌ای", PK)
        mi(0, "BACK", "", RD)
        sub_end()
        c = ask("انتخاب")
        if c in (None, "0"): return
        if c == "1":
            q = ask("جستجو")
            if q: run_cmd("search", q); pause()
        elif c == "2":
            q = ask("سؤال")
            if q: run_cmd("ask", q); pause()
        elif c == "3":
            p = ask("پکیج")
            if p: run_cmd("related", p); pause()
        elif c == "4":
            a = ask("از"); b = ask("به")
            if a and b: run_cmd("graph-path", a, b); pause()
        elif c == "5":
            print(f"\n  {D}کارها: web framework, async, testing...{R}")
            t = ask("کار", "web framework")
            if t:
                print()
                run_py("-c", f"""
import sys
sys.path.insert(0, "features")
from evoscanner_v2 import KB
import advisor
advisor.advise(KB(), {t!r})
""")
                pause()
        elif c == "6":
            run_py("-c", '''
import sys
sys.path.insert(0, "features")
from evoscanner_v2 import KB
import project_ideas
project_ideas.show(KB(), n=5)
''')
            pause()
        elif c == "7":
            a = ask("پکیج 1"); b = ask("پکیج 2")
            if a and b:
                print()
                run_py("-c", f"""
import sys
sys.path.insert(0, "features")
from evoscanner_v2 import KB
import compare
compare.compare(KB(), {a!r}, {b!r})
""")
                pause()
        elif c == "8":
            q = ask("سؤال")
            if q: run_py("feature_rag_v2.py", q); pause()


def sub_get():
    while True:
        sub_header("GET · جذب منابع", YL)
        mi(1, "RUN", "چرخه کشف", YL)
        mi(2, "ENRICH", "README", YL)
        mi(3, "REBUILD", "گراف", CY)
        mi(4, "HUNTER", "کوئری هوشمند", YL)
        mi(5, "SOURCES", "منابع جدید", GR)
        mi(6, "TOKEN", "GitHub", OR)
        mi(7, "AUTO-5", "۵ چرخه", YL)
        mi(8, "BULK-10", "۱۰ چرخه", YL)
        mi(0, "BACK", "", RD)
        sub_end()
        c = ask("انتخاب")
        if c in (None, "0"): return
        if c == "1":
            n = ask("تعداد", "2")
            run_cmd("reset-health"); run_cmd("run", n); run_cmd("rebuild")
            pause()
        elif c == "2":
            n = ask("تعداد", "50")
            run_cmd("enrich", n); run_cmd("rebuild")
            pause()
        elif c == "3":
            run_cmd("rebuild"); pause()
        elif c == "4":
            run_cmd("learn"); pause()
        elif c == "5":
            run_cmd("offline"); pause()
        elif c == "6":
            run_py("auth.py", "status"); pause()
        elif c == "7":
            print()
            for i in range(5):
                print(f"  {CY}▶ cycle {i+1}/5{R}")
                run_cmd("run", "1")
                if i < 4:
                    print(f"  {D}wait 30s...{R}")
                    time.sleep(30)
            run_cmd("rebuild"); pause()
        elif c == "8":
            print()
            for i in range(10):
                print(f"  {CY}▶ cycle {i+1}/10{R}")
                run_cmd("run", "1")
                if i < 9:
                    print(f"  {D}wait 20s...{R}")
                    time.sleep(20)
            run_cmd("rebuild"); pause()


def sub_learn():
    while True:
        sub_header("LEARN · یادگیری", GR)
        mi(1, "EXTRACT", "استخراج دانش", GR)
        mi(2, "STATS", "آمار", GR)
        mi(3, "PATH", "مسیر ۴ سطحی", GR)
        mi(4, "GOALS", "اهداف آماده", GR)
        mi(5, "TECH", "تکنیک‌ها", GR)
        mi(6, "SNIPPETS", "قطعات کد", GR)
        mi(7, "GRAPHICS", "گرافیک", GR)
        mi(0, "BACK", "", RD)
        sub_end()
        c = ask("انتخاب")
        if c in (None, "0"): return
        if c == "1": run_py("learn.py", "extract"); pause()
        elif c == "2": run_py("learn.py", "stats"); pause()
        elif c == "3":
            t = ask("موضوع", "graphics")
            run_py("learn.py", "path", t); pause()
        elif c == "4":
            print(f"\n  {D}backend | ml | data | devops | security{R}")
            g = ask("هدف", "backend")
            run_cmd("goal", g); pause()
        elif c == "5": run_py("learn.py", "tech"); pause()
        elif c == "6": run_py("learn.py", "snippet"); pause()
        elif c == "7": run_py("learn.py", "graphics"); pause()


def sub_evolve():
    while True:
        sub_header("EVOLVE · خودارتقایی", PK)
        mi(1, "AGENTS", "۴ ایجنت", PK)
        mi(2, "META", "خودبازنویس", PK)
        mi(3, "CHAIN", "زنجیره ایجنت", PK)
        mi(4, "METADATA", "فراداده", PK)
        mi(5, "RAG2", "چندمرحله‌ای", PK)
        mi(6, "CAPABILITY", "توانایی دستگاه", PU)
        mi(7, "ANALYZE", "تحلیل پروژه", PU)
        mi(8, "SNAPSHOT", "پشتیبان برای AI", OR)
        mi(9, "AI-AGENT", "LLM داخل", PK)
        mi(0, "BACK", "", RD)
        sub_end()
        c = ask("انتخاب")
        if c in (None, "0"): return
        if c == "1":
            run_cmd("agents"); run_cmd("agents-report"); pause()
        elif c == "2":
            run_py("feature_meta.py", "cycle"); pause()
        elif c == "3":
            run_py("feature_agent_chain.py", "run"); pause()
        elif c == "4":
            run_py("feature_metadata.py", "extract"); pause()
        elif c == "5":
            q = ask("سؤال")
            if q: run_py("feature_rag_v2.py", q); pause()
        elif c == "6":
            run_py("feature_capability.py"); pause()
        elif c == "7":
            run_py("-c", '''
import sys
sys.path.insert(0, ".")
import feature_meta
p = feature_meta.analyze_project()
print(f"\\n  Files: {len(p['files'])}")
print(f"  Lines: {p['total_lines']:,}")
print(f"  Issues: {len(p['issues'])}")
print(f"\\n  Opportunities:")
for o in p.get("opportunities", []):
    print(f"    • {o['type']}: {o['detail']}")
''')
            pause()
        elif c == "8":
            run_py("feature_snapshot.py", "build"); pause()
        elif c == "9":
            print(f"\n  {D}از منوی اصلی [14] تنظیم کن{R}")
            pause()


def sub_manage():
    while True:
        sub_header("MANAGE · مدیریت", BL)
        mi(1, "WEB", "رابط وب", BL)
        mi(2, "API", "سرور API", BL)
        mi(3, "GRAPH-WEB", "نمای گراف SVG", BL)
        mi(4, "EXPORT", "JSON/CSV/MD", OR)
        mi(5, "STATS", "آمار کامل", CY)
        mi(6, "CLEANUP", "گزارش سلامت", RD)
        mi(7, "NETWORK", "تست شبکه", BL)
        mi(0, "BACK", "", RD)
        sub_end()
        c = ask("انتخاب")
        if c in (None, "0"): return
        if c == "1": run_cmd("web"); pause()
        elif c == "2":
            print(f"\n  {D}API روی http://localhost:8081{R}")
            subprocess.run([sys.executable, "api.py"], cwd=str(BASE))
        elif c == "3": run_cmd("graphweb"); pause()
        elif c == "4": run_cmd("export"); pause()
        elif c == "5": run_cmd("stats"); pause()
        elif c == "6": run_py("feature_cleanup.py", "report"); pause()
        elif c == "7": run_py("feature_net.py", "report"); pause()


def sub_graph():
    while True:
        sub_header("GRAPH · کاوش گراف", BL)
        mi(1, "TOP", "۲۵ نود برتر", BL)
        mi(2, "RELATED", "مرتبط‌ها", CY)
        mi(3, "PEERS", "هم‌دسته", CY)
        mi(4, "NEIGHBORS", "همسایه‌ها", CY)
        mi(5, "PATH", "کوتاه‌ترین مسیر", BL)
        mi(6, "CAT", "فیلتر دسته", CY)
        mi(0, "BACK", "", RD)
        sub_end()
        c = ask("انتخاب")
        if c in (None, "0"): return
        if c == "1": run_cmd("top", "25"); pause()
        elif c == "2":
            p = ask("پکیج")
            if p: run_cmd("graph-related", p); pause()
        elif c == "3":
            p = ask("پکیج")
            if p: run_cmd("graph-peers", p); pause()
        elif c == "4":
            p = ask("نود")
            if p: run_cmd("graph-neighbors", p); pause()
        elif c == "5":
            a = ask("از"); b = ask("به")
            if a and b: run_cmd("graph-path", a, b); pause()
        elif c == "6":
            cat = ask("دسته")
            if cat: run_cmd("cat", cat); pause()


# ═══════════════════════════════════════════════════
#  AUTOPILOT
# ═══════════════════════════════════════════════════

def autopilot():
    clear()
    s1 = get_stats()

    print()
    print(f"  {PU}{B}◆ AUTOPILOT{R}")
    print(f"  {D}خودش تصمیم می‌گیرد چه کار کند{R}")
    print()
    print(f"  {GY}وضعیت:{R} src {YL}{s1['src']}{R} · "
          f"graph {CY}{s1['graph']}{R} · "
          f"tech {GR}{s1['tech']}{R} · "
          f"snip {GR}{s1['snip']}{R}")
    print()

    # تصمیم
    plan = []
    if s1["src"] < 400:
        plan.append(("enrich 50", ["enrich", "50"]))
    if s1["tech"] < 200:
        plan.append(("extract", "py:learn.py:extract"))
    plan.append(("rebuild", ["rebuild"]))
    plan.append(("meta cycle", "py:feature_meta.py:cycle"))
    if s1["graph"] < 700:
        plan.append(("run 2", ["run", "2"]))
    plan.append(("snapshot", "py:feature_snapshot.py:build"))

    print(f"  {GY}برنامه:{R}")
    for i, (n, _) in enumerate(plan, 1):
        print(f"    {i}. {n}")
    print()
    pause("Enter برای شروع")

    for i, (name, action) in enumerate(plan, 1):
        print()
        print(f"  {PU}{B}[{i}/{len(plan)}]{R} {WH}{name}{R}")
        print(f"  {D}{'─' * 44}{R}")
        if isinstance(action, list):
            run_cmd(*action)
        elif action.startswith("py:"):
            parts = action.split(":")
            run_py(parts[1], *parts[2:])
        print(f"  {GR}✓{R} تمام")

    s2 = get_stats()

    def diff(a, b):
        d = b - a
        col = GR if d > 0 else (RD if d < 0 else GY)
        sign = "+" if d > 0 else ""
        return f"{col}{sign}{d}{R}"

    print()
    print(f"  {CY}──────────────────────────────────────────────────{R}")
    print(f"  {GR}{B}✓ AUTOPILOT تمام{R}")
    print(f"  {CY}──────────────────────────────────────────────────{R}")
    print()
    print(f"    src   {s1['src']} → {YL}{s2['src']}{R}  ({diff(s1['src'], s2['src'])})")
    print(f"    graph {s1['graph']} → {CY}{s2['graph']}{R}  ({diff(s1['graph'], s2['graph'])})")
    print(f"    tech  {s1['tech']} → {GR}{s2['tech']}{R}  ({diff(s1['tech'], s2['tech'])})")
    print(f"    snip  {s1['snip']} → {GR}{s2['snip']}{R}  ({diff(s1['snip'], s2['snip'])})")
    print()
    pause()


# ═══════════════════════════════════════════════════
#  SMART
# ═══════════════════════════════════════════════════

def smart():
    header()
    print(f"  {GR}{B}★ SMART MODE{R}")
    print(f"  {D}هرچی می‌خواهی بگو — خودش می‌فهمد{R}")
    print()
    print(f"  {D}مثال:{R} search fastapi  |  graph django  |  اجرا 3{R}")
    print()

    text = ask("چی می‌خواهی؟")
    if not text:
        return

    p = text.split()
    f = p[0].lower()

    if f in ("search", "s", "جستجو", "سرچ", "بگرد"):
        q = " ".join(p[1:]) or ask("جستجو")
        if q: run_cmd("search", q)

    elif f in ("ask", "a", "بپرس", "سوال", "سؤال", "پرسش"):
        q = " ".join(p[1:]) or ask("سؤال")
        if q: run_cmd("ask", q)

    elif f in ("related", "r", "مرتبط"):
        x = " ".join(p[1:]) or ask("پکیج")
        if x: run_cmd("related", x)

    elif f in ("graph", "g", "گراف"):
        x = " ".join(p[1:]) or ask("موجودیت")
        if x: run_cmd("graph-related", x)

    elif f in ("run", "cycle", "چرخه", "اجرا"):
        n = p[1] if len(p) > 1 else "2"
        run_cmd("reset-health"); run_cmd("run", n); run_cmd("rebuild")

    elif f in ("extract", "استخراج", "یاد"):
        run_py("learn.py", "extract")

    elif f in ("stats", "آمار"):
        run_cmd("stats")

    elif f in ("snapshot", "پشتیبان"):
        run_py("feature_snapshot.py", "build")

    elif f in ("capability", "توان"):
        run_py("feature_capability.py")

    elif f in ("meta", "متا"):
        run_py("feature_meta.py", "cycle")

    elif f in ("agents", "ایجنت"):
        run_cmd("agents")

    elif f in ("help", "h", "راهنما", "?"):
        show_help()
        return

    else:
        print(f"\n  {D}جستجو می‌کنم...{R}\n")
        run_cmd("search", text)

    pause()


def show_help():
    header()
    print(f"  {PU}{B}◆ HELP{R}")
    print()
    print(f"  {PU}{B}◆ AUTO{R}    اجرای خودکار — {D}کلید a{R}")
    print(f"  {GR}{B}★ SMART{R}   تایپ آزاد  — {D}کلید s{R}")
    print()
    print(f"  {CY}SMART MODE{R} — مثال‌ها:")
    print(f"    search fastapi")
    print(f"    graph asyncio")
    print(f"    اجرا 3")
    print(f"    مشاور پکیج")
    print(f"    متا")
    print(f"    پشتیبان")
    print()
    print(f"  {D}عدد 1-24 → زیرمنو{R}")
    print(f"  {D}q → خروج{R}")
    print()
    pause()


# ═══════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════

def main():
    while True:
        try:
            c = menu()
            if c is None or c.lower() in ("q", "quit", "exit", "0", "خروج"):
                clear()
                print(f"\n  {CY}Bedrood 👋{R}\n")
                return

            c = c.strip().lower()

            if c in ("a", "auto", "اتو", "autopilot", "خودکار"):
                autopilot()
            elif c in ("s", "smart", "هوش", "★"):
                smart()
            elif c in ("h", "help", "راهنما", "?"):
                show_help()
            elif c == "1": sub_ask()
            elif c == "2": sub_get()
            elif c == "3": sub_learn()
            elif c == "4": sub_evolve()
            elif c in ("5", "6"): sub_manage()
            elif c == "7": sub_graph()
            elif c in ("8", "9", "10", "11", "12", "13",
                       "14", "15", "16", "17", "18",
                       "19", "20", "21", "22", "23", "24"):
                # بفرست به زیرمنوی مرتبط
                m = {"13": "6", "14": "6", "15": "6",
                     "16": "1", "17": "1", "18": "6",
                     "19": "6", "20": "6", "21": "6",
                     "22": "6", "23": "4", "24": "help"}
                k = m.get(c, "1")
                if k == "help":
                    show_help()
                else:
                    {"1": sub_ask, "4": sub_evolve,
                     "6": sub_manage}[k]()
            else:
                # پیش‌فرض: جستجو
                run_cmd("search", c)
                pause()

        except KeyboardInterrupt:
            print()
            continue
        except Exception as e:
            print(f"\n  {RD}خطا: {e}{R}\n")
            pause()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        clear()
        print("\nBye\n")

