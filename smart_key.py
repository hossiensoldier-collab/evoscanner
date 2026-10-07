"""Smart Key — یک کلمه، همه چیز"""
import os
import subprocess
import sys
from pathlib import Path

BASE = Path.home() / "evoscanner"

# کلمه کلیدی → دستور
KEYS = {
    # جستجو و پرسش
    "s": "search", "search": "search", "جستجو": "search",
    "سرچ": "search", "find": "search",
    "a": "ask", "ask": "ask", "بپرس": "ask",
    "سوال": "ask", "سؤال": "ask", "پرسش": "ask",
    "r": "related", "rel": "related", "مرتبط": "related",
    "g": "graph", "graph": "graph", "گراف": "graph",
    "path": "path", "مسیر": "path",

    # اجرا
    "run": "run", "cycle": "run", "چرخه": "run",
    "e": "enrich", "enrich": "enrich", "غنی": "enrich",
    "rb": "rebuild", "rebuild": "rebuild",

    # یادگیری
    "l": "learn", "learn": "learn", "یاد": "learn",
    "ex": "extract", "extract": "extract", "استخراج": "extract",
    "goal": "goal", "هدف": "goal",
    "h": "help", "help": "help", "راهنما": "help",

    # سیستم
    "stat": "stats", "stats": "stats", "آمار": "stats",
    "ag": "agents", "agents": "agents",
    "snap": "snapshot", "snapshot": "snapshot",
    "cap": "capability", "capability": "capability", "توان": "capability",
    "meta": "meta", "متا": "meta",
    "clean": "cleanup", "cleanup": "cleanup",
    "web": "web", "وب": "web",
    "auth": "auth", "token": "auth", "توکن": "auth",
    "top": "top", "برتر": "top",
    "cats": "categories", "دسته": "categories",
    "exp": "export", "export": "export", "خروجی": "export",
    "rep": "report", "report": "report", "گزارش": "report",
}


def run_cmd(cmd, *args):
    """اجرای دستور از evoscanner_v2"""
    try:
        subprocess.run([sys.executable, "evoscanner_v2.py", cmd] + list(args),
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


def handle(text):
    """تشخیص و اجرا"""
    text = text.strip()
    if not text:
        return

    # تقسیم به کلمات
    parts = text.split()
    first = parts[0].lower()
    rest = parts[1:]

    # اگر با / شروع شد → مستقیم دستور
    if first.startswith("/"):
        cmd = first[1:]
        run_cmd(cmd, *rest)
        return

    # چک کلیدواژه
    if first in KEYS:
        cmd = KEYS[first]
        return dispatch(cmd, rest, text)

    # اگر در KEYS نبود، خودِ کلمه را جستجو کن
    run_cmd("search", text)


def dispatch(cmd, args, full_text):
    """اجرای دستور بر اساس نوع"""
    if cmd == "search":
        q = " ".join(args) if args else input("جستجو: ").strip()
        if q:
            run_cmd("search", q)

    elif cmd == "ask":
        q = " ".join(args) if args else input("سؤال: ").strip()
        if q:
            run_cmd("ask", q)

    elif cmd == "related":
        q = " ".join(args) if args else input("پکیج: ").strip()
        if q:
            run_cmd("related", q)

    elif cmd == "graph":
        q = " ".join(args) if args else input("موجودیت: ").strip()
        if q:
            run_cmd("graph-related", q)

    elif cmd == "path":
        if len(args) >= 2:
            run_cmd("graph-path", args[0], args[1])
        else:
            a = input("از: ").strip()
            b = input("به: ").strip()
            if a and b:
                run_cmd("graph-path", a, b)

    elif cmd == "run":
        n = args[0] if args else "2"
        run_cmd("reset-health")
        run_cmd("run", n)
        run_cmd("rebuild")

    elif cmd == "enrich":
        n = args[0] if args else "30"
        run_cmd("enrich", n)
        run_cmd("rebuild")

    elif cmd == "rebuild":
        run_cmd("rebuild")

    elif cmd == "learn":
        run_py("learn.py", "extract")

    elif cmd == "extract":
        run_py("learn.py", "extract")

    elif cmd == "goal":
        g = args[0] if args else "backend"
        run_cmd("goal", g)

    elif cmd == "stats":
        run_cmd("stats")

    elif cmd == "agents":
        run_cmd("agents")
        run_cmd("agents-report")

    elif cmd == "snapshot":
        run_py("feature_snapshot.py", "build")

    elif cmd == "capability":
        run_py("feature_capability.py")

    elif cmd == "meta":
        run_py("feature_meta.py", "cycle")

    elif cmd == "cleanup":
        run_py("feature_cleanup.py", "report")

    elif cmd == "web":
        run_cmd("web")

    elif cmd == "auth":
        run_py("auth.py", "status")

    elif cmd == "top":
        run_cmd("top", "25")

    elif cmd == "categories":
        run_cmd("categories")

    elif cmd == "export":
        run_cmd("export")

    elif cmd == "report":
        run_cmd("report")

    elif cmd == "help":
        show_help()


def show_help():
    print()
    print("=" * 56)
    print("  Smart Key — یک کلمه، همه چیز")
    print("=" * 56)
    print()
    print("  فقط تایپ کن و Enter بزن:")
    print()
    print("  جستجو و پرسش:")
    print("    s fastapi          جستجو")
    print("    a how to test      سؤال")
    print("    r fastapi          پکیج مرتبط")
    print("    g asyncio          گراف")
    print("    path django flask  مسیر بین دو پکیج")
    print()
    print("  اجرا:")
    print("    run 3              سه چرخه کشف")
    print("    e 50               دریافت README")
    print("    rb                 بازسازی گراف")
    print()
    print("  یادگیری:")
    print("    l                  استخراج دانش")
    print("    goal backend       مسیر یادگیری")
    print("    h                  راهنما")
    print()
    print("  سیستم:")
    print("    stats              آمار")
    print("    snap               پشتیبان")
    print("    cap                توانایی دستگاه")
    print("    meta               ارتقای خود")
    print()
    print("  /anything            اجرای مستقیم")
    print("  هر چیز دیگری         جستجو می‌شود")
    print()


def interactive():
    """حلقه تعاملی"""
    os.system("clear")
    print()
    print("  ┌────────────────────────────────────────────┐")
    print("  │  EvoScanner Smart Key                      │")
    print("  │  یک کلمه یا جمله بنویس، Enter بزن          │")
    print("  │  'h' = راهنما، 'q' = خروج                  │")
    print("  └────────────────────────────────────────────┘")
    print()

    while True:
        try:
            text = input("  > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return

        if not text:
            continue
        if text.lower() in ("q", "quit", "exit", "خروج"):
            print("\n  Bye\n")
            return
        if text.lower() in ("h", "help", "راهنما"):
            show_help()
            continue

        handle(text)
        print()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # اجرای یک‌خطی
        handle(" ".join(sys.argv[1:]))
    else:
        interactive()

