#!/usr/bin/env python3
"""EvoScanner Panel v8 — تمیز و بدون تکرار header"""
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


# ═══════════════════════════════════════════════════
#  نمایش
# ═══════════════════════════════════════════════════

def show_header():
    s = stats()
    print()
    print(f"  {CY}──────────────────────────────────────────────────{R}")
    print(f"  {PU}{B}◆{R} {WH}{B}E V O S C A N N E R{R}  {GY}v8.0{R}")
    print(f"  {CY}──────────────────────────────────────────────────{R}")
    print()
    print(f"  {GY}src{R} {YL}{s['src']:>4}{R}   "
          f"{GY}graph{R} {CY}{s['graph']:>4}{R}   "
          f"{GY}tech{R} {GR}{s['tech']:>4}{R}   "
          f"{GY}snip{R} {GR}{s['snip']:>4}{R}")
    print()


def show_next():
    s = stats()
    hints = []
    if s["src"] < 400:
        hints.append(("GET", "2·2", "enrich README"))
    if s["tech"] < 200:
        hints.append(("LEARN", "3·1", "extract"))
    if s["graph"] < 700:
        hints.append(("GET", "2·3", "rebuild"))
    try:
        snaps = list((BASE / "snapshots").glob("snapshot_*.md"))
        if not snaps:
            hints.append(("EVOLVE", "4·8", "snapshot"))
    except Exception:
        pass
    if not hints:
        hints.append(("AUTO", "a", "خودکار"))
        hints.append(("SMART", "s", "تایپ آزاد"))

    print(f"  {PU}{B}▸ NEXT{R}")
    for tag, key, desc in hints[:3]:
        col = {"GET": YL, "LEARN": GR, "EVOLVE": PK,
               "AUTO": PU, "SMART": CY}.get(tag, GY)
        print(f"    {col}{tag:6s}{R} {WH}{key:8s}{R} {D}{desc}{R}")
    print()


def show_menu():
    show_header()
    show_next()

    print(f"  {PU}{B}╭─ KAR{R}")
    print(f"  {GY}│{R} {CY}{B}[ 1]{R}  {WH}ASK{R}      {D}سؤال · جستجو · مشاور{R}")
    print(f"  {GY}│{R} {YL}{B}[ 2]{R}  {WH}GET{R}      {D}جذب منابع · چرخه{R}")
    print(f"  {GY}│{R} {BL}{B}[ 7]{R}  {WH}GRAPH{R}    {D}کاوش گراف{R}")
    print(f"  {GY}│{R}")
    print(f"  {PU}{B}╭─ DANESH{R}")
    print(f"  {GY}│{R} {GR}{B}[ 3]{R}  {WH}LEARN{R}    {D}یادگیری · مسیر{R}")
    print(f"  {GY}│{R} {GR}{B}[12]{R}  {WH}SOURCES{R}  {D}منابع گسترده{R}")
    print(f"  {GY}│{R} {GR}{B}[17]{R}  {WH}IDEAS{R}    {D}پیشنهاد پروژه{R}")
    print(f"  {GY}│{R}")
    print(f"  {PU}{B}╭─ SYSTEM{R}")
    print(f"  {GY}│{R} {PK}{B}[ 4]{R}  {WH}EVOLVE{R}   {D}خودارتقایی · AI{R}")
    print(f"  {GY}│{R} {OR}{B}[ 5]{R}  {WH}DATA{R}     {D}خروجی · snapshot{R}")
    print(f"  {GY}│{R} {BL}{B}[ 6]{R}  {WH}SERVERS{R}  {D}API · وب{R}")
    print(f"  {GY}│{R} {RD}{B}[18]{R}  {WH}CLEANUP{R}  {D}پاک‌سازی{R}")
    print(f"  {GY}│{R}")
    print(f"  {PU}{B}╭─ INTEGRATION{R}")
    print(f"  {GY}│{R} {OR}{B}[13]{R}  {WH}TOKEN{R}    {D}GitHub{R}")
    print(f"  {GY}│{R} {PK}{B}[14]{R}  {WH}AI-AGENT{R} {D}LLM خودکار{R}")
    print(f"  {GY}│{R} {PK}{B}[15]{R}  {WH}AI-BRIDGE{R}{D}پرامپت{R}")
    print(f"  {GY}│{R} {OR}{B}[23]{R}  {WH}SNAPSHOT{R} {D}export{R}")
    print(f"  {GY}╰─────────────────────────────────────────────────{R}")
    print()
    print(f"  {PU}{B}◆ AUTO{R}   {D}خودش تصمیم می‌گیرد{R}")
    print(f"  {GR}{B}★ SMART{R}  {D}تایپ آزاد{R}")
    print(f"  {RD}{B}✕ EXIT{R}   {D}خروج{R}")
    print()


# ═══════════════════════════════════════════════════
#  زیرمنوها
# ═══════════════════════════════════════════════════

def sub(title, color, items):
    """زیرمنوی عمومی"""
    while True:
        show_header()
        print(f"  {color}{B}┌─ {title}{R}")
        for num, t, s in items:
            c = color if num != 0 else RD
            print(f"  {GY}│{R} {c}{B}[{num:>2}]{R}  "
                  f"{WH}{B}{t:<14s}{R} {D}{s}{R}")
        print(f"  {GY}└─────────────────────────────────────────────────{R}")
        print()
        c = ask("انتخاب")
        if c is None:
            return
        return c  # برمی‌گرداند تا حلقه اصلی تصمیم بگیرد


def sub_ask():
    while True:
        show_header()
        print(f"  {CY}{B}┌─ ASK{R}")
        print(f"  {GY}│{R} {CY}{B}[ 1]{R}  {WH}SEARCH{R}   {D}جستجو{R}")
        print(f"  {GY}│{R} {CY}{B}[ 2]{R}  {WH}ASK{R}      {D}پرسش RAG{R}")
        print(f"  {GY}│{R} {CY}{B}[ 3]{R}  {WH}RELATED{R}  {D}پکیج مرتبط{R}")
        print(f"  {GY}│{R} {BL}{B}[ 4]{R}  {WH}PATH{R}     {D}مسیر گراف{R}")
        print(f"  {GY}│{R} {GR}{B}[ 5]{R}  {WH}ADVISOR{R}  {D}مشاور پکیج{R}")
        print(f"  {GY}│{R} {GR}{B}[ 6]{R}  {WH}IDEAS{R}    {D}پیشنهاد پروژه{R}")
        print(f"  {GY}│{R} {CY}{B}[ 7]{R}  {WH}COMPARE{R}  {D}مقایسه دو پکیج{R}")
        print(f"  {GY}│{R} {PK}{B}[ 8]{R}  {WH}RAG2{R}     {D}چندمرحله‌ای{R}")
        print(f"  {GY}│{R} {RD}{B}[ 0]{R}  {WH}BACK{R}")
        print(f"  {GY}└─────────────────────────────────────────────────{R}")
        print()

        c = ask("انتخاب")
        if c in (None, "0"): return

        if c == "1":
            q = ask("جستجو")
            if q:
                clear()
                run_cmd("search", q)
                pause()
        elif c == "2":
            q = ask("سؤال")
            if q:
                clear()
                run_cmd("ask", q)
                pause()
        elif c == "3":
            p = ask("پکیج")
            if p:
                clear()
                run_cmd("related", p)
                pause()
        elif c == "4":
            a = ask("از"); b = ask("به")
            if a and b:
                clear()
                run_cmd("graph-path", a, b)
                pause()
        elif c == "5":
            t = ask("کار", "web framework")
            if t:
                clear()
                run_py("-c", f'''
import sys
sys.path.insert(0, "features")
from evoscanner_v2 import KB
import advisor
advisor.advise(KB(), {t!r})
''')
                pause()
        elif c == "6":
            clear()
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
                clear()
                run_py("-c", f'''
import sys
sys.path.insert(0, "features")
from evoscanner_v2 import KB
import compare
compare.compare(KB(), {a!r}, {b!r})
''')
                pause()
        elif c == "8":
            q = ask("سؤال")
            if q:
                clear()
                run_py("feature_rag_v2.py", q)
                pause()


def sub_get():
    while True:
        show_header()
        print(f"  {YL}{B}┌─ GET{R}")
        print(f"  {GY}│{R} {YL}{B}[ 1]{R}  {WH}RUN{R}       {D}چرخه کشف{R}")
        print(f"  {GY}│{R} {YL}{B}[ 2]{R}  {WH}ENRICH{R}    {D}README کامل{R}")
        print(f"  {GY}│{R} {CY}{B}[ 3]{R}  {WH}REBUILD{R}   {D}گراف{R}")
        print(f"  {GY}│{R} {YL}{B}[ 4]{R}  {WH}HUNTER{R}    {D}کوئری هوشمند{R}")
        print(f"  {GY}│{R} {GR}{B}[ 5]{R}  {WH}SOURCES{R}   {D}منابع جدید{R}")
        print(f"  {GY}│{R} {OR}{B}[ 6]{R}  {WH}TOKEN{R}     {D}GitHub{R}")
        print(f"  {GY}│{R} {RD}{B}[ 0]{R}  {WH}BACK{R}")
        print(f"  {GY}└─────────────────────────────────────────────────{R}")
        print()

        c = ask("انتخاب")
        if c in (None, "0"): return

        if c == "1":
            n = ask("تعداد", "2")
            clear()
            run_cmd("reset-health"); run_cmd("run", n); run_cmd("rebuild")
            pause()
        elif c == "2":
            n = ask("تعداد", "50")
            clear()
            run_cmd("enrich", n); run_cmd("rebuild")
            pause()
        elif c == "3":
            clear(); run_cmd("rebuild"); pause()
        elif c == "4":
            clear(); run_cmd("learn"); pause()
        elif c == "5":
            clear(); run_cmd("offline"); pause()
        elif c == "6":
            clear(); run_py("auth.py", "status"); pause()


def sub_learn():
    while True:
        show_header()
        print(f"  {GR}{B}┌─ LEARN{R}")
        print(f"  {GY}│{R} {GR}{B}[ 1]{R}  {WH}EXTRACT{R}   {D}استخراج دانش{R}")
        print(f"  {GY}│{R} {GR}{B}[ 2]{R}  {WH}STATS{R}     {D}آمار{R}")
        print(f"  {GY}│{R} {GR}{B}[ 3]{R}  {WH}PATH{R}      {D}مسیر ۴ سطحی{R}")
        print(f"  {GY}│{R} {GR}{B}[ 4]{R}  {WH}GOALS{R}     {D}اهداف{R}")
        print(f"  {GY}│{R} {GR}{B}[ 5]{R}  {WH}TECH{R}      {D}تکنیک‌ها{R}")
        print(f"  {GY}│{R} {GR}{B}[ 6]{R}  {WH}SNIPPETS{R}  {D}قطعات کد{R}")
        print(f"  {GY}│{R} {RD}{B}[ 0]{R}  {WH}BACK{R}")
        print(f"  {GY}└─────────────────────────────────────────────────{R}")
        print()

        c = ask("انتخاب")
        if c in (None, "0"): return

        if c == "1":
            clear(); run_py("learn.py", "extract"); pause()
        elif c == "2":
            clear(); run_py("learn.py", "stats"); pause()
        elif c == "3":
            t = ask("موضوع", "graphics")
            clear(); run_py("learn.py", "path", t); pause()
        elif c == "4":
            g = ask("هدف", "backend")
            clear(); run_cmd("goal", g); pause()
        elif c == "5":
            clear(); run_py("learn.py", "tech"); pause()
        elif c == "6":
            clear(); run_py("learn.py", "snippet"); pause()


def sub_evolve():
    while True:
        show_header()
        print(f"  {PK}{B}┌─ EVOLVE{R}")
        print(f"  {GY}│{R} {PK}{B}[ 1]{R}  {WH}AGENTS{R}      {D}۴ ایجنت{R}")
        print(f"  {GY}│{R} {PK}{B}[ 2]{R}  {WH}META{R}        {D}خودبازنویس{R}")
        print(f"  {GY}│{R} {PK}{B}[ 3]{R}  {WH}METADATA{R}    {D}فراداده{R}")
        print(f"  {GY}│{R} {PK}{B}[ 4]{R}  {WH}CAPABILITY{R}  {D}توانایی{R}")
        print(f"  {GY}│{R} {PU}{B}[ 5]{R}  {WH}ANALYZE{R}     {D}تحلیل پروژه{R}")
        print(f"  {GY}│{R} {OR}{B}[ 6]{R}  {WH}SNAPSHOT{R}    {D}پشتیبان برای AI{R}")
        print(f"  {GY}│{R} {RD}{B}[ 0]{R}  {WH}BACK{R}")
        print(f"  {GY}└─────────────────────────────────────────────────{R}")
        print()

        c = ask("انتخاب")
        if c in (None, "0"): return

        if c == "1":
            clear(); run_cmd("agents"); pause()
        elif c == "2":
            clear(); run_py("feature_meta.py", "cycle"); pause()
        elif c == "3":
            clear(); run_py("feature_metadata.py", "extract"); pause()
        elif c == "4":
            clear(); run_py("feature_capability.py"); pause()
        elif c == "5":
            clear()
            run_py("-c", '''
import sys
sys.path.insert(0, ".")
import feature_meta
p = feature_meta.analyze_project()
print(f"Files: {len(p['files'])}")
print(f"Lines: {p['total_lines']:,}")
print(f"Issues: {len(p['issues'])}")
print("Opportunities:")
for o in p.get("opportunities", []):
    print(f"  • {o['type']}: {o['detail']}")
''')
            pause()
        elif c == "6":
            clear(); run_py("feature_snapshot.py", "build"); pause()


def sub_manage():
    while True:
        show_header()
        print(f"  {BL}{B}┌─ MANAGE{R}")
        print(f"  {GY}│{R} {BL}{B}[ 1]{R}  {WH}WEB{R}       {D}رابط وب{R}")
        print(f"  {GY}│{R} {BL}{B}[ 2]{R}  {WH}API{R}       {D}سرور API{R}")
        print(f"  {GY}│{R} {OR}{B}[ 3]{R}  {WH}EXPORT{R}    {D}خروجی{R}")
        print(f"  {GY}│{R} {CY}{B}[ 4]{R}  {WH}STATS{R}     {D}آمار{R}")
        print(f"  {GY}│{R} {RD}{B}[ 5]{R}  {WH}CLEANUP{R}   {D}سلامت{R}")
        print(f"  {GY}│{R} {BL}{B}[ 6]{R}  {WH}NETWORK{R}   {D}شبکه{R}")
        print(f"  {GY}│{R} {RD}{B}[ 0]{R}  {WH}BACK{R}")
        print(f"  {GY}└─────────────────────────────────────────────────{R}")
        print()

        c = ask("انتخاب")
        if c in (None, "0"): return

        if c == "1":
            clear(); run_cmd("web"); pause()
        elif c == "2":
            clear()
            try: subprocess.run([sys.executable, "api.py"], cwd=str(BASE))
            except KeyboardInterrupt: pass
        elif c == "3":
            clear(); run_cmd("export"); pause()
        elif c == "4":
            clear(); run_cmd("stats"); pause()
        elif c == "5":
            clear(); run_py("feature_cleanup.py", "report"); pause()
        elif c == "6":
            clear(); run_py("feature_net.py", "report"); pause()


def autopilot():
    clear()
    s1 = stats()
    print()
    print(f"  {PU}{B}◆ AUTOPILOT{R}")
    print(f"  {D}خودش تصمیم می‌گیرد{R}")
    print()
    print(f"  src {YL}{s1['src']}{R}  graph {CY}{s1['graph']}{R}  "
          f"tech {GR}{s1['tech']}{R}  snip {GR}{s1['snip']}{R}")
    print()

    plan = []
    if s1["src"] < 400:
        plan.append(("enrich", ["enrich", "50"]))
    if s1["tech"] < 200:
        plan.append(("extract", "py:learn.py:extract"))
    plan.append(("rebuild", ["rebuild"]))
    plan.append(("meta", "py:feature_meta.py:cycle"))
    if s1["graph"] < 700:
        plan.append(("run 2", ["run", "2"]))
    plan.append(("snapshot", "py:feature_snapshot.py:build"))

    print(f"  {D}برنامه:{R}")
    for i, (n, _) in enumerate(plan, 1):
        print(f"    {i}. {n}")
    print()
    pause("Enter برای شروع")

    for i, (name, action) in enumerate(plan, 1):
        print()
        print(f"  {PU}[{i}/{len(plan)}]{R} {WH}{name}{R}")
        if isinstance(action, list):
            run_cmd(*action)
        elif action.startswith("py:"):
            parts = action.split(":")
            run_py(parts[1], *parts[2:])
        print(f"  {GR}✓{R}")

    s2 = stats()
    def df(a, b):
        d = b - a
        c = GR if d > 0 else (RD if d < 0 else GY)
        return f"{c}{d:+d}{R}"

    print()
    print(f"  {CY}──────────────────────────────────────────────────{R}")
    print(f"  {GR}{B}✓ تمام{R}")
    print(f"  {CY}──────────────────────────────────────────────────{R}")
    print()
    print(f"    src   {s1['src']} → {s2['src']}  ({df(s1['src'], s2['src'])})")
    print(f"    graph {s1['graph']} → {s2['graph']}  ({df(s1['graph'], s2['graph'])})")
    print(f"    tech  {s1['tech']} → {s2['tech']}  ({df(s1['tech'], s2['tech'])})")
    print(f"    snip  {s1['snip']} → {s2['snip']}  ({df(s1['snip'], s2['snip'])})")
    print()
    pause()


def smart():
    clear()
    print()
    print(f"  {GR}{B}★ SMART MODE{R}")
    print(f"  {D}هرچی بگو — خودش می‌فهمد{R}")
    print()
    print(f"  {D}مثال: search fastapi  |  graph django  |  اجرا 3{R}")
    print()

    text = ask("چی می‌خواهی؟")
    if not text:
        return

    p = text.split()
    f = p[0].lower()

    cmd = None
    args = []

    if f in ("search", "s", "جستجو", "سرچ", "بگرد"):
        q = " ".join(p[1:]) or ask("جستجو")
        if q: cmd, args = "search", [q]
    elif f in ("ask", "a", "بپرس", "سوال", "سؤال"):
        q = " ".join(p[1:]) or ask("سؤال")
        if q: cmd, args = "ask", [q]
    elif f in ("related", "r", "مرتبط"):
        x = " ".join(p[1:]) or ask("پکیج")
        if x: cmd, args = "related", [x]
    elif f in ("graph", "g", "گراف"):
        x = " ".join(p[1:]) or ask("موجودیت")
        if x: cmd, args = "graph-related", [x]
    elif f in ("run", "cycle", "چرخه", "اجرا"):
        n = p[1] if len(p) > 1 else "2"
        clear()
        run_cmd("reset-health"); run_cmd("run", n); run_cmd("rebuild")
        pause(); return
    elif f in ("stats", "آمار"):
        cmd, args = "stats", []
    elif f in ("extract", "استخراج"):
        clear(); run_py("learn.py", "extract"); pause(); return
    elif f in ("snapshot", "پشتیبان"):
        clear(); run_py("feature_snapshot.py", "build"); pause(); return
    elif f in ("meta", "متا"):
        clear(); run_py("feature_meta.py", "cycle"); pause(); return
    elif f in ("capability", "توان"):
        clear(); run_py("feature_capability.py"); pause(); return
    elif f in ("agents", "ایجنت"):
        clear(); run_cmd("agents"); pause(); return
    elif f in ("help", "h", "راهنما"):
        clear(); show_help(); return
    else:
        cmd, args = "search", [text]

    if cmd:
        clear()
        run_cmd(cmd, *args)
        pause()


def show_help():
    clear()
    print()
    print(f"  {PU}{B}◆ HELP{R}")
    print()
    print(f"  {PU}{B}◆ AUTO{R}   کلید {WH}a{R} — خودکار")
    print(f"  {GR}{B}★ SMART{R}  کلید {WH}s{R} — تایپ آزاد")
    print()
    print(f"  {CY}SMART MODE{R}:")
    print(f"    search fastapi")
    print(f"    graph asyncio")
    print(f"    اجرا 3")
    print(f"    مشاور پکیج")
    print(f"    متا")
    print(f"    پشتیبان")
    print()
    pause()


# ═══════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════

def main():
    while True:
        try:
            show_menu()
            c = ask("انتخاب")

            if c is None or c.strip().lower() in ("q", "quit", "exit", "0", "خروج"):
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
            elif c == "7":
                # مستقیم گراف
                clear()
                run_cmd("top", "25")
                pause()
            elif c in ("13", "14", "15"):
                clear()
                run_py("auth.py", "status")
                pause()
            elif c == "23":
                clear()
                run_py("feature_snapshot.py", "build")
                pause()
            else:
                clear()
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

