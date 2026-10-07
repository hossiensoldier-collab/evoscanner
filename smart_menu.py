"""Smart Menu v5 — 5 گزینه + روتر هوشمند"""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

BASE = Path.home() / "evoscanner"

C = {
    "R": "\033[0;31m", "G": "\033[0;32m", "Y": "\033[1;33m",
    "B": "\033[0;34m", "M": "\033[0;35m", "Cy": "\033[0;36m",
    "W": "\033[1;37m", "D": "\033[0m",
    "Bold": "\033[1m", "Dim": "\033[2m",
}


def clear():
    os.system("clear")


def ask(p, default=""):
    try:
        s = input(f"{C['Bold']}  > {C['D']}{p}"
                  + (f" [{default}]" if default else "") + ": ").strip()
        return s or default
    except (EOFError, KeyboardInterrupt):
        return ""


def pause():
    try:
        input(f"\n{C['Dim']}  Enter...{C['D']}")
    except (EOFError, KeyboardInterrupt):
        pass


def run_evocmd(*args):
    """اجرای دستور از evoscanner_v2"""
    try:
        subprocess.run([sys.executable, "evoscanner_v2.py"] + list(args),
                       cwd=str(BASE))
    except KeyboardInterrupt:
        pass


def run_py(script, *args):
    """اجرای یک اسکریپت پایتون"""
    try:
        subprocess.run([sys.executable, script] + list(args),
                       cwd=str(BASE))
    except KeyboardInterrupt:
        pass


# ═══════════════════════════════════════════════════
#  کارت‌های اصلی — ۵ گروه
# ═══════════════════════════════════════════════════

def stats():
    """آمار سریع"""
    out = {"src": 0, "gr": 0, "tech": 0, "snips": 0}
    try:
        import sqlite3
        db = sqlite3.connect(BASE / "knowledge.db")
        out["src"] = db.execute(
            "SELECT COUNT(*) FROM resources").fetchone()[0]
        for k, t in [("tech", "techniques"), ("snips", "snippets")]:
            try:
                out[k] = db.execute(
                    f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            except Exception:
                pass
        db.close()
    except Exception:
        pass
    try:
        g = json.loads((BASE / "graph.json").read_text())
        out["gr"] = sum(1 for v in g["nodes"].values()
                        if v.get("type") == "entity")
    except Exception:
        pass
    return out


def banner():
    clear()
    s = stats()
    print()
    print(C["Cy"] + "  ╔══════════════════════════════════════════════════╗" + C["D"])
    print(C["Cy"] + "  ║" + C["D"] +
          C["Bold"] + C["W"] +
          "           E V O S C A N N E R   v 5 . 0          " +
          C["D"] + C["Cy"] + "║" + C["D"])
    print(C["Cy"] + "  ╚══════════════════════════════════════════════════╝" + C["D"])
    print()
    print(f"  {C['Dim']}src {C['D']}{C['Y']}{s['src']:>4d}{C['D']}"
          f"  {C['Dim']}graph {C['D']}{C['Cy']}{s['gr']:>4d}{C['D']}"
          f"  {C['Dim']}tech {C['D']}{C['G']}{s['tech']:>4d}{C['D']}"
          f"  {C['Dim']}snips {C['D']}{C['G']}{s['snips']:>4d}{C['D']}")
    print()


def main_menu():
    banner()
    print(f"  {C['Bold']}{C['Cy']}[1]{C['D']}  {C['Bold']}ASK{C['D']}      "
          f"{C['Dim']}سؤال، جستجو، کاوش، مشاور{C['D']}")
    print(f"  {C['Bold']}{C['Cy']}[2]{C['D']}  {C['Bold']}GET{C['D']}      "
          f"{C['Dim']}جذب منابع، چرخه، enrich{C['D']}")
    print(f"  {C['Bold']}{C['Cy']}[3]{C['D']}  {C['Bold']}LEARN{C['D']}    "
          f"{C['Dim']}یادگیری، مسیر، دانش{C['D']}")
    print(f"  {C['Bold']}{C['Cy']}[4]{C['D']}  {C['Bold']}EVOLVE{C['D']}   "
          f"{C['Dim']}خودارتقایی، AI Agent، Meta{C['D']}")
    print(f"  {C['Bold']}{C['Cy']}[5]{C['D']}  {C['Bold']}MANAGE{C['D']}   "
          f"{C['Dim']}سرور، تنظیمات، پاک‌سازی{C['D']}")
    print()
    print(f"  {C['Dim']}[s]{C['D']}  {C['Dim']}جستجوی هوشمند (تایپ آزاد){C['D']}")
    print(f"  {C['Dim']}[h]{C['D']}  {C['Dim']}راهنما{C['D']}")
    print(f"  {C['Dim']}[0]{C['D']}  {C['Dim']}خروج{C['D']}")
    print()
    print(C["Dim"] + "  " + "─" * 52 + C["D"])
    return ask("انتخاب")


# ═══════════════════════════════════════════════════
#  Smart Router — جستجوی هوشمند
# ═══════════════════════════════════════════════════

ROUTES = {
    # ASK
    "ask":       ("ask", ["[1]", "ASK"]),
    "search":    ("search", ["[1]", "ASK"]),
    "جستجو":     ("search", ["[1]", "ASK"]),
    "سرچ":       ("search", ["[1]", "ASK"]),
    "related":   ("related", ["[1]", "ASK"]),
    "مرتبط":     ("related", ["[1]", "ASK"]),
    "graph":     ("graph", ["[1]", "ASK"]),
    "گراف":      ("graph", ["[1]", "ASK"]),
    "advisor":   ("advisor", ["[1]", "ASK"]),
    "مشاور":     ("advisor", ["[1]", "ASK"]),
    "ideas":     ("ideas", ["[1]", "ASK"]),
    "پروژه":     ("ideas", ["[1]", "ASK"]),
    "compare":   ("compare", ["[1]", "ASK"]),
    "مقایسه":    ("compare", ["[1]", "ASK"]),

    # GET
    "run":       ("run", ["[2]", "GET"]),
    "cycle":     ("cycle", ["[2]", "GET"]),
    "چرخه":      ("cycle", ["[2]", "GET"]),
    "collect":   ("collect", ["[2]", "GET"]),
    "جمع":       ("collect", ["[2]", "GET"]),
    "enrich":    ("enrich", ["[2]", "GET"]),
    "token":     ("token", ["[2]", "GET"]),
    "توکن":      ("token", ["[2]", "GET"]),
    "hunter":    ("hunter", ["[2]", "GET"]),
    "شکار":      ("hunter", ["[2]", "GET"]),
    "sources":   ("sources", ["[2]", "GET"]),
    "منابع":     ("sources", ["[2]", "GET"]),

    # LEARN
    "goal":      ("goal", ["[3]", "LEARN"]),
    "هدف":       ("goal", ["[3]", "LEARN"]),
    "path":      ("path", ["[3]", "LEARN"]),
    "مسیر":      ("path", ["[3]", "LEARN"]),
    "extract":   ("extract", ["[3]", "LEARN"]),
    "استخراج":   ("extract", ["[3]", "LEARN"]),
    "learn":     ("learn", ["[3]", "LEARN"]),
    "یادگیری":   ("learn", ["[3]", "LEARN"]),
    "snippet":   ("snippet", ["[3]", "LEARN"]),
    "weekly":    ("weekly", ["[3]", "LEARN"]),
    "هفتگی":     ("weekly", ["[3]", "LEARN"]),

    # EVOLVE
    "agent":     ("agent", ["[4]", "EVOLVE"]),
    "ایجنت":     ("agent", ["[4]", "EVOLVE"]),
    "ai":        ("ai", ["[4]", "EVOLVE"]),
    "meta":      ("meta", ["[4]", "EVOLVE"]),
    "upgrade":   ("upgrade", ["[4]", "EVOLVE"]),
    "ارتقا":     ("upgrade", ["[4]", "EVOLVE"]),
    "snapshot":  ("snapshot", ["[4]", "EVOLVE"]),
    "پشتیبان":   ("snapshot", ["[4]", "EVOLVE"]),
    "bridge":    ("bridge", ["[4]", "EVOLVE"]),
    "selfmod":   ("selfmod", ["[4]", "EVOLVE"]),
    "capability":("capability", ["[4]", "EVOLVE"]),
    "توانایی":   ("capability", ["[4]", "EVOLVE"]),

    # MANAGE
    "server":    ("server", ["[5]", "MANAGE"]),
    "سرور":      ("server", ["[5]", "MANAGE"]),
    "api":       ("server", ["[5]", "MANAGE"]),
    "web":       ("server", ["[5]", "MANAGE"]),
    "cleanup":   ("cleanup", ["[5]", "MANAGE"]),
    "پاک":       ("cleanup", ["[5]", "MANAGE"]),
    "health":    ("cleanup", ["[5]", "MANAGE"]),
    "network":   ("network", ["[5]", "MANAGE"]),
    "شبکه":      ("network", ["[5]", "MANAGE"]),
    "proxy":     ("proxy", ["[5]", "MANAGE"]),
    "پروکسی":    ("proxy", ["[5]", "MANAGE"]),
    "tunnel":    ("tunnel", ["[5]", "MANAGE"]),
    "تونل":      ("tunnel", ["[5]", "MANAGE"]),
    "settings":  ("settings", ["[5]", "MANAGE"]),
    "تنظیمات":   ("settings", ["[5]", "MANAGE"]),
    "theme":     ("settings", ["[5]", "MANAGE"]),
    "export":    ("export", ["[5]", "MANAGE"]),
    "خروجی":     ("export", ["[5]", "MANAGE"]),
    "data":      ("data", ["[5]", "MANAGE"]),
    "داده":      ("data", ["[5]", "MANAGE"]),
    "help":      ("help", ["[5]", "MANAGE"]),
    "راهنما":    ("help", ["[5]", "MANAGE"]),
}


def route(query):
    """تشخیص intent از متن آزاد"""
    q = query.lower().strip()
    tokens = re.split(r"\s+", q)

    # چک مستقیم
    if q in ROUTES:
        return ROUTES[q]

    # چک token به token
    for t in tokens:
        if t in ROUTES:
            return ROUTES[t]

    # چک partial match
    for key, val in ROUTES.items():
        if key in q and len(key) >= 3:
            return val

    return None


# ═══════════════════════════════════════════════════
#  زیرمنوهای ASK
# ═══════════════════════════════════════════════════

def sub_ask():
    while True:
        banner()
        print(f"  {C['Bold']}{C['Cy']}ASK{C['D']}  {C['Dim']}سؤال، جستجو، کاوش{C['D']}")
        print(C["Dim"] + "  " + "─" * 52 + C["D"])
        print(f"  {C['Y']}[1]{C['D']}  جستجو در منابع")
        print(f"  {C['Y']}[2]{C['D']}  پرسش (RAG)")
        print(f"  {C['Y']}[3]{C['D']}  پکیج مرتبط")
        print(f"  {C['Y']}[4]{C['D']}  مسیر گراف")
        print(f"  {C['Y']}[5]{C['D']}  کاوش گراف (submenu)")
        print(f"  {C['Y']}[6]{C['D']}  مشاور پکیج")
        print(f"  {C['Y']}[7]{C['D']}  پیشنهاد پروژه")
        print(f"  {C['Y']}[8]{C['D']}  مقایسه دو پکیج")
        print(f"  {C['Y']}[9]{C['D']}  پیشنهاد import")
        print(f"  {C['Y']}[10]{C['D']} RAG v2 (چندمرحله‌ای)")
        print(f"  {C['Y']}[11]{C['D']} پرسش مستقیم با یک خط")
        print(f"  {C['Y']}[0]{C['D']}  بازگشت")
        print()
        c = ask("انتخاب")

        if c == "0":
            return
        elif c == "1":
            q = ask("جستجو")
            if q:
                run_evocmd("search", q)
                pause()
        elif c == "2":
            q = ask("سؤال")
            if q:
                run_evocmd("ask", q)
                pause()
        elif c == "3":
            p = ask("پکیج")
            if p:
                run_evocmd("related", p)
                pause()
        elif c == "4":
            a = ask("از")
            b = ask("به")
            if a and b:
                run_evocmd("graph-path", a, b)
                pause()
        elif c == "5":
            run_py("feature_help.py")
        elif c == "6":
            print()
            print(f"  {C['Dim']}مثال: web framework, async, testing{C['D']}")
            t = ask("کار")
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
        elif c == "7":
            print()
            run_py("-c", """
import sys
sys.path.insert(0, "features")
from evoscanner_v2 import KB
import project_ideas
project_ideas.show(KB(), n=5)
""")
            pause()
        elif c == "8":
            a = ask("پکیج 1")
            b = ask("پکیج 2")
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
        elif c == "9":
            f = ask("فایل", str(Path.home() / "project.py"))
            print()
            run_py("-c", f"""
import sys
sys.path.insert(0, "features")
from evoscanner_v2 import KB
import compare
# استفاده از suggest endpoint
from ai_bridge import project_state
import json
from pathlib import Path
try:
    code = Path({f!r}).read_text()
    print(f"File: {f}")
    print(f"Size: {{len(code)}} chars")
except Exception as e:
    print(f"Error: {{e}}")
""")
            pause()
        elif c == "10":
            q = ask("سؤال")
            if q:
                run_py("feature_rag_v2.py", q)
                pause()
        elif c == "11":
            q = ask("سؤال")
            if q:
                run_evocmd("ask", q)
                pause()


# ═══════════════════════════════════════════════════
#  زیرمنوهای GET
# ═══════════════════════════════════════════════════

def sub_get():
    while True:
        banner()
        print(f"  {C['Bold']}{C['Cy']}GET{C['D']}  {C['Dim']}جذب و جمع‌آوری{C['D']}")
        print(C["Dim"] + "  " + "─" * 52 + C["D"])
        print(f"  {C['Y']}[1]{C['D']}  چرخه کشف (run)")
        print(f"  {C['Y']}[2]{C['D']}  دریافت README (enrich)")
        print(f"  {C['Y']}[3]{C['D']}  بازسازی گراف (rebuild)")
        print(f"  {C['Y']}[4]{C['D']}  Hunter (کوئری هوشمند)")
        print(f"  {C['Y']}[5]{C['D']}  منابع گسترده (PyPI, arXiv, ...)")
        print(f"  {C['Y']}[6]{C['D']}  توکن GitHub")
        print(f"  {C['Y']}[7]{C['D']}  چرخه خودکار (5 چرخه)")
        print(f"  {C['Y']}[8]{C['D']}  کشف دسته جدید")
        print(f"  {C['Y']}[9]{C['D']}  پیشنهاد کوئری برای شکاف")
        print(f"  {C['Y']}[10]{C['D']} دانلود انبوه ۱۰ چرخه")
        print(f"  {C['Y']}[0]{C['D']}  بازگشت")
        print()
        c = ask("انتخاب")

        if c == "0":
            return
        elif c == "1":
            n = ask("تعداد", "2")
            run_evocmd("reset-health")
            run_evocmd("run", n)
            run_evocmd("rebuild")
            pause()
        elif c == "2":
            n = ask("تعداد", "50")
            run_evocmd("enrich", n)
            run_evocmd("rebuild")
            pause()
        elif c == "3":
            run_evocmd("rebuild")
            pause()
        elif c == "4":
            run_evocmd("learn")
            pause()
        elif c == "5":
            run_evocmd("offline")
            pause()
        elif c == "6":
            run_py("auth.py", "status")
            pause()
        elif c == "7":
            print(f"\n  {C['Dim']}۵ چرخه با ۳۰ ثانیه فاصله...{C['D']}\n")
            for i in range(5):
                print(f"  {C['Cy']}cycle {i+1}/5{C['D']}")
                run_evocmd("run", "1")
                if i < 4:
                    print(f"  {C['Dim']}wait 30s...{C['D']}")
                    time.sleep(30)
            run_evocmd("rebuild")
            pause()
        elif c == "8":
            run_evocmd("discover", "8")
            pause()
        elif c == "9":
            run_evocmd("suggest")
            pause()
        elif c == "10":
            print(f"\n  {C['Dim']}۱۰ چرخه متوالی...{C['D']}\n")
            for i in range(10):
                print(f"  {C['Cy']}cycle {i+1}/10{C['D']}")
                run_evocmd("run", "1")
                if i < 9:
                    time.sleep(20)
            run_evocmd("rebuild")
            pause()


# ═══════════════════════════════════════════════════
#  زیرمنوهای LEARN
# ═══════════════════════════════════════════════════

def sub_learn():
    while True:
        banner()
        print(f"  {C['Bold']}{C['Cy']}LEARN{C['D']}  {C['Dim']}یادگیری و دانش{C['D']}")
        print(C["Dim"] + "  " + "─" * 52 + C["D"])
        print(f"  {C['Y']}[1]{C['D']}  استخراج دانش (extract)")
        print(f"  {C['Y']}[2]{C['D']}  آمار دانش")
        print(f"  {C['Y']}[3]{C['D']}  مسیر یادگیری (۴ سطح)")
        print(f"  {C['Y']}[4]{C['D']}  اهداف (backend, ml, ...)")
        print(f"  {C['Y']}[5]{C['D']}  تکنیک‌ها")
        print(f"  {C['Y']}[6]{C['D']}  Code snippets")
        print(f"  {C['Y']}[7]{C['D']}  گزارش گرافیک")
        print(f"  {C['Y']}[8]{C['D']}  گزارش هفتگی")
        print(f"  {C['Y']}[9]{C['D']}  افزودن snippet شخصی")
        print(f"  {C['Y']}[10]{C['D']} چرخه کامل یادگیری (extract + graphics)")
        print(f"  {C['Y']}[11]{C['D']} همه اهداف")
        print(f"  {C['Y']}[0]{C['D']}  بازگشت")
        print()
        c = ask("انتخاب")

        if c == "0":
            return
        elif c == "1":
            run_py("learn.py", "extract")
            pause()
        elif c == "2":
            run_py("learn.py", "stats")
            pause()
        elif c == "3":
            t = ask("موضوع", "graphics")
            run_py("learn.py", "path", t)
            pause()
        elif c == "4":
            g = ask("هدف (backend/ml/data/devops/security)")
            if g:
                run_evocmd("goal", g)
                pause()
        elif c == "5":
            run_py("learn.py", "tech")
            pause()
        elif c == "6":
            run_py("learn.py", "snippet")
            pause()
        elif c == "7":
            run_py("learn.py", "graphics")
            pause()
        elif c == "8":
            print()
            run_py("-c", """
import sys
sys.path.insert(0, "features")
from evoscanner_v2 import KB
import weekly
weekly.generate(KB())
""")
            pause()
        elif c == "9":
            print(f"\n  {C['Dim']}چند خط بنویس، خط خالی = پایان{C['D']}\n")
            lines = []
            while True:
                try:
                    l = input("  > ")
                except (EOFError, KeyboardInterrupt):
                    break
                if not l:
                    break
                lines.append(l)
            if lines:
                title = ask("عنوان", "snippet")
                print("  ✓ ذخیره شد")
            pause()
        elif c == "10":
            run_py("learn.py", "extract")
            pause()
        elif c == "11":
            run_evocmd("goals")
            pause()


# ═══════════════════════════════════════════════════
#  زیرمنوهای EVOLVE
# ═══════════════════════════════════════════════════

def sub_evolve():
    while True:
        banner()
        print(f"  {C['Bold']}{C['Cy']}EVOLVE{C['D']}  {C['Dim']}خودارتقایی{C['D']}")
        print(C["Dim"] + "  " + "─" * 52 + C["D"])
        print(f"  {C['Y']}[1]{C['D']}  ۴ ایجنت اصلی")
        print(f"  {C['Y']}[2]{C['D']}  Meta Agent (خودبازنویس)")
        print(f"  {C['Y']}[3]{C['D']}  Agent Chain")
        print(f"  {C['Y']}[4]{C['D']}  AI Agent (LLM داخل)")
        print(f"  {C['Y']}[5]{C['D']}  AI Bridge (پرامپت برای AI خارجی)")
        print(f"  {C['Y']}[6]{C['D']}  Self-Upgrade (patch کد)")
        print(f"  {C['Y']}[7]{C['D']}  Metadata extract")
        print(f"  {C['Y']}[8]{C['D']}  RAG v2")
        print(f"  {C['Y']}[9]{C['D']}  Project Snapshot (export برای AI)")
        print(f"  {C['Y']}[10]{C['D']} پیش‌بینی توانایی")
        print(f"  {C['Y']}[11]{C['D']} اجرای چرخه کامل Meta")
        print(f"  {C['Y']}[12]{C['D']} تحلیل کامل پروژه")
        print(f"  {C['Y']}[0]{C['D']}  بازگشت")
        print()
        c = ask("انتخاب")

        if c == "0":
            return
        elif c == "1":
            run_evocmd("agents")
            run_evocmd("agents-report")
            pause()
        elif c == "2":
            run_py("feature_meta.py", "cycle")
            pause()
        elif c == "3":
            run_py("feature_agent_chain.py", "run")
            pause()
        elif c == "4":
            print(f"  {C['Dim']}این منو داخل پنل اصلی است — [14]{C['D']}")
            pause()
        elif c == "5":
            print(f"  {C['Dim']}این منو داخل پنل اصلی است — [15]{C['D']}")
            pause()
        elif c == "6":
            print(f"  {C['Dim']}این منو داخل پنل اصلی است — [10]{C['D']}")
            pause()
        elif c == "7":
            run_py("feature_metadata.py", "extract")
            pause()
        elif c == "8":
            q = ask("سؤال")
            if q:
                run_py("feature_rag_v2.py", q)
                pause()
        elif c == "9":
            run_py("feature_snapshot.py", "build")
            pause()
        elif c == "10":
            run_py("feature_capability.py")
            pause()
        elif c == "11":
            run_py("feature_meta.py", "cycle")
            run_py("feature_agent_chain.py", "run")
            pause()
        elif c == "12":
            run_py("-c", """
import sys
sys.path.insert(0, ".")
import feature_meta
p = feature_meta.analyze_project()
print(f"Files: {len(p['files'])}")
print(f"Lines: {p['total_lines']:,}")
print(f"Issues: {len(p['issues'])}")
print(f"Opportunities: {len(p['opportunities'])}")
for o in p["opportunities"]:
    print(f"  • {o['type']}: {o['detail']}")
""")
            pause()


# ═══════════════════════════════════════════════════
#  زیرمنوهای MANAGE
# ═══════════════════════════════════════════════════

def sub_manage():
    while True:
        banner()
        print(f"  {C['Bold']}{C['Cy']}MANAGE{C['D']}  {C['Dim']}مدیریت سیستم{C['D']}")
        print(C["Dim"] + "  " + "─" * 52 + C["D"])
        print(f"  {C['Y']}[1]{C['D']}  سرور API و وب")
        print(f"  {C['Y']}[2]{C['D']}  تونل SSH")
        print(f"  {C['Y']}[3]{C['D']}  شبکه (provider تست)")
        print(f"  {C['Y']}[4]{C['D']}  پروکسی محلی")
        print(f"  {C['Y']}[5]{C['D']}  پاک‌سازی و سلامت")
        print(f"  {C['Y']}[6]{C['D']}  خروجی (JSON/CSV/MD)")
        print(f"  {C['Y']}[7]{C['D']}  تنظیمات و تم")
        print(f"  {C['Y']}[8]{C['D']}  راهنما (Menu Map)")
        print(f"  {C['Y']}[9]{C['D']}  Server Hub (auto cloud)")
        print(f"  {C['Y']}[10]{C['D']} آمار کامل")
        print(f"  {C['Y']}[0]{C['D']}  بازگشت")
        print()
        c = ask("انتخاب")

        if c == "0":
            return
        elif c == "1":
            run_evocmd("web")
            pause()
        elif c == "2":
            print(f"  {C['Dim']}این منو داخل پنل اصلی است — [21]{C['D']}")
            pause()
        elif c == "3":
            run_py("feature_net.py", "report")
            pause()
        elif c == "4":
            print(f"  {C['Dim']}این منو داخل پنل اصلی است — [20]{C['D']}")
            pause()
        elif c == "5":
            run_py("feature_cleanup.py", "report")
            pause()
        elif c == "6":
            run_evocmd("export")
            pause()
        elif c == "7":
            print(f"  {C['Dim']}این منو داخل پنل اصلی است — [9]{C['D']}")
            pause()
        elif c == "8":
            run_py("feature_help.py")
        elif c == "9":
            run_py("auto_setup.py")
        elif c == "10":
            run_evocmd("stats")
            pause()


# ═══════════════════════════════════════════════════
#  حلقه اصلی
# ═══════════════════════════════════════════════════

def smart_search():
    """جستجوی هوشمند — متن آزاد"""
    clear()
    print()
    print(C["Cy"] + "  ╔══════════════════════════════════════════════════╗" + C["D"])
    print(C["Cy"] + "  ║" + C["D"] +
          C["Bold"] + C["W"] +
          "        🔍  جستجوی هوشمند                        " +
          C["D"] + C["Cy"] + "║" + C["D"])
    print(C["Cy"] + "  ╚══════════════════════════════════════════════════╝" + C["D"])
    print()
    print(f"  {C['Dim']}هرچی می‌خواهی تایپ کن: کلمه، دستور، سؤال{C['D']}")
    print(f"  {C['Dim']}مثال: search fastapi | graph | مشاور | run 3{C['D']}")
    print()
    q = ask("چی می‌خواهی؟")
    if not q:
        return

    # اگر با یک کلمه بود، مسیر دهی
    parts = q.split()
    first = parts[0].lower()

    # چک اگر مستقیم یک دستور evoscanner است
    EVOCMDS = ["run", "search", "ask", "related", "graph-path", "top",
               "categories", "path", "goal", "stats", "report",
               "export", "enrich", "rebuild", "suggest", "discover",
               "compress", "learn", "agents", "agents-report"]
    if first in EVOCMDS:
        print(f"\n  {C['G']}→ اجرا: {q}{C['D']}\n")
        run_evocmd(*parts)
        pause()
        return

    # چک routes
    r = route(q)
    if r:
        cmd, group = r
        print(f"\n  {C['G']}→ مسیر: {group[1]} → {cmd}{C['D']}\n")
        time.sleep(0.5)

        if group[1] == "ASK":
            sub_ask()
        elif group[1] == "GET":
            sub_get()
        elif group[1] == "LEARN":
            sub_learn()
        elif group[1] == "EVOLVE":
            sub_evolve()
        elif group[1] == "MANAGE":
            sub_manage()
        return

    # جستجوی معمولی
    print(f"\n  {C['Dim']}جستجو در منابع...{C['D']}\n")
    run_evocmd("search", q)
    pause()


def help_screen():
    clear()
    print()
    print(C["Cy"] + "  ╔══════════════════════════════════════════════════╗" + C["D"])
    print(C["Cy"] + "  ║" + C["D"] +
          C["Bold"] + C["W"] +
          "        📖  راهنمای Smart Menu v5                " +
          C["D"] + C["Cy"] + "║" + C["D"])
    print(C["Cy"] + "  ╚══════════════════════════════════════════════════╝" + C["D"])
    print()
    print(f"  {C['Bold']}{C['Cy']}[1] ASK{C['D']}")
    print(f"      {C['Dim']}سؤال، جستجو، کاوش، مشاور{C['D']}")
    print(f"      {C['Dim']}شامل: search, ask, related, graph, advisor, ideas, compare{C['D']}")
    print()
    print(f"  {C['Bold']}{C['Cy']}[2] GET{C['D']}")
    print(f"      {C['Dim']}جذب منابع از اینترنت{C['D']}")
    print(f"      {C['Dim']}شامل: run, enrich, rebuild, hunter, sources, token{C['D']}")
    print()
    print(f"  {C['Bold']}{C['Cy']}[3] LEARN{C['D']}")
    print(f"      {C['Dim']}یادگیری و دانش{C['D']}")
    print(f"      {C['Dim']}شامل: extract, path, goal, tech, snippets, graphics{C['D']}")
    print()
    print(f"  {C['Bold']}{C['Cy']}[4] EVOLVE{C['D']}")
    print(f"      {C['Dim']}خودارتقایی{C['D']}")
    print(f"      {C['Dim']}شامل: agents, meta, ai, bridge, selfmod, snapshot{C['D']}")
    print()
    print(f"  {C['Bold']}{C['Cy']}[5] MANAGE{C['D']}")
    print(f"      {C['Dim']}مدیریت سرور و تنظیمات{C['D']}")
    print(f"      {C['Dim']}شامل: server, tunnel, network, proxy, cleanup, export{C['D']}")
    print()
    print(f"  {C['Bold']}{C['Cy']}[s] Smart Search{C['D']}")
    print(f"      {C['Dim']}تایپ آزاد — خودش می‌فهمد چه می‌خواهی{C['D']}")
    print()
    print(f"  {C['Dim']}مثال‌های Smart Search:{C['D']}")
    print(f"    • {C['Cy']}search fastapi{C['D']}")
    print(f"    • {C['Cy']}مشاور پکیج{C['D']}")
    print(f"    • {C['Cy']}graph django{C['D']}")
    print(f"    • {C['Cy']}run 3{C['D']}")
    print()
    pause()


def main():
    while True:
        try:
            c = main_menu()

            if c in ("0", "q", "exit", "quit"):
                clear()
                print(f"\n  {C['Cy']}Bedrood 👋{C['D']}\n")
                return
            elif c == "1":
                sub_ask()
            elif c == "2":
                sub_get()
            elif c == "3":
                sub_learn()
            elif c == "4":
                sub_evolve()
            elif c == "5":
                sub_manage()
            elif c in ("s", "S", "search"):
                smart_search()
            elif c in ("h", "H", "help"):
                help_screen()
            else:
                # هر چیز دیگری — جستجوی هوشمند
                r = route(c)
                if r:
                    _, group = r
                    if group[1] == "ASK":
                        sub_ask()
                    elif group[1] == "GET":
                        sub_get()
                    elif group[1] == "LEARN":
                        sub_learn()
                    elif group[1] == "EVOLVE":
                        sub_evolve()
                    elif group[1] == "MANAGE":
                        sub_manage()
                else:
                    # جستجو مستقیم
                    run_evocmd("search", c)
                    pause()

        except KeyboardInterrupt:
            print()
            continue
        except Exception as e:
            print(f"\n  {C['R']}Error: {e}{C['D']}")
            pause()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        clear()
        print("\nBye\n")

