#!/usr/bin/env python3
"""v1.0 — حالت آفلاین: جستجو، دسته‌بندی، گزارش روی داده‌های موجود"""
from pathlib import Path
import py_compile, sys

src = Path("evoscanner_v2.py")
code = src.read_text()

# ── ۱. دسته‌بندی خودکار منابع ─────────────────
categorizer = '''

# ─────────── دسته‌بندی خودکار ───────────
CATEGORIES = {
    "async":      ["async", "asyncio", "await", "concurren", "aiohttp", "sanic"],
    "web":        ["flask", "django", "fastapi", "web", "http", "rest", "api"],
    "ml-ai":      ["machine learning", "ml", "ai", "neural", "deep", "llm",
                   "transformer", "gpt", "model", "training", "pytorch",
                   "tensorflow", "scikit", "gradio"],
    "testing":    ["test", "pytest", "unittest", "coverage", "mock"],
    "data":       ["pandas", "numpy", "data science", "dataframe", "csv",
                   "database", "sql", "sqlite", "postgres"],
    "security":   ["security", "vulnerab", "crypto", "auth", "cve", "injection"],
    "performance":["performance", "benchmark", "optim", "speed", "memory",
                   "profil", "cache"],
    "typing":     ["typing", "type hint", "mypy", "pydantic", "dataclass"],
    "patterns":   ["design pattern", "pattern", "architecture", "solid",
                   "refactor"],
    "packaging":  ["poetry", "pip", "package", "setuptools", "wheel", "pypi"],
    "parsing":    ["regex", "parse", "scrap", "beautifulsoup", "lxml",
                   "selenium"],
    "devops":     ["docker", "kubernetes", "ci", "cd", "deploy", "pipeline"],
}


def categorize(title, content="", tags=""):
    """تشخیص دسته بر اساس کلمات کلیدی"""
    text = (title + " " + content + " " + tags).lower()
    hits = []
    for cat, words in CATEGORIES.items():
        score = sum(1 for w in words if w in text)
        if score > 0:
            hits.append((cat, score))
    hits.sort(key=lambda x: -x[1])
    return hits[0][0] if hits else "other"


'''

if "def categorize(" not in code:
    code = code.replace("# ─────────── HTTP ───────────",
                        categorizer + "\n# ─────────── HTTP ───────────")

# ── ۲. میگریشن: افزودن ستون category ────────
old_init = '''            self.conn.execute("""CREATE TABLE IF NOT EXISTS resources(
            hash TEXT PRIMARY KEY, url TEXT, title TEXT, content TEXT,
            source TEXT, score REAL, tags TEXT, found_at TEXT)""")'''

new_init = '''            self.conn.execute("""CREATE TABLE IF NOT EXISTS resources(
            hash TEXT PRIMARY KEY, url TEXT, title TEXT, content TEXT,
            source TEXT, score REAL, tags TEXT, found_at TEXT,
            category TEXT DEFAULT 'other')""")'''

if old_init in code:
    code = code.replace(old_init, new_init)
    print("✓ جدول با ستون category به‌روز شد")

# migration
old_kb_init_end = '''        self.conn.execute("""CREATE TABLE IF NOT EXISTS queries(
            id INTEGER PRIMARY KEY AUTOINCREMENT, query TEXT, source TEXT,
            new_hits INTEGER, ts TEXT)""")
        self.conn.commit()'''

new_kb_init_end = '''        self.conn.execute("""CREATE TABLE IF NOT EXISTS queries(
            id INTEGER PRIMARY KEY AUTOINCREMENT, query TEXT, source TEXT,
            new_hits INTEGER, ts TEXT)""")
        # migration: افزودن category اگر نبود
        cols = [r[1] for r in self.conn.execute("PRAGMA table_info(resources)")]
        if "category" not in cols:
            self.conn.execute("ALTER TABLE resources ADD COLUMN category TEXT DEFAULT 'other'")
        self.conn.commit()
        self._categorize_existing()

    def _categorize_existing(self):
        """دسته‌بندی خودکار منابعی که category ندارند"""
        rows = self.conn.execute(
            "SELECT hash, title, content, tags FROM resources WHERE category='other' OR category IS NULL"
        ).fetchall()
        for h, title, content, tags in rows:
            cat = categorize(title or "", content or "", tags or "")
            self.conn.execute("UPDATE resources SET category=? WHERE hash=?",
                              (cat, h))
        if rows:
            self.conn.commit()
            print(f"  🏷  {len(rows)} منبع دسته‌بندی شد")'''

if old_kb_init_end in code:
    code = code.replace(old_kb_init_end, new_kb_init_end)
    print("✓ migration category اضافه شد")

# ── ۳. توابع جدید: by_category, categories_stats ──
new_methods = '''
    def categories_stats(self):
        return self.conn.execute(
            """SELECT category, COUNT(*), AVG(score)
               FROM resources GROUP BY category ORDER BY COUNT(*) DESC"""
        ).fetchall()

    def by_category(self, cat, limit=50):
        return self.conn.execute(
            """SELECT source, title, url, score FROM resources
               WHERE category=? ORDER BY score DESC LIMIT ?""",
            (cat, limit)).fetchall()

'''

# اضافه به کلاس KB قبل از all_hashes
marker = "    def all_hashes(self):"
if marker in code and "def categories_stats" not in code:
    code = code.replace(marker, new_methods + marker)
    print("✓ توابع categories_stats و by_category اضافه شد")

# ── ۴. دستور آفلاین در main ──────────────────
offline_block = '''        if cmd == "offline":
            print("🔌 حالت آفلاین — فقط داده‌های موجود")
            show_stats(kb, evo)
            print("\\n📂 دسته‌بندی منابع:")
            for cat, cnt, avg in kb.categories_stats():
                print(f"  {cat:15s} {cnt:4d}  میانگین {avg:.2f}")
            print("\\n🏆 برترین‌ها در هر دسته:")
            for cat, cnt, avg in kb.categories_stats()[:5]:
                print(f"\\n  ── {cat} ──")
                for src, title, url, score in kb.by_category(cat, 3):
                    print(f"    [{src}] {title[:60]}")
            return

        if cmd == "categories":
            for cat, cnt, avg in kb.categories_stats():
                print(f"  {cat:15s} {cnt:4d}  میانگین {avg:.2f}")
            return

        if cmd == "cat":
            cat = sys.argv[2] if len(sys.argv) > 2 else "web"
            for src, title, url, score in kb.by_category(cat, 30):
                print(f"[{src:15s}] {score:.2f}  {title[:65]}")
                print(f"   {url}")
            return

        if cmd == "top":
            n = int(sys.argv[2]) if len(sys.argv) > 2 else 15
            rows = kb.conn.execute(
                """SELECT source, title, url, score, category
                   FROM resources ORDER BY score DESC LIMIT ?""", (n,)).fetchall()
            for src, title, url, score, cat in rows:
                print(f"[{src:15s}|{cat:10s}] {score:.2f}  {title[:55]}")
                print(f"   {url}")
            return
'''

marker2 = '        if cmd == "health":'
if marker2 in code and 'cmd == "offline"' not in code:
    code = code.replace(marker2, offline_block + "\n" + marker2)
    print("✓ دستورات offline, categories, cat, top اضافه شد")

# ── ۵. گزارش با دسته‌بندی ────────────────────
old_report_cat = '''    lines.append("\\n## کوئری‌های فعال\\n")'''

new_report_cat = '''    lines.append("\\n## دسته‌بندی منابع\\n")
    lines.append("| دسته | تعداد | میانگین امتیاز |")
    lines.append("|---|---|---|")
    for cat, cnt, avg in kb.categories_stats():
        lines.append(f"| {cat} | {cnt} | {avg:.2f} |")

    lines.append("\\n## برترین منابع هر دسته\\n")
    for cat, cnt, avg in kb.categories_stats()[:8]:
        lines.append(f"\\n### {cat} ({cnt} مورد)\\n")
        for src, title, url, score in kb.by_category(cat, 5):
            lines.append(f"- [{title}]({url}) — `{src}` ⭐ {score:.2f}")

    lines.append("\\n## کوئری‌های فعال\\n")'''

if old_report_cat in code:
    code = code.replace(old_report_cat, new_report_cat)
    print("✓ گزارش با دسته‌بندی به‌روز شد")

# ── ۶. ذخیره ──────────────────────────────
src.write_text(code)
print("✓ فایل ذخیره شد")

try:
    py_compile.compile("evoscanner_v2.py", doraise=True)
    print("✓ نحو درست")
except py_compile.PyCompileError as e:
    print(f"✗ خطای نحوی: {e}")
    sys.exit(1)
