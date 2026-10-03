#!/usr/bin/env python3
"""v0.3 — Health Tracker + منابع پایدار + TF-IDF سبک"""
from pathlib import Path
import py_compile, sys

src = Path("evoscanner_v2.py")
code = src.read_text()

# ── ۱. Health Tracker ────────────────────────
health_code = '''

# ─────────── Health Tracker ───────────
_HEALTH_FILE = BASE / "health.json"

class Health:
    """ردیابی سلامت منابع — بعد از ۳ خطای متوالی، منبع خاموش می‌شود"""
    def __init__(self):
        self.data = self._load()

    def _load(self):
        if _HEALTH_FILE.exists():
            try:
                return json.loads(_HEALTH_FILE.read_text())
            except Exception:
                pass
        return {}

    def _save(self):
        _HEALTH_FILE.write_text(json.dumps(self.data, indent=2))

    def is_ok(self, name):
        return self.data.get(name, {}).get("fails", 0) < 3

    def ok(self, name):
        d = self.data.setdefault(name, {})
        d["fails"] = 0
        d["last_ok"] = datetime.now().isoformat()
        self._save()

    def fail(self, name):
        d = self.data.setdefault(name, {})
        d["fails"] = d.get("fails", 0) + 1
        d["last_fail"] = datetime.now().isoformat()
        self._save()
        if d["fails"] >= 3:
            print(f"  ⚠ {name} خاموش شد (۳ خطای متوالی)")

    def summary(self):
        return [(k, v.get("fails", 0)) for k, v in self.data.items()]

'''

if "class Health:" not in code:
    code = code.replace("# ─────────── HTTP ───────────",
                        health_code + "\n# ─────────── HTTP ───────────")

# ── ۲. بازنویسی one_cycle با health ──────────
old_cycle = '''def one_cycle(kb, evo, queries):
    cycle = evo.state["cycle"] + 1
    print(f"\\n═══ چرخه {cycle} ═══")
    total_new = 0
    for q in queries:
        for name, fn in SCANNERS:
            results = fn(q)
            new = 0
            for r in results:
                if kb.add(r["url"], r["title"], r["content"],
                          r["source"], r["score"], r.get("tags", "")):
                    new += 1; total_new += 1
                    print(f"  + [{r['source']}] {r['title'][:70]}")
            kb.log(q, name, new)
    print(f"\\nجدید: {total_new} | کل: {kb.total()}")
    evo.evolve()
    return total_new'''

new_cycle = '''def one_cycle(kb, evo, queries, health=None):
    cycle = evo.state["cycle"] + 1
    print(f"\\n═══ چرخه {cycle} ═══")
    if health:
        dead = [n for n, _ in health.summary() if not health.is_ok(n)]
        if dead:
            print(f"  💤 منابع خاموش: {', '.join(dead)}")
    total_new = 0
    for q in queries:
        for name, fn in SCANNERS:
            if health and not health.is_ok(name):
                continue
            try:
                results = fn(q)
                new = 0
                for r in results:
                    if kb.add(r["url"], r["title"], r["content"],
                              r["source"], r["score"], r.get("tags", "")):
                        new += 1; total_new += 1
                        print(f"  + [{r['source']}] {r['title'][:70]}")
                kb.log(q, name, new)
                if health:
                    if results:
                        health.ok(name)
                    else:
                        # اگر exception گرفته و لیست خالی برگرداند
                        health.fail(name)
            except Exception as e:
                if health:
                    health.fail(name)
                print(f"  ! {name}: {e}")
    print(f"\\nجدید: {total_new} | کل: {kb.total()}")
    evo.evolve()
    return total_new'''

if old_cycle in code:
    code = code.replace(old_cycle, new_cycle)
    print("✓ one_cycle با health به‌روز شد")

# ── ۳. اضافه کردن GitLab به اسکنرها ──────────
gitlab_fn = '''

def gitlab(q, n=5):
    """GitLab API — جایگزین پایدار GitHub"""
    url = "https://gitlab.com/api/v4/projects?" + urllib.parse.urlencode({
        "search": f"python {q}", "order_by": "star_count",
        "sort": "desc", "per_page": n})
    try:
        data = json.loads(get(url, timeout=10))
        out = []
        for it in data[:n]:
            out.append({
                "url": it["web_url"],
                "title": it["path_with_namespace"],
                "content": (it.get("description") or "")[:500],
                "source": "gitlab",
                "score": min(it.get("star_count", 0) / 5000, 1.0),
                "tags": "gitlab,repo"})
        return out
    except Exception as e:
        print(f"  ! gitlab: {e}"); return []

'''

if "def gitlab" not in code:
    code = code.replace("\nSCANNERS = [", gitlab_fn + "\nSCANNERS = [")

# جایگزینی reddit با gitlab در SCANNERS
if '"hackernews", hackernews' in code or '("hackernews", hackernews),' in code:
    code = code.replace('("hackernews", hackernews),', '("gitlab", gitlab),')

if '("reddit", reddit),' in code:
    code = code.replace('("reddit", reddit),', '("gitlab", gitlab),')

# ── ۴. main با health ────────────────────────
old_main_cycle = "one_cycle(kb, evo, evo.next_queries(6))"
new_main_cycle = "one_cycle(kb, evo, evo.next_queries(6), health)"

# فقط در بلوک run
old_run_block = '''            for i in range(n):
                    one_cycle(kb, evo, evo.next_queries(6))'''
new_run_block = '''            for i in range(n):
                    one_cycle(kb, evo, evo.next_queries(6), health)'''

# در main، health را بساز
if "health = Health()" not in code:
    code = code.replace("    kb = KB(); evo = Evolver(kb)",
                        "    kb = KB(); evo = Evolver(kb); health = Health()")

# جایگزینی همه one_cycle calls
code = code.replace("one_cycle(kb, evo, evo.next_queries(6))",
                    "one_cycle(kb, evo, evo.next_queries(6), health)")

# ── ۵. TF-IDF سبک برای search ────────────────
old_search = '''        if cmd == "search":
            term = sys.argv[2] if len(sys.argv) > 2 else "python"
            for src, title, url, score in kb.search(term):
                print(f"[{src:15s}] {score:.2f} {title[:60]}\\n   {url}")
            return'''

new_search = '''        if cmd == "search":
            term = sys.argv[2] if len(sys.argv) > 2 else "python"
            results = kb.search(term, 30)
            # امتیازدهی TF-IDF سبک
            import math
            N = max(kb.total(), 1)
            scored = []
            term_lower = term.lower()
            for src, title, url, score in results:
                tf = title.lower().count(term_lower)
                if tf == 0:
                    tf = 1
                # idf تقریبی
                idf = math.log(N / 10) if N > 10 else 1.0
                ranked = (tf * idf) + score
                scored.append((ranked, src, title, url))
            scored.sort(reverse=True)
            for rank, src, title, url in scored[:20]:
                print(f"[{src:15s}] {rank:.2f}  {title[:65]}")
                print(f"   {url}")
            return

        if cmd == "health":
            print("وضعیت سلامت منابع:")
            for name, fails in health.summary():
                status = "✓" if fails < 3 else "✗ خاموش"
                print(f"  {status}  {name:15s} خطاها: {fails}")
            return

        if cmd == "reset-health":
            health.data = {}
            health._save()
            print("✓ سلامت منابع ریست شد")
            return'''

if old_search in code:
    code = code.replace(old_search, new_search)
    print("✓ search با TF-IDF + health command اضافه شد")

# ── ۶. ذخیره ──────────────────────────────
src.write_text(code)
print("✓ فایل ذخیره شد")

try:
    py_compile.compile("evoscanner_v2.py", doraise=True)
    print("✓ نحو درست")
except py_compile.PyCompileError as e:
    print(f"✗ خطای نحوی: {e}")
    sys.exit(1)
