#!/usr/bin/env python3
"""v1.1 — کاوشگر تعاملی"""
from pathlib import Path
import py_compile, sys

src = Path("evoscanner_v2.py")
code = src.read_text()

explorer = '''

# ─────────── کاوشگر تعاملی ───────────

def explore(kb, evo):
    """حالت گفتگو با پایگاه دانش"""
    print("\\n" + "═" * 55)
    print("  🔍 کاوشگر دانش — پایگاه پایتون و AI")
    print("═" * 55)
    print("  دستورات:")
    print("    /help         راهنما")
    print("    /cats         دسته‌ها")
    print("    /gaps         شکاف‌های دانشی")
    print("    /path <topic> مسیر یادگیری")
    print("    /quit         خروج")
    print("  یا فقط یک کلمه/سؤال بنویس.")
    print("═" * 55)

    while True:
        try:
            q = input("\\n❯ ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\\nخداحافظ"); return

        if not q:
            continue
        if q in ("/quit", "/exit", "/q"):
            print("خداحافظ"); return
        if q == "/help":
            print("  /cats /gaps /path /quit — یا هر چیزی بنویس")
            continue
        if q == "/cats":
            for cat, cnt, avg in kb.categories_stats():
                bar = "█" * min(cnt, 30)
                print(f"  {cat:12s} {cnt:4d}  {bar}")
            continue
        if q == "/gaps":
            cats = dict((c, n) for c, n, _ in kb.categories_stats())
            weak = [c for c in CATEGORIES if cats.get(c, 0) < 3]
            if weak:
                print("  📉 دسته‌های ضعیف:")
                for c in weak:
                    print(f"    • {c}  ({cats.get(c, 0)} منبع)")
                print("\\n  پیشنهاد: کوئری‌های مرتبط را در evolution.json اضافه کن")
            else:
                print("  ✅ همه دسته‌ها پوشش کافی دارند")
            continue
        if q.startswith("/path "):
            topic = q[6:].strip()
            print_learning_path(kb, topic)
            continue

        # جستجوی عادی
        results = kb.search(q, 10)
        if not results:
            print(f"  ✗ چیزی برای '{q}' پیدا نشد")
            continue
        print(f"\\n  📚 {len(results)} نتیجه:\\n")
        for i, (src, title, url, score) in enumerate(results, 1):
            cat = categorize(title, "", "") if hasattr(sys.modules[__name__], "categorize") else "?"
            print(f"  {i:2d}. [{src:14s}] {title[:60]}")
            print(f"      {url}")
            if score >= 0.9:
                print(f"      ⭐ امتیاز بالا")


def print_learning_path(kb, topic):
    """مسیر یادگیری از مبتدی تا پیشرفته برای یک موضوع"""
    print(f"\\n  🎯 مسیر یادگیری: {topic}")
    print("  " + "─" * 50)

    steps = [
        ("مبتدی",   [topic, f"{topic} tutorial", f"{topic} basics", f"{topic} intro"]),
        ("متوسط",   [f"{topic} advanced", f"{topic} patterns", f"{topic} best practices"]),
        ("پیشرفته", [f"{topic} internals", f"{topic} performance", f"{topic} production"]),
        ("پژوهش",   [f"{topic} research", f"{topic} paper", f"{topic} state of the art"]),
    ]

    for level, queries in steps:
        found = []
        for q in queries:
            r = kb.search(q, 3)
            found.extend(r)
        # حذف تکراری
        seen = set(); uniq = []
        for r in found:
            if r[2] not in seen:
                seen.add(r[2]); uniq.append(r)
        print(f"\\n  ◆ {level} ({len(uniq)} منبع)")
        if not uniq:
            print("    (خالی — نیاز به جمع‌آوری بیشتر)")
        for src, title, url, score in uniq[:3]:
            print(f"    • [{src}] {title[:60]}")
            print(f"      {url}")

'''

# درج قبل از def main
marker = "\ndef main():"
if marker in code and "def explore(" not in code:
    code = code.replace(marker, explorer + marker, 1)
    print("✓ explore اضافه شد")

# افزودن دستور explore به main
main_marker = '        if cmd == "stats":'
if main_marker in code and 'cmd == "explore"' not in code:
    new_cmd = '''        if cmd == "explore":
            explore(kb, evo); return
        if cmd == "stats":'''
    code = code.replace(main_marker, new_cmd, 1)
    print("✓ دستور explore اضافه شد")

src.write_text(code)
print("✓ فایل ذخیره شد")

try:
    py_compile.compile("evoscanner_v2.py", doraise=True)
    print("✓ نحو درست")
except py_compile.PyCompileError as e:
    print(f"✗ خطای نحوی: {e}")
    sys.exit(1)
