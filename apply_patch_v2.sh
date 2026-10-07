#!/data/data/com.termux/files/usr/bin/bash
# ─────────────────────────────────────────────
# EvoScanner Patch v0.1 → v0.2
# اجرا: bash apply_patch_v2.sh
# ─────────────────────────────────────────────

set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'

echo -e "${YELLOW}▶ شروع پچ v0.1 → v0.2${NC}"

# ── ۱. پشتیبان‌گیری ─────────────────────────
if [ -f evoscanner.py ]; then
    cp evoscanner.py "evoscanner_v0.1.py.bak"
    echo -e "${GREEN}✓ پشتیبان ساخته شد: evoscanner_v0.1.py.bak${NC}"
else
    echo -e "${YELLOW}! فایل evoscanner.py یافت نشد، ادامه می‌دهیم${NC}"
fi

# ── ۲. Migration دیتابیس ────────────────────
if [ -f knowledge.db ]; then
    cp knowledge.db "knowledge.db.bak"
    echo -e "${GREEN}✓ پشتیبان دیتابیس: knowledge.db.bak${NC}"

    python - <<'PYEOF'
import sqlite3
from pathlib import Path
db = Path("knowledge.db")
conn = sqlite3.connect(db)
cur = conn.cursor()
cols = [r[1] for r in cur.execute("PRAGMA table_info(resources)")]
if "tags" not in cols:
    cur.execute("ALTER TABLE resources ADD COLUMN tags TEXT DEFAULT ''")
    print("  + ستون 'tags' اضافه شد")
else:
    print("  • ستون 'tags' از قبل وجود داشت")
conn.commit()
conn.close()
PYEOF
fi

# ── ۳. نوشتن فایل جدید ───────────────────────
cat > evoscanner_v2.py <<'PYFILE'
#!/usr/bin/env python3
"""
EvoScanner v0.2 — نسخه بهبودیافته
رفع PyPI + افزودن StackOverflow/Reddit/Dev.to + گزارش
"""

import hashlib, json, re, sqlite3, ssl, sys, time
import urllib.request, urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

HOME = Path.home()
BASE = HOME / "evoscanner"
BASE.mkdir(exist_ok=True)
DB = BASE / "knowledge.db"
EVO = BASE / "evolution.json"
REPORT = BASE / "report.md"

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux) EvoScanner/0.2"}


# ─────────── پایگاه دانش ───────────

class KB:
    def __init__(self):
        self.conn = sqlite3.connect(DB)
        self.conn.execute("""CREATE TABLE IF NOT EXISTS resources(
            hash TEXT PRIMARY KEY, url TEXT, title TEXT, content TEXT,
            source TEXT, score REAL, tags TEXT, found_at TEXT)""")
        self.conn.execute("""CREATE TABLE IF NOT EXISTS queries(
            id INTEGER PRIMARY KEY AUTOINCREMENT, query TEXT, source TEXT,
            new_hits INTEGER, ts TEXT)""")
        self.conn.commit()

    def add(self, url, title, content, source, score=0.5, tags=""):
        h = hashlib.sha256((url + title).encode()).hexdigest()[:16]
        try:
            self.conn.execute("INSERT INTO resources VALUES (?,?,?,?,?,?,?,?)",
                (h, url, title, content[:800], source, score, tags,
                 datetime.now().isoformat()))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def log(self, q, src, new):
        self.conn.execute("INSERT INTO queries(query,source,new_hits,ts) VALUES(?,?,?,?)",
            (q, src, new, datetime.now().isoformat()))
        self.conn.commit()

    def total(self):
        return self.conn.execute("SELECT COUNT(*) FROM resources").fetchone()[0]

    def stats(self):
        return self.conn.execute(
            "SELECT source, COUNT(*), AVG(score) FROM resources GROUP BY source"
        ).fetchall()

    def search(self, term, limit=20):
        return self.conn.execute(
            """SELECT source, title, url, score FROM resources
               WHERE title LIKE ? OR content LIKE ? OR tags LIKE ?
               ORDER BY score DESC LIMIT ?""",
            (f"%{term}%", f"%{term}%", f"%{term}%", limit)).fetchall()

    def best_queries(self, limit=10):
        return self.conn.execute(
            """SELECT query, SUM(new_hits) as t FROM queries
               GROUP BY query ORDER BY t DESC LIMIT ?""", (limit,)).fetchall()

    def by_source(self, src, limit=100):
        return self.conn.execute(
            """SELECT title, url, score FROM resources
               WHERE source=? ORDER BY score DESC LIMIT ?""", (src, limit)).fetchall()


# ─────────── HTTP ───────────

def get(url, timeout=15):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as r:
        return r.read().decode("utf-8", errors="ignore")


# ─────────── اسکنرها ───────────

def github(q, n=5):
    url = "https://api.github.com/search/repositories?" + urllib.parse.urlencode({
        "q": f"{q} language:python", "sort": "stars",
        "order": "desc", "per_page": n})
    try:
        data = json.loads(get(url))
        out = []
        for it in data.get("items", []):
            out.append({
                "url": it["html_url"], "title": it["full_name"],
                "content": (it.get("description") or "")[:500],
                "source": "github",
                "score": min(it.get("stargazers_count", 0) / 10000, 1.0),
                "tags": "repo,python"})
        return out
    except Exception as e:
        print(f"  ! github: {e}"); return []


def arxiv(q, n=5):
    """فقط دسته‌های مرتبط با برنامه‌نویسی و AI"""
    cat_filter = "(cat:cs.SE OR cat:cs.PL OR cat:cs.AI OR cat:cs.LG OR cat:cs.CL)"
    url = "http://export.arxiv.org/api/query?" + urllib.parse.urlencode({
        "search_query": f"all:{q} AND {cat_filter}",
        "start": 0, "max_results": n,
        "sortBy": "submittedDate", "sortOrder": "descending"})
    try:
        root = ET.fromstring(get(url))
        ns = {"a": "http://www.w3.org/2005/Atom"}
        out = []
        for e in root.findall("a:entry", ns):
            title = e.find("a:title", ns).text.strip().replace("\n", " ")
            summary = e.find("a:summary", ns).text.strip().replace("\n", " ")
            link = e.find("a:id", ns).text
            cats = [c.get("term") for c in e.findall("a:category", ns)]
            out.append({
                "url": link, "title": title,
                "content": summary[:600], "source": "arxiv",
                "score": 0.85, "tags": ",".join(cats)})
        return out
    except Exception as e:
        print(f"  ! arxiv: {e}"); return []


def stackoverflow(q, n=5):
    """Stack Overflow API — بدون کلید، سهمیه ۳۰۰ در روز"""
    url = "https://api.stackexchange.com/2.3/search/advanced?" + urllib.parse.urlencode({
        "order": "desc", "sort": "votes",
        "q": q, "tagged": "python",
        "site": "stackoverflow", "pagesize": n,
        "filter": "withbody"})
    try:
        data = json.loads(get(url))
        out = []
        for it in data.get("items", []):
            body = re.sub(r"<[^>]+>", "", it.get("body", ""))[:500]
            out.append({
                "url": it["link"],
                "title": it["title"],
                "content": body,
                "source": "stackoverflow",
                "score": min(it.get("score", 0) / 100, 1.0),
                "tags": ",".join(it.get("tags", []))})
        return out
    except Exception as e:
        print(f"  ! stackoverflow: {e}"); return []


def reddit(q, n=5):
    """Reddit JSON API — بدون کلید"""
    url = "https://www.reddit.com/search.json?" + urllib.parse.urlencode({
        "q": f"{q} subreddit:Python", "sort": "top",
        "t": "year", "limit": n})
    try:
        data = json.loads(get(url))
        out = []
        for it in data.get("data", {}).get("children", []):
            d = it["data"]
            out.append({
                "url": f"https://reddit.com{d['permalink']}",
                "title": d["title"],
                "content": (d.get("selftext") or "")[:500],
                "source": "reddit",
                "score": min(d.get("score", 0) / 1000, 1.0),
                "tags": f"r/{d['subreddit']}"})
        return out
    except Exception as e:
        print(f"  ! reddit: {e}"); return []


def devto(q, n=5):
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
        print(f"  ! devto: {e}"); return []


SCANNERS = [
    ("github", github),
    ("arxiv", arxiv),
    ("stackoverflow", stackoverflow),
    ("reddit", reddit),
    ("devto", devto),
]


# ─────────── موتور تکامل ───────────

BASE_TOPICS = [
    "python asyncio", "python machine learning", "python typing",
    "python testing", "python performance", "python web framework",
    "python security", "python design patterns", "python packaging",
    "python concurrency", "python data science", "python fastapi",
    "python pydantic", "python poetry", "python debugging",
]

MUTATORS = [
    "{} 2025", "{} 2026", "best {}", "advanced {}",
    "{} benchmark", "{} tutorial", "{} best practices",
    "{} production", "{} patterns",
]


class Evolver:
    def __init__(self, kb):
        self.kb = kb
        self.state = self._load()

    def _load(self):
        if EVO.exists():
            return json.loads(EVO.read_text())
        return {"cycle": 0, "active": list(BASE_TOPICS),
                "retired": [], "history": []}

    def _save(self):
        EVO.write_text(json.dumps(self.state, indent=2))

    def next_queries(self, n=6):
        best = [q for q, _ in self.kb.best_queries(5)]
        pool = list(dict.fromkeys(best + self.state["active"]))
        return pool[:n]

    def evolve(self):
        import random
        self.state["cycle"] += 1
        scores = {q: t for q, t in self.kb.best_queries(100)}

        survivors = []
        for q in self.state["active"]:
            if q not in scores or scores[q] > 0:
                survivors.append(q)
            else:
                self.state["retired"].append(q)

        if scores:
            top3 = sorted(scores, key=scores.get, reverse=True)[:3]
            for best_q in top3:
                for _ in range(2):
                    new = random.choice(MUTATORS).format(best_q)
                    if new not in survivors:
                        survivors.append(new)

        while len(survivors) < 10:
            for t in BASE_TOPICS:
                if t not in survivors:
                    survivors.append(t); break

        self.state["active"] = survivors[:15]
        self.state["history"].append({
            "cycle": self.state["cycle"],
            "active": len(survivors),
            "retired_total": len(self.state["retired"]),
            "ts": datetime.now().isoformat()})
        self._save()
        return self.state["active"]


# ─────────── گزارش ───────────

def write_report(kb, evo):
    lines = [
        f"# گزارش EvoScanner v0.2",
        f"\n**تاریخ:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**چرخه:** {evo.state['cycle']}",
        f"**کل منابع:** {kb.total()}\n",
        "## آمار منابع\n",
        "| منبع | تعداد | میانگین امتیاز |",
        "|---|---|---|",
    ]
    for src, cnt, avg in kb.stats():
        lines.append(f"| {src} | {cnt} | {avg:.2f} |")

    lines.append("\n## بهترین منابع گیت‌هاب\n")
    for title, url, score in kb.by_source("github", 10):
        lines.append(f"- [{title}]({url}) — ⭐ {score:.2f}")

    lines.append("\n## پژوهش‌های arXiv\n")
    for title, url, score in kb.by_source("arxiv", 10):
        lines.append(f"- [{title}]({url})")

    lines.append("\n## کوئری‌های فعال\n")
    for q in evo.state["active"][:15]:
        lines.append(f"- `{q}`")

    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"📄 گزارش نوشته شد: {REPORT}")


# ─────────── حلقه اصلی ───────────

def one_cycle(kb, evo, queries):
    cycle = evo.state["cycle"] + 1
    print(f"\n═══ چرخه {cycle} ═══")
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
    print(f"\nجدید: {total_new} | کل: {kb.total()}")
    evo.evolve()
    return total_new


def show_stats(kb, evo):
    print("\n📊 پایگاه دانش:")
    for src, cnt, avg in kb.stats():
        print(f"  {src:15s} {cnt:5d} | میانگین {avg:.2f}")
    print(f"  کل: {kb.total()} | چرخه: {evo.state['cycle']}")


def main():
    kb = KB(); evo = Evolver(kb)

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "stats":
            show_stats(kb, evo); return
        if cmd == "search":
            term = sys.argv[2] if len(sys.argv) > 2 else "python"
            for src, title, url, score in kb.search(term):
                print(f"[{src:15s}] {score:.2f} {title[:60]}\n   {url}")
            return
        if cmd == "queries":
            for q in evo.state["active"]:
                print(f"  • {q}")
            return
        if cmd == "report":
            write_report(kb, evo); return
        if cmd == "run":
            n = int(sys.argv[2]) if len(sys.argv) > 2 else 3
            for i in range(n):
                one_cycle(kb, evo, evo.next_queries(6))
                if i < n - 1:
                    print("  انتظار ۱۰s..."); time.sleep(10)
            show_stats(kb, evo)
            write_report(kb, evo)
            return

    one_cycle(kb, evo, evo.next_queries(6))
    show_stats(kb, evo)


if __name__ == "__main__":
    main()
PYFILE

chmod +x evoscanner_v2.py
echo -e "${GREEN}✓ فایل evoscanner_v2.py ساخته شد${NC}"

# ── ۴. تست نحوی ──────────────────────────────
python -m py_compile evoscanner_v2.py && \
    echo -e "${GREEN}✓ تست نحوی موفق${NC}" || {
        echo -e "${RED}✗ خطای نحوی — فایل اصلی حفظ شد${NC}"; exit 1; }

# ── ۵. خلاصه ─────────────────────────────────
echo ""
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo -e "${GREEN}  پچ با موفقیت اعمال شد${NC}"
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo ""
echo "فایل‌های ساخته‌شده:"
echo "  • evoscanner_v2.py         ← نسخه جدید"
echo "  • evoscanner_v0.1.py.bak   ← پشتیبان کد قدیمی"
echo "  • knowledge.db.bak         ← پشتیبان دیتابیس"
echo ""
echo "دستورات:"
echo "  python evoscanner_v2.py run 3"
echo "  python evoscanner_v2.py stats"
echo "  python evoscanner_v2.py report"
echo "  python evoscanner_v2.py search fastapi"

