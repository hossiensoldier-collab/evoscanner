#!/usr/bin/env python3
"""EvoScanner Panel v10 — Infinite Edition"""
import json
import os
import random
import subprocess
import sys
import time
from collections import Counter, deque
from datetime import datetime
from pathlib import Path
import engines
import selfcare
import deep_test
import panel_test
import health
import autoheal

BASE = Path.home() / "evoscanner"
os.chdir(str(BASE))


# ═══════════════════════════════════════════════════
#  COLORS
# ═══════════════════════════════════════════════════

class C:
    R = "\033[0m"
    B = "\033[1m"
    D = "\033[2m"
    I = "\033[3m"
    U = "\033[4m"

    CY = "\033[38;2;100;220;230m"
    PU = "\033[38;2;180;140;255m"
    PK = "\033[38;2;255;140;200m"
    YL = "\033[38;2;255;215;80m"
    GR = "\033[38;2;120;230;150m"
    RD = "\033[38;2;255;110;110m"
    BL = "\033[38;2;120;170;255m"
    OR = "\033[38;2;255;160;80m"
    WH = "\033[38;2;230;230;240m"
    GY = "\033[38;2;130;135;150m"


# ═══════════════════════════════════════════════════
#  STATE — favorites + history
# ═══════════════════════════════════════════════════

STATE_FILE = BASE / ".v10_state.json"


class State:
    def __init__(self):
        self.data = self._load()

    def _load(self):
        if STATE_FILE.exists():
            try:
                return json.loads(STATE_FILE.read_text())
            except Exception:
                pass
        return {"favorites": [], "recent": [], "stats_history": []}

    def save(self):
        try:
            STATE_FILE.write_text(json.dumps(self.data, indent=2))
        except Exception:
            pass

    def fav_add(self, item):
        if item not in self.data["favorites"]:
            self.data["favorites"].append(item)
            self.data["favorites"] = self.data["favorites"][-30:]
            self.save()

    def fav_remove(self, item):
        if item in self.data["favorites"]:
            self.data["favorites"].remove(item)
            self.save()

    def recent_add(self, item):
        r = self.data.setdefault("recent", [])
        r[:] = [x for x in r if x != item]
        r.insert(0, item)
        del r[50:]
        self.save()

    def record_stats(self, s):
        h = self.data.setdefault("stats_history", [])
        h.append({"ts": datetime.now().isoformat(),
                  "src": s["src"], "tech": s["tech"],
                  "graph": s["graph"], "snip": s["snip"]})
        del h[:-100]
        self.save()


STATE = State()


# ═══════════════════════════════════════════════════
#  UI
# ═══════════════════════════════════════════════════

def clear():
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def ask(prompt, default=""):
    try:
        pr = f"{C.CY}{C.B}❯{C.R} {C.WH}{prompt}{C.R}"
        if default:
            pr += f" {C.D}[{default}]{C.R}"
        pr += f"{C.CY} : {C.R}"
        s = input(pr).strip()
        return s if s else default
    except (EOFError, KeyboardInterrupt):
        print()
        return None


def pause(msg="ادامه"):
    try:
        input(f"\n  {C.D}{msg}...{C.R}")
    except (EOFError, KeyboardInterrupt):
        print()


def stats():
    st = {"src": 0, "graph": 0, "tech": 0, "snip": 0, "db_mb": 0}
    try:
        import sqlite3
        db = sqlite3.connect(BASE / "knowledge.db")
        st["src"] = db.execute("SELECT COUNT(*) FROM resources").fetchone()[0]
        for k, t in [("tech", "techniques"), ("snip", "snippets")]:
            try:
                st[k] = db.execute(
                    f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            except Exception:
                pass
        db.close()
        st["db_mb"] = (BASE / "knowledge.db").stat().st_size // (1024 * 1024)
    except Exception:
        pass
    try:
        g = json.loads((BASE / "graph.json").read_text())
        st["graph"] = sum(1 for v in g["nodes"].values()
                          if v.get("type") == "entity")
    except Exception:
        pass
    return st


def bar(value, max_v, width=20, color=None):
    if max_v <= 0:
        return ""
    filled = int(value / max_v * width)
    col = color or C.GR
    return col + "█" * filled + C.D + "░" * (width - filled) + C.R


def sparkline(values, width=30):
    if not values:
        return ""
    chars = "▁▂▃▄▅▆▇█"
    vals = values[-width:]
    mn, mx = min(vals), max(vals)
    if mx == mn:
        return C.CY + chars[0] * len(vals) + C.R
    out = ""
    for v in vals:
        idx = int((v - mn) / (mx - mn) * (len(chars) - 1))
        out += chars[idx]
    return C.CY + out + C.R


def header(subtitle=""):
    clear()
    s = stats()
    STATE.record_stats(s)
    print()
    print(f"  {C.CY}╭{'─' * 56}╮{C.R}")
    print(f"  {C.CY}│{C.R} {C.PU}{C.B}◆{C.R} {C.WH}{C.B}E V O S C A N N E R{C.R}"
          f"  {C.GY}v10{C.R}  {C.GR}●{C.R}")
    if subtitle:
        print(f"  {C.CY}│{C.R} {C.D}{subtitle}{C.R}")
    print(f"  {C.CY}╰{'─' * 56}╯{C.R}")
    print()
    print(f"  {C.GY}src{C.R} {C.YL}{s['src']:>4}{C.R}   "
          f"{C.GY}graph{C.R} {C.CY}{s['graph']:>4}{C.R}   "
          f"{C.GY}tech{C.R} {C.GR}{s['tech']:>4}{C.R}   "
          f"{C.GY}snip{C.R} {C.GR}{s['snip']:>4}{C.R}   "
          f"{C.GY}db{C.R} {C.OR}{s['db_mb']}MB{C.R}")
    print()


def menu_item(num, title, sub, color=None):
    col = color or C.CY
    n = str(num)
    if len(n) == 1:
        n = f" {n}"
    print(f"  {C.GY}│{C.R} {col}{C.B}[{n}]{C.R}  "
          f"{C.WH}{title:<12s}{C.R} {C.D}{sub}{C.R}")


def group(text):
    print(f"  {C.PU}{C.B}┌─ {text}{C.R}")


def run_cmd(*args):
    try:
        subprocess.run([sys.executable, "evoscanner_v2.py"] + list(args),
                       cwd=str(BASE))
    except KeyboardInterrupt:
        print()


def run_py(script, *args):
    try:
        subprocess.run([sys.executable, script] + list(args), cwd=str(BASE))
    except KeyboardInterrupt:
        print()


def run_py_capture(script, *args, timeout=60):
    """اجرای اسکریپت و برگشت خروجی"""
    try:
        r = subprocess.run(
            [sys.executable, script] + list(args),
            cwd=str(BASE), capture_output=True, text=True, timeout=timeout)
        return r.stdout or "", r.stderr or ""
    except Exception as e:
        return "", str(e)


# ═══════════════════════════════════════════════════
#  MAIN MENU
# ═══════════════════════════════════════════════════

def main_menu():
    header()
    print(f"  {C.PU}{C.B}▸ NEXT{C.R}")
    s = stats()
    hints = []
    if s["src"] < 400:
        hints.append((C.YL, "GET", "2·2", "enrich"))
    if s["tech"] < 200:
        hints.append((C.GR, "LEARN", "3·1", "extract"))
    if s["graph"] < 600:
        hints.append((C.CY, "GET", "2·3", "rebuild"))
    if not hints:
        hints.append((C.PU, "AUTO", "a", "خودکار"))
        hints.append((C.CY, "SMART", "s", "تایپ آزاد"))
    for col, tag, key, desc in hints[:3]:
        print(f"    {col}{tag:6s}{C.R} {C.WH}{key:8s}{C.R} {C.D}{desc}{C.R}")
    print()

    group("KAR")
    menu_item(1, "ASK", "سؤال · جستجو · مشاور", C.CY)
    menu_item(2, "GET", "جذب منابع · چرخه", C.YL)
    menu_item(7, "GRAPH", "کاوش گراف", C.BL)
    print(f"  {C.GY}│{C.R}")

    group("DANESH")
    menu_item(3, "LEARN", "یادگیری · مسیر", C.GR)
    menu_item(8, "SOURCES", "منابع جدید", C.GR)
    menu_item(9, "IDEAS", "پیشنهاد پروژه", C.GR)
    print(f"  {C.GY}│{C.R}")

    group("SYSTEM")
    menu_item(4, "EVOLVE", "خودارتقایی", C.PK)
    menu_item(5, "DATA", "خروجی", C.OR)
    menu_item(6, "SERVERS", "API · وب", C.BL)
    print(f"  {C.GY}│{C.R}")

    group("ENGINES")
    menu_item(15, "ENGINES", "due · forge · sacred", C.PU)
    menu_item(16, "DUE", "خودارتقایی · ۴۵۵۶ خط", C.PK)
    menu_item(17, "SELF-CARE", "ترمیم · ارتقا · صافی", C.PK)
    menu_item(18, "AUTO-HEAL", "تشخیص و تعمیر خودکار", C.RD)
    menu_item(19, "HEALTH", "داشبورد سلامت", C.GR)
    menu_item(20, "TEST", "تست سریع پنل", C.CY)
    menu_item(21, "DEEP-TEST", "تست کامل زیرمنوها", C.CY)
    print(f"  {C.GY}│{C.R}")

    group("POWER")
    menu_item(10, "DASHBOARD", "داشبورد زنده", C.PU)
    menu_item(11, "HISTORY", "تاریخچه + Favorites", C.PU)
    menu_item(12, "SEARCH", "جستجوی جهانی", C.PU)
    menu_item(13, "TASKS", "اجرای موازی", C.PU)
    menu_item(14, "SETTINGS", "تنظیمات", C.GY)
    print(f"  {C.PU}{C.B}└{'─' * 54}{C.R}")
    print()
    print(f"  {C.PU}{C.B}◆ AUTO{C.R}   {C.D}خودکار{C.R}    "
          f"{C.GR}{C.B}★ SMART{C.R}  {C.D}تایپ آزاد{C.R}    "
          f"{C.RD}{C.B}✕ EXIT{C.R}   {C.D}خروج{C.R}")
    print()
    return ask("انتخاب")


# ═══════════════════════════════════════════════════
#  ASK
# ═══════════════════════════════════════════════════

def sub_ask():
    while True:
        header("ASK — سؤال و کاوش")
        group("QUERY")
        menu_item(1, "SEARCH", "جستجو در منابع", C.CY)
        menu_item(2, "ASK", "پرسش RAG", C.CY)
        menu_item(3, "RELATED", "پکیج مرتبط", C.CY)
        menu_item(4, "PATH", "مسیر گراف", C.BL)
        menu_item(5, "COMPARE", "مقایسه دو پکیج", C.BL)
        menu_item(6, "ADVISOR", "مشاور پکیج", C.GR)
        menu_item(7, "IDEAS", "پیشنهاد پروژه", C.GR)
        menu_item(8, "RAG4", "RAG snippet", C.PU)
        menu_item(0, "BACK", "", C.RD)
        print(f"  {C.PU}{C.B}└{'─' * 54}{C.R}")
        print()
        c = ask("انتخاب")
        if c in (None, "0"):
            return
        if c == "1":
            q = ask("جستجو")
            if q:
                STATE.recent_add(f"search:{q}")
                clear(); run_cmd("search", q); pause()
        elif c == "2":
            q = ask("سؤال")
            if q:
                STATE.recent_add(f"ask:{q}")
                clear(); run_cmd("ask", q); pause()
        elif c == "3":
            p = ask("پکیج")
            if p:
                STATE.recent_add(f"related:{p}")
                clear(); run_cmd("related", p); pause()
        elif c == "4":
            a = ask("از"); b = ask("به")
            if a and b:
                clear(); run_cmd("graph-path", a, b); pause()
        elif c == "5":
            a = ask("پکیج 1"); b = ask("پکیج 2")
            if a and b:
                clear()
                run_py("-c", f"""
import sys
sys.path.insert(0, "features")
from evoscanner_v2 import KB
import compare
import engines
compare.compare(KB(), {a!r}, {b!r})
""")
                pause()
        elif c == "6":
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
        elif c == "7":
            clear()
            run_py("-c", """
import sys
sys.path.insert(0, "features")
from evoscanner_v2 import KB
import project_ideas
project_ideas.show(KB(), n=5)
""")
            pause()
        elif c == "8":
            q = ask("سؤال")
            if q:
                clear(); run_py("feature_rag_v4.py", q); pause()


# ═══════════════════════════════════════════════════
#  GET
# ═══════════════════════════════════════════════════

def sub_get():
    while True:
        header("GET — جذب منابع")
        group("COLLECT")
        menu_item(1, "RUN", "چرخه کشف", C.YL)
        menu_item(2, "ENRICH", "README کامل", C.YL)
        menu_item(3, "REBUILD", "بازسازی گراف", C.CY)
        menu_item(4, "HUNTER", "کوئری هوشمند", C.YL)
        menu_item(5, "SOURCES", "منابع گسترده", C.GR)
        menu_item(6, "TOKEN", "GitHub Token", C.OR)
        menu_item(7, "BULK-5", "۵ چرخه خودکار", C.YL)
        menu_item(8, "BULK-10", "۱۰ چرخه", C.YL)
        menu_item(0, "BACK", "", C.RD)
        print(f"  {C.PU}{C.B}└{'─' * 54}{C.R}")
        print()
        c = ask("انتخاب")
        if c in (None, "0"):
            return
        if c == "1":
            n = ask("تعداد", "2")
            clear(); run_cmd("reset-health"); run_cmd("run", n)
            run_cmd("rebuild"); pause()
        elif c == "2":
            n = ask("تعداد", "50")
            clear(); run_cmd("enrich", n); run_cmd("rebuild"); pause()
        elif c == "3":
            clear(); run_cmd("rebuild"); pause()
        elif c == "4":
            clear(); run_cmd("learn"); pause()
        elif c == "5":
            clear(); run_cmd("offline"); pause()
        elif c == "6":
            clear(); run_py("auth.py", "status"); pause()
        elif c == "7":
            for i in range(5):
                print(f"  {C.CY}cycle {i + 1}/5{C.R}")
                run_cmd("run", "1")
                if i < 4:
                    time.sleep(30)
            run_cmd("rebuild"); pause()
        elif c == "8":
            for i in range(10):
                print(f"  {C.CY}cycle {i + 1}/10{C.R}")
                run_cmd("run", "1")
                if i < 9:
                    time.sleep(20)
            run_cmd("rebuild"); pause()


# ═══════════════════════════════════════════════════
#  LEARN
# ═══════════════════════════════════════════════════

def sub_learn():
    while True:
        header("LEARN — یادگیری")
        group("KNOWLEDGE")
        menu_item(1, "EXTRACT", "استخراج دانش", C.GR)
        menu_item(2, "STATS", "آمار دانش", C.GR)
        menu_item(3, "PATH", "مسیر ۴ سطحی", C.GR)
        menu_item(4, "GOALS", "اهداف آماده", C.GR)
        menu_item(5, "TECH", "تکنیک‌ها", C.GR)
        menu_item(6, "SNIPPETS", "قطعات کد", C.GR)
        menu_item(7, "GRAPHICS", "گرافیک", C.GR)
        menu_item(0, "BACK", "", C.RD)
        print(f"  {C.PU}{C.B}└{'─' * 54}{C.R}")
        print()
        c = ask("انتخاب")
        if c in (None, "0"):
            return
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
        elif c == "7":
            clear(); run_py("learn.py", "graphics"); pause()


# ═══════════════════════════════════════════════════
#  EVOLVE
# ═══════════════════════════════════════════════════

def sub_evolve():
    while True:
        header("EVOLVE — خودارتقایی")
        group("AGENTS")
        menu_item(1, "AGENTS", "۴ ایجنت", C.PK)
        menu_item(2, "META", "خودبازنویس", C.PK)
        menu_item(3, "METADATA", "فراداده", C.PK)
        menu_item(4, "CAPABILITY", "توانایی", C.PK)
        menu_item(5, "ANALYZE", "تحلیل پروژه", C.PU)
        menu_item(6, "SNAPSHOT", "پشتیبان", C.OR)
        print(f"  {C.GY}│{C.R}")
        group("GRAPH ALGORITHMS")
        menu_item(8, "DEPS", "گراف وابستگی", C.PU)
        menu_item(9, "ORACLE", "PageRank · Community", C.PU)
        menu_item(10, "ANALYTICS", "Betweenness · Cycle", C.PU)
        menu_item(11, "ADVANCED", "Influence · Predict", C.PU)
        menu_item(0, "BACK", "", C.RD)
        print(f"  {C.PU}{C.B}└{'─' * 54}{C.R}")
        print()
        c = ask("انتخاب")
        if c in (None, "0"):
            return
        elif c == "1":
            clear(); run_cmd("agents"); pause()
        elif c == "2":
            clear(); run_py("feature_meta.py", "cycle"); pause()
        elif c == "3":
            clear(); run_py("feature_metadata.py", "extract"); pause()
        elif c == "4":
            clear(); run_py("feature_capability.py"); pause()
        elif c == "5":
            clear()
            run_py("-c", """
import sys
sys.path.insert(0, ".")
import feature_meta
p = feature_meta.analyze_project()
print(f"Files: {len(p['files'])}")
print(f"Lines: {p['total_lines']:,}")
print(f"Issues: {len(p['issues'])}")
print("Opportunities:")
for o in p.get("opportunities", []):
    print(f"  - {o['type']}: {o['detail']}")
""")
            pause()
        elif c == "6":
            clear(); run_py("feature_snapshot.py", "build"); pause()
        elif c == "8":
            print()
            print("  [1] build  [2] stats  [3] requires  [4] breaks")
            sub = ask("انتخاب", "2")
            if sub == "1":
                clear()
                run_py("feature_deps.py", "build", "--limit=100"); pause()
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
            print("  [1] rank  [2] order  [3] community")
            print("  [4] path  [5] anomaly [6] stats")
            sub = ask("انتخاب", "1")
            if sub == "1":
                clear(); run_py("feature_oracle.py", "rank"); pause()
            elif sub == "2":
                p = ask("پکیج‌ها")
                if p:
                    pkgs = [x.strip() for x in p.split(",") if x.strip()]
                    clear()
                    run_py("feature_oracle.py", "order", *pkgs); pause()
            elif sub == "3":
                clear(); run_py("feature_oracle.py", "community"); pause()
            elif sub == "4":
                a = ask("از"); b = ask("به")
                if a and b:
                    clear()
                    run_py("feature_oracle.py", "path", a, b); pause()
            elif sub == "5":
                clear(); run_py("feature_oracle.py", "anomaly"); pause()
            elif sub == "6":
                clear(); run_py("feature_oracle.py", "stats"); pause()
        elif c == "10":
            print()
            print("  [1] betweenness [2] kcore")
            print("  [3] cycles      [4] simrank")
            sub = ask("انتخاب", "3")
            if sub == "1":
                clear()
                run_py("feature_analytics.py", "betweenness"); pause()
            elif sub == "2":
                clear(); run_py("feature_analytics.py", "kcore"); pause()
            elif sub == "3":
                clear(); run_py("feature_analytics.py", "cycles"); pause()
            elif sub == "4":
                p = ask("پکیج")
                if p:
                    clear()
                    run_py("feature_analytics.py", "simrank", p); pause()
        elif c == "11":
            print()
            print("  [1] influence [2] spread   [3] community")
            print("  [4] predict   [5] predict-all")
            sub = ask("انتخاب", "1")
            if sub == "1":
                k = ask("تعداد seed", "5")
                clear()
                run_py("feature_advanced.py", "influence", str(k)); pause()
            elif sub == "2":
                p = ask("پکیج")
                if p:
                    clear()
                    run_py("feature_advanced.py", "spread", p); pause()
            elif sub == "3":
                clear()
                run_py("feature_advanced.py", "community"); pause()
            elif sub == "4":
                m = ask("روش", "adamic_adar")
                clear()
                run_py("feature_advanced.py", "predict", m); pause()
            elif sub == "5":
                clear()
                run_py("feature_advanced.py", "predict-all"); pause()


# ═══════════════════════════════════════════════════
#  DATA
# ═══════════════════════════════════════════════════

def sub_data():
    while True:
        header("DATA — خروجی و پشتیبان")
        group("EXPORT")
        menu_item(1, "EXPORT-ALL", "JSON + CSV + MD", C.OR)
        menu_item(2, "REPORT", "گزارش روزانه", C.OR)
        menu_item(3, "STATS", "آمار کامل", C.CY)
        menu_item(4, "CATEGORIES", "دسته‌ها", C.CY)
        menu_item(5, "SNAPSHOT", "پشتیبان برای AI", C.PU)
        menu_item(6, "CLEANUP", "پاک‌سازی", C.RD)
        menu_item(0, "BACK", "", C.RD)
        print(f"  {C.PU}{C.B}└{'─' * 54}{C.R}")
        print()
        c = ask("انتخاب")
        if c in (None, "0"):
            return
        if c == "1":
            clear(); run_cmd("export"); pause()
        elif c == "2":
            clear(); run_cmd("report"); pause()
        elif c == "3":
            clear(); run_cmd("stats"); pause()
        elif c == "4":
            clear(); run_cmd("categories"); pause()
        elif c == "5":
            clear(); run_py("feature_snapshot.py", "build"); pause()
        elif c == "6":
            clear(); run_py("feature_cleanup.py", "report"); pause()


# ═══════════════════════════════════════════════════
#  SERVERS
# ═══════════════════════════════════════════════════

def sub_servers():
    while True:
        header("SERVERS — سرورها")
        group("RUNNING")
        menu_item(1, "WEB", "رابط وب", C.BL)
        menu_item(2, "API", "سرور API :8081", C.BL)
        menu_item(3, "GRAPH-WEB", "نمای گراف SVG", C.BL)
        menu_item(4, "NETWORK", "تست شبکه", C.CY)
        menu_item(0, "BACK", "", C.RD)
        print(f"  {C.PU}{C.B}└{'─' * 54}{C.R}")
        print()
        c = ask("انتخاب")
        if c in (None, "0"):
            return
        if c == "1":
            clear(); run_cmd("web"); pause()
        elif c == "2":
            clear()
            try:
                subprocess.run([sys.executable, "api.py"], cwd=str(BASE))
            except KeyboardInterrupt:
                pass
        elif c == "3":
            clear(); run_py("-c", "import sys; sys.path.insert(0, \".\"); from graph_web import serve; serve()"); pause()
        elif c == "4":
            clear(); run_py("feature_net.py", "report"); pause()


# ═══════════════════════════════════════════════════
#  GRAPH
# ═══════════════════════════════════════════════════

def sub_graph():
    while True:
        header("GRAPH — کاوش")
        group("EXPLORE")
        menu_item(1, "TOP", "۲۵ نود برتر", C.BL)
        menu_item(2, "RELATED", "مرتبط‌ها", C.CY)
        menu_item(3, "PEERS", "هم‌دسته", C.CY)
        menu_item(4, "NEIGHBORS", "همسایه‌ها", C.CY)
        menu_item(5, "PATH", "کوتاه‌ترین مسیر", C.BL)
        menu_item(6, "CAT", "فیلتر دسته", C.CY)
        menu_item(0, "BACK", "", C.RD)
        print(f"  {C.PU}{C.B}└{'─' * 54}{C.R}")
        print()
        c = ask("انتخاب")
        if c in (None, "0"):
            return
        if c == "1":
            clear(); run_cmd("top", "25"); pause()
        elif c == "2":
            p = ask("پکیج")
            if p:
                clear(); run_cmd("graph-related", p); pause()
        elif c == "3":
            p = ask("پکیج")
            if p:
                clear(); run_cmd("graph-peers", p); pause()
        elif c == "4":
            p = ask("نود")
            if p:
                clear(); run_cmd("graph-neighbors", p); pause()
        elif c == "5":
            a = ask("از"); b = ask("به")
            if a and b:
                clear(); run_cmd("graph-path", a, b); pause()
        elif c == "6":
            cat = ask("دسته")
            if cat:
                clear(); run_cmd("cat", cat); pause()


# ═══════════════════════════════════════════════════
#  DASHBOARD — NEW
# ═══════════════════════════════════════════════════

def sub_dashboard():
    header("DASHBOARD — نمای زنده")
    s = stats()
    hist = STATE.data.get("stats_history", [])

    # ۱. Metrics cards
    print(f"  {C.PU}{C.B}▌ SNAPSHOT{C.R}")
    print()
    print(f"    {C.GY}منابع{C.R}       {C.YL}{C.B}{s['src']:>6}{C.R}")
    print(f"    {C.GY}گراف{C.R}        {C.CY}{C.B}{s['graph']:>6}{C.R}")
    print(f"    {C.GY}تکنیک{C.R}       {C.GR}{C.B}{s['tech']:>6}{C.R}")
    print(f"    {C.GY}snippet{C.R}    {C.GR}{C.B}{s['snip']:>6}{C.R}")
    print(f"    {C.GY}DB size{C.R}    {C.OR}{C.B}{s['db_mb']:>4} MB{C.R}")
    print()

    # ۲. Trend
    if len(hist) >= 2:
        print(f"  {C.PU}{C.B}▌ TREND (آخرین {len(hist)} رکورد){C.R}")
        print()
        src_vals = [h["src"] for h in hist]
        tech_vals = [h["tech"] for h in hist]
        gr_vals = [h["graph"] for h in hist]

        print(f"    {C.YL}src {C.R}  {sparkline(src_vals, 40)}")
        print(f"    {C.GR}tech{C.R}  {sparkline(tech_vals, 40)}")
        print(f"    {C.CY}graph{C.R} {sparkline(gr_vals, 40)}")
        print()

    # ۳. Category breakdown
    print(f"  {C.PU}{C.B}▌ CATEGORIES{C.R}")
    print()
    try:
        import sqlite3
        db = sqlite3.connect(BASE / "knowledge.db")
        rows = db.execute(
            """SELECT category, COUNT(*) as n FROM resources
               GROUP BY category ORDER BY n DESC LIMIT 10"""
        ).fetchall()
        db.close()
        mx = rows[0][1] if rows else 1
        for cat, n in rows:
            print(f"    {C.WH}{cat:12s}{C.R} {bar(n, mx, 30, C.CY)} "
                  f"{C.GR}{n:>4}{C.R}")
    except Exception:
        print(f"    {C.RD}خطا در بارگذاری{C.R}")
    print()

    # ۴. Top resources
    print(f"  {C.PU}{C.B}▌ TOP 5{C.R}")
    print()
    try:
        import sqlite3
        db = sqlite3.connect(BASE / "knowledge.db")
        rows = db.execute(
            """SELECT title, url, source, score FROM resources
               ORDER BY score DESC LIMIT 5"""
        ).fetchall()
        db.close()
        for title, url, src, sc in rows:
            print(f"    {C.GR}{sc:.2f}{C.R}  {C.WH}{title[:50]}{C.R}")
    except Exception:
        pass
    print()

    # ۵. Recent activity
    print(f"  {C.PU}{C.B}▌ RECENT{C.R}")
    print()
    for item in STATE.data.get("recent", [])[:5]:
        print(f"    {C.D}•{C.R} {C.WH}{item}{C.R}")
    print()
    pause()


# ═══════════════════════════════════════════════════
#  HISTORY + FAVORITES — NEW
# ═══════════════════════════════════════════════════

def sub_history():
    while True:
        header("HISTORY — تاریخچه + Favorites")
        group("VIEW")
        menu_item(1, "RECENT", "آخرین دستورات", C.PU)
        menu_item(2, "FAVORITES", "ستاره‌دارها", C.GR)
        menu_item(3, "STATS-HISTORY", "تاریخچه آمار", C.CY)
        menu_item(4, "CLEAR", "پاک‌سازی", C.RD)
        menu_item(0, "BACK", "", C.RD)
        print(f"  {C.PU}{C.B}└{'─' * 54}{C.R}")
        print()
        c = ask("انتخاب")
        if c in (None, "0"):
            return
        if c == "1":
            clear()
            print(f"\n  {C.PU}{C.B}◆ آخرین دستورات{C.R}\n")
            for i, item in enumerate(STATE.data.get("recent", []), 1):
                print(f"  {C.D}{i:2d}.{C.R} {C.WH}{item}{C.R}")
            print()
            # انتخاب برای replay
            n = ask("شماره برای اجرا (Enter=بازگشت)")
            try:
                idx = int(n) - 1
                recent = STATE.data.get("recent", [])
                if 0 <= idx < len(recent):
                    cmd = recent[idx]
                    if ":" in cmd:
                        typ, val = cmd.split(":", 1)
                        clear()
                        if typ == "search":
                            run_cmd("search", val)
                        elif typ == "ask":
                            run_cmd("ask", val)
                        elif typ == "related":
                            run_cmd("related", val)
                        else:
                            run_cmd(typ, val)
                        pause()
            except Exception:
                pass
        elif c == "2":
            clear()
            print(f"\n  {C.PU}{C.B}◆ Favorites{C.R}\n")
            favs = STATE.data.get("favorites", [])
            if not favs:
                print(f"  {C.D}خالی{C.R}")
            for i, item in enumerate(favs, 1):
                print(f"  {C.GR}{i:2d}.{C.R} {C.WH}{item}{C.R}")
            print()
            n = ask("حذف شماره (Enter=بازگشت)")
            try:
                idx = int(n) - 1
                if 0 <= idx < len(favs):
                    STATE.fav_remove(favs[idx])
            except Exception:
                pass
        elif c == "3":
            clear()
            print(f"\n  {C.PU}{C.B}◆ تاریخچه آمار{C.R}\n")
            hist = STATE.data.get("stats_history", [])
            for h in hist[-20:]:
                ts = h["ts"][:16].replace("T", " ")
                print(f"  {C.D}{ts}{C.R}  src={C.YL}{h['src']}{C.R} "
                      f"tech={C.GR}{h['tech']}{C.R} "
                      f"graph={C.CY}{h['graph']}{C.R}")
            print()
            pause()
        elif c == "4":
            if ask("پاک کن؟ (b/n)", "n").lower() == "b":
                STATE.data["recent"] = []
                STATE.data["stats_history"] = []
                STATE.save()


# ═══════════════════════════════════════════════════
#  UNIVERSAL SEARCH — NEW
# ═══════════════════════════════════════════════════

def sub_search():
    header("SEARCH — جستجوی جهانی")
    print(f"  {C.D}همه جا جستجو می‌کند: DB، Graph، Files، History{C.R}")
    print()
    q = ask("عبارت")
    if not q:
        return

    ql = q.lower()

    # ۱. DB
    print(f"\n  {C.PU}{C.B}▌ دیتابیس{C.R}\n")
    try:
        import sqlite3
        db = sqlite3.connect(BASE / "knowledge.db")
        rows = db.execute(
            """SELECT title, url, source, score FROM resources
               WHERE LOWER(title) LIKE ? OR LOWER(content) LIKE ?
               ORDER BY score DESC LIMIT 8""",
            (f"%{ql}%", f"%{ql}%")
        ).fetchall()
        db.close()
        if not rows:
            print(f"    {C.D}چیزی نیست{C.R}")
        for title, url, src, sc in rows:
            print(f"    {C.GR}{sc:.2f}{C.R} [{C.CY}{src}{C.R}] "
                  f"{C.WH}{title[:55]}{C.R}")
    except Exception:
        pass

    # ۲. Graph
    print(f"\n  {C.PU}{C.B}▌ گراف{C.R}\n")
    try:
        g = json.loads((BASE / "graph.json").read_text())
        matches = []
        for n, v in g["nodes"].items():
            if v.get("type") != "entity":
                continue
            if ql in n.lower():
                matches.append((n, v.get("count", 0)))
        matches.sort(key=lambda x: -x[1])
        if not matches:
            print(f"    {C.D}چیزی نیست{C.R}")
        for n, c in matches[:8]:
            print(f"    {C.CY}count={c}{C.R}  {C.WH}{n}{C.R}")
    except Exception:
        pass

    # ۳. Files
    print(f"\n  {C.PU}{C.B}▌ فایل‌ها{C.R}\n")
    matches = []
    try:
        for f in BASE.glob("*.py"):
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                if ql in content.lower():
                    count = content.lower().count(ql)
                    matches.append((f.name, count))
            except Exception:
                pass
        matches.sort(key=lambda x: -x[1])
        if not matches:
            print(f"    {C.D}چیزی نیست{C.R}")
        for name, c in matches[:8]:
            print(f"    {C.YL}{c:>3}{C.R} hits in {C.WH}{name}{C.R}")
    except Exception:
        pass

    # ۴. History
    print(f"\n  {C.PU}{C.B}▌ تاریخچه{C.R}\n")
    hist = [x for x in STATE.data.get("recent", []) if ql in x.lower()]
    if not hist:
        print(f"    {C.D}چیزی نیست{C.R}")
    for item in hist[:5]:
        print(f"    {C.D}•{C.R} {C.WH}{item}{C.R}")
    print()

    # ذخیره به favorites
    if ask("به Favorites اضافه شود؟ (b/n)", "n").lower() == "b":
        STATE.fav_add(q)
        print(f"  {C.GR}✓ اضافه شد{C.R}")

    pause()


# ═══════════════════════════════════════════════════
#  TASKS — NEW: parallel runner
# ═══════════════════════════════════════════════════

def sub_tasks():
    header("TASKS — اجرای موازی")
    print(f"  {C.D}چند task را همزمان اجرا کن{C.R}")
    print()

    # پیش‌فرض‌ها
    TASKS = {
        "1": ("rebuild", ["evoscanner_v2.py", "rebuild"]),
        "2": ("extract", ["learn.py", "extract"]),
        "3": ("meta", ["feature_meta.py", "cycle"]),
        "4": ("enrich", ["evoscanner_v2.py", "enrich", "30"]),
        "5": ("export", ["evoscanner_v2.py", "export"]),
        "6": ("snapshot", ["feature_snapshot.py", "build"]),
        "7": ("agents", ["evoscanner_v2.py", "agents"]),
        "8": ("stats", ["evoscanner_v2.py", "stats"]),
    }

    group("AVAILABLE")
    for k, (name, cmd) in TASKS.items():
        print(f"  {C.GY}│{C.R} {C.YL}[{k}]{C.R}  {C.WH}{name:<15s}{C.R} "
              f"{C.D}{' '.join(cmd)}{C.R}")
    print(f"  {C.PU}{C.B}└{'─' * 54}{C.R}")
    print()

    sel = ask("انتخاب (مثلاً 1,2,5)")
    if not sel:
        return

    indices = [x.strip() for x in sel.split(",") if x.strip() in TASKS]
    if not indices:
        print(f"  {C.RD}نامعتبر{C.R}")
        pause(); return

    print()
    print(f"  {C.CY}اجرای {len(indices)} task به موازات...{C.R}")
    print()

    # اجرای موازی با Popen
    procs = []
    for i in indices:
        name, cmd = TASKS[i]
        log = BASE / f".task_{name}.log"
        try:
            f = open(log, "w")
            p = subprocess.Popen(
                [sys.executable] + cmd,
                cwd=str(BASE), stdout=f, stderr=subprocess.STDOUT)
            procs.append((i, name, p, log))
            print(f"  {C.GR}▶{C.R} {name}  (PID {p.pid})")
        except Exception as e:
            print(f"  {C.RD}✗{C.R} {name}: {e}")

    print()
    print(f"  {C.D}منتظر اتمام...{C.R}")

    # انتظار
    while procs:
        time.sleep(1)
        running = []
        for i, name, p, log in procs:
            if p.poll() is None:
                running.append((i, name, p, log))
            else:
                status = (C.GR + "✓" if p.returncode == 0
                          else C.RD + "✗") + C.R
                print(f"    {status} {name}  (exit {p.returncode})")
        procs = running

    print()
    print(f"  {C.GR}✓ همه تمام شد{C.R}")
    pause()


# ═══════════════════════════════════════════════════
#  SETTINGS
# ═══════════════════════════════════════════════════

def sub_settings():
    while True:
        header("SETTINGS")
        group("CONFIG")
        menu_item(1, "FAV-CLEAR", "پاک‌سازی Favorites", C.RD)
        menu_item(2, "STATE-CLEAR", "پاک‌سازی State", C.RD)
        menu_item(3, "VIEW-STATE", "نمایش State", C.CY)
        menu_item(4, "BACKUP-STATE", "پشتیبان State", C.GR)
        menu_item(0, "BACK", "", C.RD)
        print(f"  {C.PU}{C.B}└{'─' * 54}{C.R}")
        print()
        c = ask("انتخاب")
        if c in (None, "0"):
            return
        elif c == "1":
            if ask("پاک شود؟ (b/n)", "n").lower() == "b":
                STATE.data["favorites"] = []
                STATE.save()
        elif c == "2":
            if ask("پاک شود؟ (b/n)", "n").lower() == "b":
                STATE.data = {"favorites": [], "recent": [],
                              "stats_history": []}
                STATE.save()
        elif c == "3":
            clear()
            print(json.dumps(STATE.data, indent=2, ensure_ascii=False))
            pause()
        elif c == "4":
            import shutil
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest = BASE / f".v10_state.{ts}.bak"
            shutil.copy(STATE_FILE, dest)
            print(f"  {C.GR}✓ {dest.name}{C.R}")
            pause()


# ═══════════════════════════════════════════════════
#  AUTOPILOT
# ═══════════════════════════════════════════════════

def autopilot():
    header("AUTOPILOT")
    s1 = stats()
    print(f"  {C.D}خودش تصمیم می‌گیرد{C.R}")
    print()
    plan = []
    if s1["src"] < 400:
        plan.append(("enrich 50", ["enrich", "50"]))
    if s1["tech"] < 200:
        plan.append(("extract", "py:learn.py:extract"))
    plan.append(("rebuild", ["rebuild"]))
    plan.append(("meta", "py:feature_meta.py:cycle"))
    if s1["graph"] < 700:
        plan.append(("run 2", ["run", "2"]))
    plan.append(("snapshot", "py:feature_snapshot.py:build"))

    print(f"  {C.D}برنامه:{C.R}")
    for i, (n, _) in enumerate(plan, 1):
        print(f"    {i}. {n}")
    print()
    pause("Enter برای شروع")

    for i, (name, action) in enumerate(plan, 1):
        print(f"\n  {C.PU}[{i}/{len(plan)}]{C.R} {C.WH}{name}{C.R}")
        if isinstance(action, list):
            run_cmd(*action)
        elif action.startswith("py:"):
            parts = action.split(":")
            run_py(parts[1], *parts[2:])
        print(f"  {C.GR}✓{C.R}")

    s2 = stats()
    print()
    print(f"  {C.CY}{'─' * 50}{C.R}")
    print(f"  {C.GR}{C.B}✓ تمام{C.R}")
    print(f"  {C.CY}{'─' * 50}{C.R}")
    print()
    print(f"    src   {s1['src']:>4} → {s2['src']:>4}  "
          f"({s2['src'] - s1['src']:+d})")
    print(f"    tech  {s1['tech']:>4} → {s2['tech']:>4}  "
          f"({s2['tech'] - s1['tech']:+d})")
    print(f"    graph {s1['graph']:>4} → {s2['graph']:>4}  "
          f"({s2['graph'] - s1['graph']:+d})")
    print()
    pause()


# ═══════════════════════════════════════════════════
#  SMART MODE
# ═══════════════════════════════════════════════════

def smart():
    header("SMART MODE")
    print(f"  {C.D}هرچی بگو — خودش می‌فهمد{C.R}")
    print()
    text = ask("چی می‌خواهی؟")
    if not text:
        return

    STATE.recent_add(f"smart:{text}")
    p = text.split()
    f = p[0].lower()

    if f in ("search", "s", "جستجو", "سرچ"):
        q = " ".join(p[1:]) or ask("جستجو")
        if q:
            clear(); run_cmd("search", q); pause()
    elif f in ("ask", "a", "بپرس"):
        q = " ".join(p[1:]) or ask("سؤال")
        if q:
            clear(); run_cmd("ask", q); pause()
    elif f in ("related", "r", "مرتبط"):
        x = " ".join(p[1:]) or ask("پکیج")
        if x:
            clear(); run_cmd("related", x); pause()
    elif f in ("graph", "g", "گراف"):
        x = " ".join(p[1:]) or ask("موجودیت")
        if x:
            clear(); run_cmd("graph-related", x); pause()
    elif f in ("run", "cycle", "چرخه", "اجرا"):
        n = p[1] if len(p) > 1 else "2"
        clear()
        run_cmd("reset-health"); run_cmd("run", n); run_cmd("rebuild")
        pause()
    elif f in ("extract", "استخراج"):
        clear(); run_py("learn.py", "extract"); pause()
    elif f in ("stats", "آمار"):
        clear(); run_cmd("stats"); pause()
    elif f in ("snapshot", "پشتیبان"):
        clear(); run_py("feature_snapshot.py", "build"); pause()
    elif f in ("meta", "متا"):
        clear(); run_py("feature_meta.py", "cycle"); pause()
    elif f in ("agents", "ایجنت"):
        clear(); run_cmd("agents"); pause()
    elif f in ("help", "h", "راهنما"):
        clear()
        print(f"\n  {C.PU}{C.B}◆ HELP{C.R}\n")
        print(f"  {C.CY}search{C.R} <q>     جستجو")
        print(f"  {C.CY}ask{C.R} <q>        پرسش")
        print(f"  {C.CY}related{C.R} <pkg>  مرتبط")
        print(f"  {C.CY}graph{C.R} <node>   گراف")
        print(f"  {C.CY}run{C.R} <n>        چرخه")
        print(f"  {C.CY}extract{C.R}        استخراج")
        print(f"  {C.CY}stats{C.R}          آمار")
        print(f"  {C.CY}snapshot{C.R}       پشتیبان")
        print()
        pause()
    else:
        clear(); run_cmd("search", text); pause()


# ═══════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════

def main():
    while True:
        try:
            c = main_menu()
            if c is None or c.strip().lower() in ("q", "exit", "0", "خروج"):
                clear()
                print(f"\n  {C.CY}Bedrood 👋{C.R}\n")
                return

            c = c.strip().lower()

            if c in ("a", "auto", "اتو", "خودکار"):
                autopilot()
            elif c in ("s", "smart", "هوش"):
                smart()
            elif c == "1":
                sub_ask()
            elif c == "2":
                sub_get()
            elif c == "3":
                sub_learn()
            elif c == "4":
                sub_evolve()
            elif c == "5":
                sub_data()
            elif c == "6":
                sub_servers()
            elif c == "7":
                sub_graph()
            elif c == "8":
                sub_get()  # sources — alias به get
            elif c == "9":
                sub_ask()  # ideas — alias
            elif c == "10":
                sub_dashboard()
            elif c == "11":
                sub_history()
            elif c == "12":
                sub_search()
            elif c == "13":
                sub_tasks()
            elif c == "14":
                sub_settings()
            elif c == "15":
                clear()
                try:
                    engines.engines_menu()
                except Exception as e:
                    print(f"\n  {C.RD}خطا: {e}{C.R}\n")
                    pause()
            elif c == "16":
                clear()
                try:
                    engines.due_menu()
                except Exception as e:
                    print(f"\n  {C.RD}خطا: {e}{C.R}\n")
                    pause()
            elif c == "17":
                clear()
                try:
                    selfcare.main_menu()
                except Exception as e:
                    print(f"\n  {C.RD}خطا: {e}{C.R}\n")
                    pause()
            elif c == "18":
                clear()
                try:
                    autoheal.run()
                except Exception as e:
                    print(f"\n  {C.RD}خطا: {e}{C.R}\n")
                    pause()
            elif c == "19":
                clear()
                try:
                    health.check()
                except Exception as e:
                    print(f"خطا: {e}")
                    pause()
            elif c == "20":
                clear()
                try:
                    panel_test.main()
                except Exception as e:
                    print(f"خطا: {e}")
                    pause()
            elif c == "21":
                clear()
                try:
                    deep_test.main()
                except Exception as e:
                    print(f"خطا: {e}")
                    pause()
            else:
                clear()
                run_cmd("search", c)
                pause()

        except KeyboardInterrupt:
            print()
            continue
        except Exception as e:
            print(f"\n  {C.RD}خطا: {e}{C.R}\n")
            pause()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        clear()
        print("\nBye\n")