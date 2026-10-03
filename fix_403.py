#!/usr/bin/env python3
"""رفع 403 + fallback + Ctrl+C در evoscanner_v2.py"""
from pathlib import Path

src = Path("evoscanner_v2.py")
code = src.read_text()

# ── ۱. هدرهای واقعی مرورگر ──────────────────
old_ua = 'UA = {"User-Agent": "Mozilla/5.0 (X11; Linux) EvoScanner/0.2"}'
new_ua = '''UA = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "identity",
    "Connection": "close",
}'''
if old_ua in code:
    code = code.replace(old_ua, new_ua)

# ── ۲. hackernews → fallback به Lobsters ─────
old_hn = '''def hackernews(q, n=5):
    """Hacker News API — بدون کلید، پایدار"""
    url = "https://hn.algolia.com/api/v1/search?" + urllib.parse.urlencode({
        "query": f"python {q}", "tags": "story",
        "numericFilters": "points>20", "hitsPerPage": n})
    try:
        data = json.loads(get(url))
        out = []
        for it in data.get("hits", []):
            out.append({
                "url": it.get("url") or f"https://news.ycombinator.com/item?id={it['objectID']}",
                "title": it.get("title", ""),
                "content": (it.get("story_text") or "")[:500],
                "source": "hackernews",
                "score": min(it.get("points", 0) / 500, 1.0),
                "tags": "hn,python"})
        return out
    except Exception as e:
        print(f"  ! hackernews: {e}"); return []'''

new_hn = '''def hackernews(q, n=5):
    """HN Algolia + fallback به Lobsters"""
    url = "https://hn.algolia.com/api/v1/search?" + urllib.parse.urlencode({
        "query": f"python {q}", "tags": "story",
        "numericFilters": "points>20", "hitsPerPage": n})
    try:
        data = json.loads(get(url))
        out = []
        for it in data.get("hits", []):
            out.append({
                "url": it.get("url") or f"https://news.ycombinator.com/item?id={it['objectID']}",
                "title": it.get("title", ""),
                "content": (it.get("story_text") or "")[:500],
                "source": "hackernews",
                "score": min(it.get("points", 0) / 500, 1.0),
                "tags": "hn,python"})
        if out:
            return out
    except Exception as e:
        print(f"  ! hackernews: {e}")

    # fallback: Lobsters
    return lobsters(q, n)


def lobsters(q, n=5):
    """Lobsters — جایگزین HN، بدون Cloudflare"""
    url = "https://lobste.rs/search.json?" + urllib.parse.urlencode({
        "q": f"python {q}", "what": "stories",
        "order": "relevance", "page": 1})
    try:
        data = json.loads(get(url))
        out = []
        for it in data[:n]:
            out.append({
                "url": it.get("url") or it.get("comments_url", ""),
                "title": it.get("title", ""),
                "content": (it.get("description") or "")[:500],
                "source": "lobsters",
                "score": min(it.get("score", 0) / 50, 1.0),
                "tags": ",".join(it.get("tags", []))})
        return out
    except Exception as e:
        print(f"  ! lobsters: {e}"); return []'''

if old_hn in code:
    code = code.replace(old_hn, new_hn)
    print("✓ HN با fallback به Lobsters به‌روز شد")
else:
    print("! الگوی HN یافت نشد")

# ── ۳. Dev.to با timeout سخت‌گیرانه ─────────
old_devto = '''def devto(q, n=5):
    """Dev.to API — عمومی، بدون کلید"""
    url = "https://dev.to/api/articles?" + urllib.parse.urlencode({
        "tag": "python", "per_page": n, "top": 365})
    try:
        data = json.loads(get(url))
        out = []
        for it in data[:n]:
            out.append({
                "url": it["url"],
                "title": it["title"],
                "content": (it.get("description") or "")[:500],
                "source": "devto",
                "score": 0.6,
                "tags": ",".join(it.get("tag_list", []))})
        return out
    except Exception as e:
        print(f"  ! devto: {e}"); return []'''

new_devto = '''def devto(q, n=5):
    """Dev.to — با timeout کوتاه"""
    url = "https://dev.to/api/articles?" + urllib.parse.urlencode({
        "tag": "python", "per_page": n, "top": 365})
    try:
        data = json.loads(get(url, timeout=8))
        out = []
        for it in data[:n]:
            out.append({
                "url": it["url"],
                "title": it["title"],
                "content": (it.get("description") or "")[:500],
                "source": "devto",
                "score": 0.6,
                "tags": ",".join(it.get("tag_list", []))})
        return out
    except Exception as e:
        print(f"  ! devto: {e}"); return []'''

if old_devto in code:
    code = code.replace(old_devto, new_devto)
    print("✓ Dev.to با timeout کوتاه به‌روز شد")

# ── ۴. Graceful Ctrl+C در main ──────────────
old_run = '''        if cmd == "run":
            n = int(sys.argv[2]) if len(sys.argv) > 2 else 3
            for i in range(n):
                one_cycle(kb, evo, evo.next_queries(6))
                if i < n - 1:
                    print("  انتظار ۱۰s..."); time.sleep(10)
            show_stats(kb, evo)
            write_report(kb, evo)
            return'''

new_run = '''        if cmd == "run":
            n = int(sys.argv[2]) if len(sys.argv) > 2 else 3
            try:
                for i in range(n):
                    one_cycle(kb, evo, evo.next_queries(6))
                    if i < n - 1:
                        print("  انتظار ۱۰s..."); time.sleep(10)
            except KeyboardInterrupt:
                print("\\n⏸  متوقف شد — ذخیره وضعیت...")
            show_stats(kb, evo)
            write_report(kb, evo)
            return'''

if old_run in code:
    code = code.replace(old_run, new_run)
    print("✓ مدیریت Ctrl+C اضافه شد")

src.write_text(code)
print("\n✓ پچ اعمال شد. تست نحوی:")

import py_compile
try:
    py_compile.compile("evoscanner_v2.py", doraise=True)
    print("✓ نحو درست")
except py_compile.PyCompileError as e:
    print(f"✗ خطای نحوی: {e}")
