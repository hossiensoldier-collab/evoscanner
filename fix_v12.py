#!/usr/bin/env python3
"""v1.2 — مسیر خودکار + پیشنهاد کوئری + رابط وب"""
from pathlib import Path
import py_compile, sys

src = Path("evoscanner_v2.py")
code = src.read_text()

# ── ۱. پیشنهاد کوئری برای پر کردن شکاف ─────
suggest = '''

# ─────────── پیشنهاد کوئری بر اساس شکاف ───────────

GAP_QUERIES = {
    "parsing":   ["python regex advanced", "python parser combinator",
                  "beautifulsoup vs lxml", "python html parsing"],
    "data":      ["pandas advanced", "python polars", "duckdb python",
                  "python data pipeline"],
    "typing":    ["python typing generics", "python protocol typing",
                  "mypy strict mode", "pydantic v2"],
    "packaging": ["python poetry guide", "pyproject.toml", "uv python",
                  "python wheel build"],
    "devops":    ["python docker best practices", "python kubernetes client",
                  "github actions python", "python ci cd"],
    "testing":   ["python pytest fixtures", "hypothesis python",
                  "python mock advanced", "pytest parametrize"],
    "performance": ["python numba jit", "cython tutorial", "python memory profiler",
                    "python async performance"],
    "patterns":  ["python design patterns book", "python dependency injection",
                  "python hexagonal architecture"],
    "security":  ["python security best practices", "bandit python",
                  "python cryptography"],
    "async":     ["python asyncio advanced", "python anyio", "trio python"],
    "web":       ["python fastapi advanced", "django rest framework",
                  "python graphql"],
    "ml-ai":     ["python llm fine tuning", "huggingface transformers advanced",
                  "langchain python", "rag python"],
}


def suggest_queries(kb, top_n=3):
    """پیشنهاد کوئری برای دسته‌های ضعیف"""
    stats = {c: n for c, n, _ in kb.categories_stats()}
    weak = []
    for cat in GAP_QUERIES:
        cnt = stats.get(cat, 0)
        if cnt < 5:
            weak.append((cat, cnt))
    weak.sort(key=lambda x: x[1])

    if not weak:
        print("✅ همه دسته‌ها پوشش کافی دارند")
        return []

    suggestions = []
    print(f"\\n📉 {len(weak)} دسته ضعیف — پیشنهاد کوئری:\\n")
    for cat, cnt in weak[:top_n]:
        print(f"  ── {cat} ({cnt} منبع) ──")
        for q in GAP_QUERIES[cat][:3]:
            print(f"    • {q}")
            suggestions.append(q)
        print()

    # ذخیره در evolution برای چرخه بعدی
    import json as _json
    evo_file = BASE / "evolution.json"
    if evo_file.exists():
        try:
            state = _json.loads(evo_file.read_text())
            state.setdefault("suggested", [])
            state["suggested"] = list(dict.fromkeys(
                state["suggested"] + suggestions
            ))[:30]
            # افزودن به active
            state["active"] = list(dict.fromkeys(
                state["active"] + suggestions
            ))[:25]
            evo_file.write_text(_json.dumps(state, indent=2))
            print(f"  ✓ {len(suggestions)} کوئری به لیست فعال اضافه شد")
            print(f"    در چرخه بعدی به‌طور خودکار اجرا می‌شوند")
        except Exception as e:
            print(f"  ! خطا در ذخیره: {e}")

    return suggestions


# ─────────── مسیر یادگیری خودکار ───────────

def auto_path(kb, topic):
    """مسیر یادگیری ۴ سطحی + پیشنهاد منابع جایگزین برای سطح خالی"""
    print(f"\\n🎯 مسیر یادگیری خودکار: {topic}")
    print("─" * 55)

    levels = [
        ("مبتدی",   [f"{topic}", f"{topic} tutorial", f"{topic} basics",
                     f"{topic} intro", f"python {topic}"]),
        ("متوسط",   [f"{topic} advanced", f"{topic} patterns",
                     f"{topic} best practices", f"{topic} intermediate"]),
        ("پیشرفته", [f"{topic} internals", f"{topic} performance",
                     f"{topic} production", f"{topic} deep dive"]),
        ("پژوهش",   [f"{topic} research", f"{topic} paper",
                     f"{topic} state of the art", f"{topic} benchmark"]),
    ]

    total = 0
    missing = []
    for level, queries in levels:
        found = []
        for q in queries:
            found.extend(kb.search(q, 5))
        seen = set(); uniq = []
        for src_, title, url, score in found:
            if url not in seen:
                seen.add(url); uniq.append((src_, title, url, score))
        print(f"\\n  ◆ {level} — {len(uniq)} منبع")
        if not uniq:
            missing.append(level)
            print("    (خالی — نیاز به جمع‌آوری)")
        for src_, title, url, score in uniq[:3]:
            total += 1
            print(f"    • [{src_:14s}] {title[:55]}")
            print(f"      {url}")

    # پیشنهاد برای سطوح خالی
    if missing:
        print(f"\\n  💡 سطوح خالی: {', '.join(missing)}")
        print(f"  کوئری پیشنهادی:")
        for level in missing:
            for q in [f"{topic} {level}"]:
                print(f"    • {q}")

    print(f"\\n  جمع: {total} منبع مرتبط")
    return total


'''

marker = "\n# ─────────── کاوشگر تعاملی ───────────"
if marker in code and "def suggest_queries" not in code:
    code = code.replace(marker, suggest + marker, 1)
    print("✓ suggest_queries و auto_path اضافه شد")

# ── ۲. رابط وب با http.server استاندارد ─────
web = '''

# ─────────── رابط وب ───────────

def run_web(kb, evo, port=8080):
    """سرور وب ساده با کتابخانه استاندارد"""
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import urllib.parse

    HTML_HEAD = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>EvoScanner</title>
<style>
body{font-family:-apple-system,sans-serif;max-width:900px;margin:2em auto;
     padding:0 1em;background:#0d1117;color:#c9d1d9}
h1{color:#58a6ff} h2{color:#79c0ff;border-bottom:1px solid #30363d;padding-bottom:.3em}
input{width:70%;padding:.7em;background:#161b22;color:#c9d1d9;
      border:1px solid #30363d;border-radius:6px;font-size:1em}
button{padding:.7em 1.5em;background:#238636;color:#fff;border:0;
       border-radius:6px;font-size:1em;cursor:pointer}
button:hover{background:#2ea043}
.item{padding:.8em;margin:.5em 0;background:#161b22;border-left:3px solid #58a6ff;
      border-radius:4px}
.item a{color:#58a6ff;text-decoration:none;font-weight:bold}
.item a:hover{text-decoration:underline}
.src{font-size:.8em;color:#8b949e;background:#21262d;padding:.15em .5em;
     border-radius:10px;margin-right:.5em}
.cat{font-size:.8em;color:#d29922;margin-left:.5em}
.score{font-size:.8em;color:#8b949e;float:right}
.cats{margin:1em 0}
.cat-row{display:flex;align-items:center;gap:1em;margin:.3em 0}
.bar{height:14px;background:#238636;border-radius:7px;min-width:2px}
</style></head><body>
<h1>🔍 EvoScanner</h1>
"""

    HTML_TAIL = "</body></html>"


    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass  # ساکت

        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            qs = urllib.parse.parse_qs(parsed.query)
            path = parsed.path
            q = qs.get("q", [""])[0]
            cat = qs.get("cat", [""])[0]

            html = [HTML_HEAD]

            if path == "/" or path == "":
                # فرم جستجو
                html.append(f'''
                <form method="get" action="/">
                  <input name="q" value="{q}" placeholder="جستجو..." autofocus>
                  <button>جستجو</button>
                </form>
                ''')

                # دسته‌ها
                cats = kb.categories_stats()
                html.append('<div class="cats"><h2>دسته‌ها</h2>')
                max_n = max((c for _, c, _ in cats), default=1)
                for c, n, avg in cats:
                    bar_w = int(n / max_n * 300)
                    html.append(
                        f'<div class="cat-row">'
                        f'<a href="/?cat={c}" style="color:#79c0ff;text-decoration:none;'
                        f'width:100px">{c}</a>'
                        f'<div class="bar" style="width:{bar_w}px"></div>'
                        f'<span>{n} | ⌀ {avg:.2f}</span>'
                        f'</div>'
                    )
                html.append('</div>')

                # نتایج
                if q:
                    results = kb.search(q, 30)
                    html.append(f'<h2>نتایج "{q}" ({len(results)})</h2>')
                    for src_, title, url, score in results:
                        html.append(
                            f'<div class="item">'
                            f'<span class="src">{src_}</span>'
                            f'<a href="{url}" target="_blank">{title}</a>'
                            f'<span class="score">⭐ {score:.2f}</span>'
                            f'</div>'
                        )
                elif cat:
                    results = kb.by_category(cat, 50)
                    html.append(f'<h2>دسته {cat} ({len(results)})</h2>')
                    for src_, title, url, score in results:
                        html.append(
                            f'<div class="item">'
                            f'<span class="src">{src_}</span>'
                            f'<a href="{url}" target="_blank">{title}</a>'
                            f'<span class="score">⭐ {score:.2f}</span>'
                            f'</div>'
                        )
                else:
                    html.append(f'<p style="color:#8b949e">'
                                f'کل منابع: {kb.total()} | چرخه: {evo.state["cycle"]}'
                                f'</p>')

            elif path == "/stats":
                html.append('<h2>📊 آمار</h2>')
                for src_, cnt, avg in kb.stats():
                    html.append(f'<div class="item">'
                                f'<b>{src_}</b> — {cnt} | ⌀ {avg:.2f}</div>')
                html.append(f'<p>کل: <b>{kb.total()}</b></p>')
                html.append('<p><a href="/" style="color:#58a6ff">← بازگشت</a></p>')

            html.append(HTML_TAIL)
            body = "".join(html).encode("utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    print(f"\\n🌐 سرور وب: http://localhost:{port}")
    print("   Ctrl+C برای توقف\\n")
    try:
        HTTPServer(("", port), Handler).serve_forever()
    except KeyboardInterrupt:
        print("\\n⏸ سرور متوقف شد")


'''

marker2 = "\n# ─────────── حلقه اصلی ───────────"
if marker2 in code and "def run_web" not in code:
    code = code.replace(marker2, web + marker2, 1)
    print("✓ run_web اضافه شد")

# ── ۳. دستورات جدید در main ─────────────────
new_cmds = '''        if cmd == "suggest":
            suggest_queries(kb, top_n=5); return

        if cmd == "path":
            topic = sys.argv[2] if len(sys.argv) > 2 else "asyncio"
            auto_path(kb, topic); return

        if cmd == "web":
            port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
            run_web(kb, evo, port); return

'''

marker3 = '        if cmd == "explore":'
if marker3 in code and 'cmd == "suggest"' not in code:
    code = code.replace(marker3, new_cmds + marker3, 1)
    print("✓ دستورات suggest/path/web اضافه شد")

src.write_text(code)
print("✓ فایل ذخیره شد")

try:
    py_compile.compile("evoscanner_v2.py", doraise=True)
    print("✓ نحو درست")
except py_compile.PyCompileError as e:
    print(f"✗ خطای نحوی: {e}")
    sys.exit(1)
