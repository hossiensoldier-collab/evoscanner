#!/usr/bin/env python3
"""EvoScanner Panel v6 — بازسازی‌شده با ارتقای جهشی"""
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

BASE = Path.home() / "evoscanner"
os.chdir(str(BASE))

# ═══════════════════════════════════════════════════
#  رنگ‌ها — Cyberpunk × Material mix
# ═══════════════════════════════════════════════════

class C:
    # پایه
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDER = "\033[4m"

    # رنگ‌های ۲۴ بیتی — تم سایبرپانک آرام
    BG = "\033[48;2;15;17;23m"          # پس‌زمینه تیره
    CYAN = "\033[38;2;100;220;230m"     # فیروزه‌ای
    PURPLE = "\033[38;2;180;140;255m"   # بنفش
    PINK = "\033[38;2;255;140;200m"     # صورتی
    M = "\033[38;2;200;150;255m"
    YELLOW = "\033[38;2;255;215;80m"    # زرد
    GREEN = "\033[38;2;120;230;150m"    # سبز
    RED = "\033[38;2;255;110;110m"      # قرمز
    BLUE = "\033[38;2;120;170;255m"     # آبی
    ORANGE = "\033[38;2;255;160;80m"    # نارنجی
    WHITE = "\033[38;2;230;230;240m"    # سفید
    GRAY = "\033[38;2;130;135;150m"     # خاکستری


def clear():
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def ask(p, default=""):
    try:
        prompt = f"{C.CYAN}{C.BOLD}❯{C.RESET} {C.WHITE}{p}{C.RESET}"
        if default:
            prompt += f" {C.DIM}[{default}]{C.RESET}"
        prompt += f"{C.CYAN} : {C.RESET}"
        s = input(prompt).strip()
        return s or default
    except (EOFError, KeyboardInterrupt):
        return None


def pause(msg="ادامه..."):
    try:
        input(f"\n  {C.DIM}{msg} [Enter]{C.RESET}")
    except (EOFError, KeyboardInterrupt):
        pass


# ═══════════════════════════════════════════════════
#  آمار زنده
# ═══════════════════════════════════════════════════

def get_stats():
    st = {"src": 0, "graph": 0, "tech": 0, "snip": 0, "db_mb": 0}
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


# ═══════════════════════════════════════════════════
#  بنر
# ═══════════════════════════════════════════════════

def banner():
    clear()
    s = get_stats()

    print()
    print(f"{C.CYAN}  ══════════════════════════════════════════════════{C.RESET}")
    print(f"{C.PURPLE}  ◆{C.RESET} {C.WHITE}{C.BOLD}EVOSCANNER{C.RESET} "
          f"{C.GRAY}v6.0{C.RESET}")
    print(f"{C.PURPLE}  ◆{C.RESET} {C.DIM}Self-Evolving Knowledge System{C.RESET}")
    print(f"{C.CYAN}  ══════════════════════════════════════════════════{C.RESET}")
    print()

    # آمار در یک نوار
    print(f"  {C.DIM}┃{C.RESET} {C.GRAY}src{C.RESET} "
          f"{C.YELLOW}{s['src']:>4}{C.RESET}   "
          f"{C.GRAY}graph{C.RESET} {C.CYAN}{s['graph']:>4}{C.RESET}   "
          f"{C.GRAY}tech{C.RESET} {C.GREEN}{s['tech']:>4}{C.RESET}   "
          f"{C.GRAY}snip{C.RESET} {C.GREEN}{s['snip']:>4}{C.RESET}   "
          f"{C.GRAY}db{C.RESET} {C.ORANGE}{s['db_mb']}MB{C.RESET}")
    print()


# ═══════════════════════════════════════════════════
#  NEXT Hint — پیشنهاد هوشمند
# ═══════════════════════════════════════════════════

def next_hint():
    hints = []
    s = get_stats()

    if s["src"] < 200:
        hints.append(("GET", "2 → 1", "منابع کم است — چرخه بزن"))
    elif s["src"] < 400:
        hints.append(("GET", "2 → 2", "enrich برای README کامل"))

    if s["tech"] < 100:
        hints.append(("LEARN", "3 → 1", "extract تکنیک‌ها"))

    if s["graph"] < 600:
        hints.append(("GET", "2 → 3", "rebuild گراف"))

    # چک پشتیبان
    try:
        snaps = list((BASE / "snapshots").glob("snapshot_*.md"))
        if not snaps:
            hints.append(("EVOLVE", "4 → 9", "snapshot بگیر"))
    except Exception:
        pass

    if not hints:
        hints.append(("EVOLVE", "4 → 5", "AI Agent برای ارتقا"))
        hints.append(("MANAGE", "5 → 6", "خروجی JSON/CSV"))

    print(f"  {C.PURPLE}{C.BOLD}┃ NEXT{C.RESET}")
    for tag, key, desc in hints[:3]:
        color = {"GET": C.YELLOW, "LEARN": C.GREEN,
                 "EVOLVE": C.PINK, "MANAGE": C.CYAN}.get(tag, C.GRAY)
        print(f"  {C.DIM}┃{C.RESET}  {color}{tag:6s}{C.RESET} "
              f"{C.WHITE}{key:10s}{C.RESET} "
              f"{C.GRAY}{desc}{C.RESET}")
    print()


# ═══════════════════════════════════════════════════
#  آیتم منو
# ═══════════════════════════════════════════════════

def item(num, title, sub, color=None):
    color = color or C.CYAN
    print(f"  {C.DIM}┃{C.RESET} {color}{C.BOLD}[{num:>2}]{C.RESET}  "
          f"{C.WHITE}{C.BOLD}{title:<18s}{C.RESET} "
          f"{C.GRAY}{sub}{C.RESET}")


def header(text):
    print(f"  {C.PURPLE}{C.BOLD}┃ {text}{C.RESET}")
    print(f"  {C.DIM}┃{C.RESET}")


# ═══════════════════════════════════════════════════
#  منوی اصلی
# ═══════════════════════════════════════════════════

def main_menu():
    banner()
    next_hint()

    print(f"  {C.DIM}┃{C.RESET}")
    header("KAR")
    item(1, "ASK", "سؤال · جستجو · مشاور", C.CYAN)
    item(2, "GET", "جذب منابع · چرخه", C.YELLOW)
    item(7, "GRAPH", "کاوش گراف", C.BLUE)
    print(f"  {C.DIM}┃{C.RESET}")

    header("DANESH")
    item(3, "LEARN", "یادگیری · مسیر · دانش", C.GREEN)
    item(12, "SOURCES", "منابع گسترده", C.GREEN)
    item(17, "IDEAS", "پیشنهاد پروژه", C.GREEN)
    print(f"  {C.DIM}┃{C.RESET}")

    header("SYSTEM")
    item(4, "EVOLVE", "خودارتقایی · AI", C.PINK)
    item(5, "DATA", "خروجی · snapshot", C.ORANGE)
    item(6, "SERVERS", "API · وب · IDE", C.BLUE)
    item(8, "BOOKMARKS", "ذخیره‌شده‌ها", C.GRAY)
    item(9, "SETTINGS", "تم · تنظیمات", C.GRAY)
    print(f"  {C.DIM}┃{C.RESET}")

    header("INTEGRATION")
    item(13, "TOKEN", "GitHub Token", C.ORANGE)
    item(14, "AI-AGENT", "LLM خودکار", C.PINK)
    item(15, "AI-BRIDGE", "پرامپت برای AI", C.PINK)
    item(16, "EXTRAS", "compare · weekly", C.CYAN)
    print(f"  {C.DIM}┃{C.RESET}")

    header("INFRA")
    item(18, "CLEANUP", "پاک‌سازی", C.RED)
    item(19, "NETWORK", "شبکه · provider", C.BLUE)
    item(20, "PROXY", "پروکسی · tasks", C.BLUE)
    item(21, "TUNNEL", "سرور · SSH", C.BLUE)
    item(22, "CLOUD", "auto cloud", C.BLUE)
    item(23, "SNAPSHOT", "export برای AI", C.ORANGE)
    item(24, "HELP", "راهنما", C.GRAY)
    print(f"  {C.DIM}┃{C.RESET}")

    print(f"  {C.DIM}┃{C.RESET} {C.M}{C.BOLD}◆{C.RESET} "
          f"{C.WHITE}{C.BOLD}AUTO{C.RESET}  "
          f"{C.GRAY}خودش تصمیم می‌گیرد چه کار کند{C.RESET}")
    print(f"  {C.PURPLE}{C.BOLD}  ◆ AUTO{C.RESET}  "
          f"{C.GRAY}خودش تصمیم می‌گیرد چه کار کند{C.RESET}")
    print(f"  {C.GREEN}{C.BOLD}  ★ SMART{C.RESET} "
          f"{C.GRAY}تایپ آزاد — خودش می‌فهمد{C.RESET}")
    print(f"  {C.DIM}┃{C.RESET} {C.RED}✕{C.RESET} "
          f"{C.WHITE}{C.BOLD}EXIT{C.RESET}   {C.GRAY}خروج{C.RESET}")
    print(f"  {C.DIM}┗{'━' * 50}{C.RESET}")
    print()

    return ask("انتخاب")


# ═══════════════════════════════════════════════════
#  اجراها
# ═══════════════════════════════════════════════════

def run_evocmd(*args):
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
#  زیرمنوها
# ═══════════════════════════════════════════════════

def sub_ask():
    while True:
        banner()
        print(f"  {C.CYAN}{C.BOLD}┃ ASK{C.RESET} {C.DIM}سؤال · جستجو · کاوش{C.RESET}\n")
        item(1, "SEARCH", "جستجو در منابع")
        item(2, "ASK (RAG)", "پرسش + پاسخ")
        item(3, "RELATED", "پکیج مرتبط")
        item(4, "GRAPH PATH", "مسیر بین دو پکیج")
        item(5, "ADVISOR", "مشاور پکیج")
        item(6, "IDEAS", "پیشنهاد پروژه")
        item(7, "COMPARE", "مقایسه دو پکیج")
        item(8, "RAG v2", "چندمرحله‌ای")
        item(0, "BACK", "")
        print(f"  {C.DIM}┗{'━' * 50}{C.RESET}\n")
        c = ask("انتخاب")
        if c in (None, "0"):
            return
        elif c == "1":
            q = ask("جستجو")
            if q: run_evocmd("search", q); pause()
        elif c == "2":
            q = ask("سؤال")
            if q: run_evocmd("ask", q); pause()
        elif c == "3":
            p = ask("پکیج")
            if p: run_evocmd("related", p); pause()
        elif c == "4":
            a = ask("از"); b = ask("به")
            if a and b: run_evocmd("graph-path", a, b); pause()
        elif c == "5":
            run_py("-c", """
import sys; sys.path.insert(0, "features")
from evoscanner_v2 import KB
import advisor
print("کارها:")
advisor.show_tasks()
t = input("\\nکار: ").strip()
if t: advisor.advise(KB(), t)
""")
            pause()
        elif c == "6":
            run_py("-c", """
import sys; sys.path.insert(0, "features")
from evoscanner_v2 import KB
import project_ideas
project_ideas.show(KB(), n=5)
""")
            pause()
        elif c == "7":
            a = ask("پکیج 1"); b = ask("پکیج 2")
            if a and b:
                run_py("-c", f"""
import sys; sys.path.insert(0, "features")
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
        banner()
        print(f"  {C.YELLOW}{C.BOLD}┃ GET{C.RESET} {C.DIM}جذب و جمع‌آوری{C.RESET}\n")
        item(1, "RUN", "چرخه کشف")
        item(2, "ENRICH", "README کامل")
        item(3, "REBUILD", "گراف + دسته")
        item(4, "HUNTER", "کوئری هوشمند")
        item(5, "SOURCES", "منابع جدید")
        item(6, "TOKEN", "وضعیت GitHub")
        item(7, "AUTO", "۵ چرخه خودکار")
        item(8, "BULK-10", "۱۰ چرخه")
        item(0, "BACK", "")
        print(f"  {C.DIM}┗{'━' * 50}{C.RESET}\n")
        c = ask("انتخاب")
        if c in (None, "0"): return
        elif c == "1":
            n = ask("تعداد", "2")
            run_evocmd("reset-health"); run_evocmd("run", n); run_evocmd("rebuild")
            pause()
        elif c == "2":
            n = ask("تعداد", "50")
            run_evocmd("enrich", n); run_evocmd("rebuild")
            pause()
        elif c == "3":
            run_evocmd("rebuild"); pause()
        elif c == "4":
            run_evocmd("learn"); pause()
        elif c == "5":
            run_evocmd("offline"); pause()
        elif c == "6":
            run_py("auth.py", "status"); pause()
        elif c == "7":
            for i in range(5):
                print(f"\n  {C.CYAN}cycle {i+1}/5{C.RESET}")
                run_evocmd("run", "1")
                if i < 4: time.sleep(30)
            run_evocmd("rebuild"); pause()
        elif c == "8":
            for i in range(10):
                print(f"\n  {C.CYAN}cycle {i+1}/10{C.RESET}")
                run_evocmd("run", "1")
                if i < 9: time.sleep(20)
            run_evocmd("rebuild"); pause()


def sub_learn():
    while True:
        banner()
        print(f"  {C.GREEN}{C.BOLD}┃ LEARN{C.RESET} {C.DIM}یادگیری و دانش{C.RESET}\n")
        item(1, "EXTRACT", "استخراج دانش")
        item(2, "STATS", "آمار")
        item(3, "PATH", "مسیر یادگیری")
        item(4, "GOALS", "اهداف آماده")
        item(5, "TECH", "تکنیک‌ها")
        item(6, "SNIPPETS", "قطعات کد")
        item(7, "GRAPHICS", "گزارش گرافیک")
        item(0, "BACK", "")
        print(f"  {C.DIM}┗{'━' * 50}{C.RESET}\n")
        c = ask("انتخاب")
        if c in (None, "0"): return
        elif c == "1": run_py("learn.py", "extract"); pause()
        elif c == "2": run_py("learn.py", "stats"); pause()
        elif c == "3":
            t = ask("موضوع", "graphics")
            run_py("learn.py", "path", t); pause()
        elif c == "4":
            g = ask("هدف (backend/ml/data/devops/security)", "backend")
            run_evocmd("goal", g); pause()
        elif c == "5": run_py("learn.py", "tech"); pause()
        elif c == "6": run_py("learn.py", "snippet"); pause()
        elif c == "7": run_py("learn.py", "graphics"); pause()


def sub_evolve():
    while True:
        banner()
        print(f"  {C.PINK}{C.BOLD}┃ EVOLVE{C.RESET} {C.DIM}خودارتقایی{C.RESET}\n")
        item(1, "AGENTS", "۴ ایجنت اصلی")
        item(2, "META", "Meta Agent خودبازنویس")
        item(3, "CHAIN", "Agent Chain")
        item(4, "AI-AGENT", "LLM داخل (نیاز به کلید)")
        item(5, "SNAPSHOT", "پشتیبان برای AI")
        item(6, "METADATA", "استخراج فراداده")
        item(7, "RAG2", "RAG چندمرحله‌ای")
        item(8, "CAPABILITY", "توانایی دستگاه")
        item(9, "ANALYZE", "تحلیل کامل پروژه")
        item(0, "BACK", "")
        print(f"  {C.DIM}┗{'━' * 50}{C.RESET}\n")
        c = ask("انتخاب")
        if c in (None, "0"): return
        elif c == "1":
            run_evocmd("agents"); run_evocmd("agents-report"); pause()
        elif c == "2":
            run_py("feature_meta.py", "cycle"); pause()
        elif c == "3":
            run_py("feature_agent_chain.py", "run"); pause()
        elif c == "4":
            print(f"\n  {C.DIM}کلید AI رو از منوی اصلی [14] تنظیم کن{C.RESET}\n")
            pause()
        elif c == "5":
            run_py("feature_snapshot.py", "build"); pause()
        elif c == "6":
            run_py("feature_metadata.py", "extract"); pause()
        elif c == "7":
            q = ask("سؤال")
            if q: run_py("feature_rag_v2.py", q); pause()
        elif c == "8":
            run_py("feature_capability.py"); pause()
        elif c == "9":
            run_py("-c", """
import sys; sys.path.insert(0, ".")
import feature_meta
p = feature_meta.analyze_project()
print(f"Files: {len(p['files'])}")
print(f"Lines: {p['total_lines']:,}")
print(f"Issues: {len(p['issues'])}")
print(f"Opportunities:")
for o in p.get("opportunities", []):
    print(f"  • {o['type']}: {o['detail']}")
""")
            pause()


def sub_manage():
    while True:
        banner()
        print(f"  {C.BLUE}{C.BOLD}┃ MANAGE{C.RESET} {C.DIM}مدیریت{C.RESET}\n")
        item(1, "WEB", "رابط وب پایگاه")
        item(2, "API", "سرور API")
        item(3, "GRAPH-WEB", "نمای گراف (SVG)")
        item(4, "EXPORT", "خروجی JSON/CSV/MD")
        item(5, "STATS", "آمار کامل")
        item(6, "CLEANUP", "گزارش سلامت")
        item(7, "NETWORK", "تست شبکه")
        item(8, "SETTINGS", "تنظیمات")
        item(0, "BACK", "")
        print(f"  {C.DIM}┗{'━' * 50}{C.RESET}\n")
        c = ask("انتخاب")
        if c in (None, "0"): return
        elif c == "1": run_evocmd("web"); pause()
        elif c == "2":
            import subprocess as sp
            sp.run([sys.executable, "api.py"], cwd=str(BASE))
        elif c == "3": run_evocmd("graphweb"); pause()
        elif c == "4": run_evocmd("export"); pause()
        elif c == "5": run_evocmd("stats"); pause()
        elif c == "6": run_py("feature_cleanup.py", "report"); pause()
        elif c == "7": run_py("feature_net.py", "report"); pause()
        elif c == "8":
            print(f"\n  {C.DIM}تنظیمات: تغییر تم، confirm، reset{C.RESET}\n")
            pause()


def sub_graph():
    while True:
        banner()
        print(f"  {C.BLUE}{C.BOLD}┃ GRAPH{C.RESET} {C.DIM}کاوش گراف{C.RESET}\n")
        item(1, "TOP", "۲۵ نود برتر")
        item(2, "RELATED", "مرتبط‌ها")
        item(3, "PEERS", "هم‌دسته")
        item(4, "NEIGHBORS", "همسایه‌ها")
        item(5, "PATH", "کوتاه‌ترین مسیر")
        item(6, "CAT", "فیلتر دسته")
        item(0, "BACK", "")
        print(f"  {C.DIM}┗{'━' * 50}{C.RESET}\n")
        c = ask("انتخاب")
        if c in (None, "0"): return
        elif c == "1": run_evocmd("top", "25"); pause()
        elif c == "2":
            p = ask("پکیج")
            if p: run_evocmd("graph-related", p); pause()
        elif c == "3":
            p = ask("پکیج")
            if p: run_evocmd("graph-peers", p); pause()
        elif c == "4":
            p = ask("نود")
            if p: run_evocmd("graph-neighbors", p); pause()
        elif c == "5":
            a = ask("از"); b = ask("به")
            if a and b: run_evocmd("graph-path", a, b); pause()
        elif c == "6":
            cat = ask("دسته")
            if cat: run_evocmd("cat", cat); pause()


def smart_mode():
    """حالت هوشمند — تایپ آزاد"""
    clear()
    print(f"\n  {C.PURPLE}{C.BOLD}◆ SMART MODE{C.RESET}\n")
    print(f"  {C.DIM}هرچی می‌خواهی بگو — خودش می‌فهمد{C.RESET}")
    print(f"  {C.DIM}مثال: search fastapi | graph django | اجرا ۳ | مشاور{C.RESET}\n")

    text = ask("چی می‌خواهی؟")
    if not text:
        return

    parts = text.split()
    first = parts[0].lower()

    # نقشه‌ها
    if first in ("search", "s", "جستجو", "سرچ", "بگرد"):
        q = " ".join(parts[1:]) or ask("جستجو")
        if q: run_evocmd("search", q)
    elif first in ("ask", "a", "بپرس", "سوال", "سؤال", "پرسش"):
        q = " ".join(parts[1:]) or ask("سؤال")
        if q: run_evocmd("ask", q)
    elif first in ("related", "r", "مرتبط"):
        p = " ".join(parts[1:]) or ask("پکیج")
        if p: run_evocmd("related", p)
    elif first in ("graph", "g", "گراف"):
        p = " ".join(parts[1:]) or ask("موجودیت")
        if p: run_evocmd("graph-related", p)
    elif first in ("run", "cycle", "چرخه", "اجرا"):
        n = parts[1] if len(parts) > 1 else "2"
        run_evocmd("reset-health"); run_evocmd("run", n); run_evocmd("rebuild")
    elif first in ("extract", "استخراج"):
        run_py("learn.py", "extract")
    elif first in ("stats", "آمار"):
        run_evocmd("stats")
    elif first in ("snapshot", "پشتیبان"):
        run_py("feature_snapshot.py", "build")
    elif first in ("capability", "توان"):
        run_py("feature_capability.py")
    elif first in ("meta", "متا"):
        run_py("feature_meta.py", "cycle")
    elif first in ("agents", "ایجنت"):
        run_evocmd("agents")
    elif first in ("help", "h", "راهنما"):
        show_help()
        return
    else:
        # پیش‌فرض: جستجو
        print(f"\n  {C.DIM}جستجو می‌کنم...{C.RESET}\n")
        run_evocmd("search", text)

    pause()


def show_help():
    clear()
    print(f"\n  {C.PURPLE}{C.BOLD}◆ HELP{C.RESET}\n")
    print(f"  {C.CYAN}SMART MODE{C.RESET} — تایپ آزاد:")
    print(f"    search fastapi")
    print(f"    graph asyncio")
    print(f"    اجرا 3")
    print(f"    مشاور پکیج")
    print(f"    پشتیبان")
    print(f"    متا")
    print(f"\n  {C.YELLOW}GET{C.RESET} — جذب منابع (chرخه، enrich، rebuild)")
    print(f"  {C.GREEN}LEARN{C.RESET} — یادگیری (extract، مسیر، هدف)")
    print(f"  {C.PINK}EVOLVE{C.RESET} — خودارتقایی (AI Agent، Meta)")
    print(f"  {C.BLUE}MANAGE{C.RESET} — مدیریت (API، وب، خروجی)")
    print(f"  {C.CYAN}ASK{C.RESET} — کاوش (search، ask، advisor)")
    pause()


# ═══════════════════════════════════════════════════
#  حلقه اصلی
# ═══════════════════════════════════════════════════

def main():
    while True:
        try:
            c = main_menu()
            if c is None or c in ("0", "q", "exit", "quit", "خروج", "خروج"):
                clear()
                print(f"\n  {C.CYAN}Bedrood 👋{C.RESET}\n")
                return

            c = c.strip().lower()

            if c == "1" or c in ("ask", "سوال"): sub_ask()
            elif c == "2" or c in ("get", "جذب"): sub_get()
            elif c == "3" or c in ("learn", "یاد"): sub_learn()
            elif c == "4" or c in ("evolve", "ارتقا"): sub_evolve()
            elif c == "5" or c in ("data", "داده"): sub_manage()
            elif c == "6" or c in ("servers", "سرور"): sub_manage()
            elif c == "7" or c in ("graph", "گراف"): sub_graph()
            elif c in ("a", "auto", "اتو", "autopilot", "خودکار", "◆"):
                run_py("feature_autopilot.py")
            elif c in ("smart", "s", "هوش", "★"):
                smart_mode()
            elif c in ("h", "help", "راهنما", "24"):
                show_help()
            else:
                # هر چیز دیگری → SMART MODE
                parts = c.split()
                if parts:
                    # دستور مستقیم
                    first = parts[0]
                    if first in ("search", "s", "ask", "a", "related", "r",
                                 "graph", "g", "run", "cycle", "stats", "snapshot",
                                 "meta", "agents", "extract", "capability"):
                        smart_mode()
                    else:
                        print(f"\n  {C.DIM}نمی‌شناسم: {c}{C.RESET}")
                        print(f"  {C.DIM}به SMART MODE می‌روم...{C.RESET}\n")
                        time.sleep(1)
                        smart_mode()

        except KeyboardInterrupt:
            print()
            continue
        except Exception as e:
            print(f"\n  {C.RED}خطا: {e}{C.RESET}\n")
            pause()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        clear()
        print("\nBye\n")

