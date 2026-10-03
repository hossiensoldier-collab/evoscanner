#!/usr/bin/env python3
"""
EvoScanner v0.1 — بدون کتابخانه خارجی
فقط با کتابخانه استاندارد پایتون
"""

import asyncio
import hashlib
import json
import re
import sqlite3
import ssl
import sys
import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

# تنظیمات
HOME = Path.home()
BASE_DIR = HOME / "evoscanner"
BASE_DIR.mkdir(exist_ok=True)
DB_PATH = BASE_DIR / "knowledge.db"
EVO_PATH = BASE_DIR / "evolution.json"

# SSL بدون بررسی (برای دور زدن خطاهای فیلترینگ)
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

UA = {"User-Agent": "EvoScanner/0.1"}


# ─────────────────────────────────────────────
# پایگاه دانش
# ─────────────────────────────────────────────

class KB:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS resources(
                hash TEXT PRIMARY KEY,
                url TEXT,
                title TEXT,
                content TEXT,
                source TEXT,
                score REAL,
                found_at TEXT
            )""")
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS queries(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT,
                source TEXT,
                new_hits INTEGER,
                ts TEXT
            )""")
        self.conn.commit()

    def add(self, url, title, content, source, score=0.5):
        h = hashlib.sha256((url + title).encode()).hexdigest()[:16]
        try:
            self.conn.execute(
                "INSERT INTO resources VALUES (?,?,?,?,?,?,?)",
                (h, url, title, content[:1000], source, score,
                 datetime.now().isoformat())
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def log(self, q, src, new):
        self.conn.execute(
            "INSERT INTO queries(query, source, new_hits, ts) VALUES (?,?,?,?)",
            (q, src, new, datetime.now().isoformat())
        )
        self.conn.commit()

    def total(self):
        return self.conn.execute(
            "SELECT COUNT(*) FROM resources"
        ).fetchone()[0]

    def stats(self):
        return self.conn.execute(
            "SELECT source, COUNT(*), AVG(score) FROM resources GROUP BY source"
        ).fetchall()

    def search(self, term, limit=20):
        return self.conn.execute(
            """SELECT source, title, url, score FROM resources
               WHERE title LIKE ? OR content LIKE ?
               ORDER BY score DESC LIMIT ?""",
            (f"%{term}%", f"%{term}%", limit)
        ).fetchall()

    def best_queries(self, limit=10):
        return self.conn.execute(
            """SELECT query, SUM(new_hits) as t FROM queries
               GROUP BY query ORDER BY t DESC LIMIT ?""",
            (limit,)
        ).fetchall()


# ─────────────────────────────────────────────
# ابزار HTTP بدون کتابخانه خارجی
# ─────────────────────────────────────────────

def http_get(url, timeout=20):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as r:
        return r.read().decode("utf-8", errors="ignore")


# ─────────────────────────────────────────────
# اسکنرها
# ─────────────────────────────────────────────

def scan_github(query, n=5):
    url = "https://api.github.com/search/repositories?" + urllib.parse.urlencode({
        "q": f"{query} language:python",
        "sort": "stars",
        "order": "desc",
        "per_page": n,
    })
    try:
        data = json.loads(http_get(url))
        out = []
        for it in data.get("items", []):
            out.append({
                "url": it["html_url"],
                "title": it["full_name"],
                "content": (it.get("description") or "")[:500],
                "source": "github",
                "score": min(it.get("stargazers_count", 0) / 10000, 1.0),
            })
        return out
    except Exception as e:
        print(f"  ! github: {e}")
        return []


def scan_arxiv(query, n=5):
    url = "http://export.arxiv.org/api/query?" + urllib.parse.urlencode({
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": n,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    })
    try:
        text = http_get(url)
        root = ET.fromstring(text)
        ns = {"a": "http://www.w3.org/2005/Atom"}
        out = []
        for e in root.findall("a:entry", ns):
            title = e.find("a:title", ns).text.strip().replace("\n", " ")
            summary = e.find("a:summary", ns).text.strip().replace("\n", " ")
            link = e.find("a:id", ns).text
            out.append({
                "url": link,
                "title": title,
                "content": summary[:600],
                "source": "arxiv",
                "score": 0.85,
            })
        return out
    except Exception as e:
        print(f"  ! arxiv: {e}")
        return []


def scan_pypi(query, n=5):
    """جستجوی PyPI — از endpoint JSON استفاده می‌کند"""
    url = "https://pypi.org/simple/"
    # جستجو از طریق search — ساده‌ترین راه: regex روی HTML
    try:
        text = http_get(f"https://pypi.org/search/?q={urllib.parse.quote(query)}")
        names = re.findall(
            r'package-snippet__name">([^<]+)<', text
        )[:n]
        out = []
        for name in names:
            out.append({
                "url": f"https://pypi.org/project/{name}/",
                "title": name,
                "content": f"PyPI package: {name}",
                "source": "pypi",
                "score": 0.7,
            })
        return out
    except Exception as e:
        print(f"  ! pypi: {e}")
        return []


# ─────────────────────────────────────────────
# موتور خودتکاملی
# ─────────────────────────────────────────────

BASE_TOPICS = [
    "python asyncio",
    "python machine learning",
    "python typing",
    "python testing",
    "python performance",
    "python web framework",
    "python security",
    "python design patterns",
]

MUTATORS = [
    "{} 2025",
    "best {}",
    "advanced {}",
    "{} benchmark",
    "{} tutorial",
]


class Evolver:
    def __init__(self, kb):
        self.kb = kb
        self.state = self._load()

    def _load(self):
        if EVO_PATH.exists():
            return json.loads(EVO_PATH.read_text())
        return {"cycle": 0, "active": list(BASE_TOPICS),
                "retired": [], "history": []}

    def _save(self):
        EVO_PATH.write_text(json.dumps(self.state, indent=2))

    def next_queries(self, n=6):
        best = [q for q, _ in self.kb.best_queries(5)]
        pool = list(dict.fromkeys(best + self.state["active"]))
        return pool[:n]

    def evolve(self):
        self.state["cycle"] += 1
        scores = {q: t for q, t in self.kb.best_queries(50)}

        survivors = []
        for q in self.state["active"]:
            if q not in scores or scores[q] > 0:
                survivors.append(q)
            else:
                self.state["retired"].append(q)

        if scores:
            import random
            best_q = max(scores, key=scores.get)
            for _ in range(3):
                new = random.choice(MUTATORS).format(best_q)
                if new not in survivors:
                    survivors.append(new)

        while len(survivors) < 8:
            for t in BASE_TOPICS:
                if t not in survivors:
                    survivors.append(t)
                    break

        self.state["active"] = survivors[:12]
        self.state["history"].append({
            "cycle": self.state["cycle"],
            "active": len(survivors),
            "ts": datetime.now().isoformat(),
        })
        self._save()
        return self.state["active"]


# ─────────────────────────────────────────────
# حلقه اصلی
# ─────────────────────────────────────────────

def one_cycle(kb, evo, queries):
    cycle = evo.state["cycle"] + 1
    print(f"\n═══ چرخه {cycle} ═══")
    print(f"کوئری‌ها: {queries}")

    total_new = 0
    for q in queries:
        for scanner_name, fn in [("github", scan_github),
                                  ("arxiv", scan_arxiv),
                                  ("pypi", scan_pypi)]:
            results = fn(q)
            new = 0
            for r in results:
                if kb.add(r["url"], r["title"], r["content"],
                          r["source"], r["score"]):
                    new += 1
                    total_new += 1
                    print(f"  + [{r['source']}] {r['title'][:70]}")
            kb.log(q, scanner_name, new)

    print(f"\nجدید: {total_new} | کل: {kb.total()}")
    evo.evolve()
    return total_new


def show_stats(kb, evo):
    print("\n📊 پایگاه دانش:")
    for src, cnt, avg in kb.stats():
        print(f"  {src:10s} {cnt:5d} مورد | میانگین {avg:.2f}")
    print(f"  کل: {kb.total()}")
    print(f"  چرخه: {evo.state['cycle']}")


def main():
    kb = KB()
    evo = Evolver(kb)

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "stats":
            show_stats(kb, evo)
            return
        if cmd == "search":
            term = sys.argv[2] if len(sys.argv) > 2 else "python"
            for src, title, url, score in kb.search(term):
                print(f"[{src}] {score:.2f} {title}")
                print(f"   {url}")
            return
        if cmd == "queries":
            for q in evo.state["active"]:
                print(f"  • {q}")
            return
        if cmd == "run":
            n = int(sys.argv[2]) if len(sys.argv) > 2 else 3
            for i in range(n):
                queries = evo.next_queries(6)
                one_cycle(kb, evo, queries)
                if i < n - 1:
                    print("  انتظار ۱۰ ثانیه...")
                    time.sleep(10)
            show_stats(kb, evo)
            return

    # پیش‌فرض: یک چرخه
    queries = evo.next_queries(6)
    one_cycle(kb, evo, queries)
    show_stats(kb, evo)


if __name__ == "__main__":
    main()
