"""Metadata Extractor — استخراج کارت کامل از هر منبع"""
import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path

BASE = Path.home() / "evoscanner"
DB = BASE / "knowledge.db"

# جدول فراداده
META_SCHEMA = """
CREATE TABLE IF NOT EXISTS resource_meta (
    hash TEXT PRIMARY KEY,
    type TEXT,
    domains TEXT,
    complexity TEXT,
    python_version TEXT,
    dependencies TEXT,
    alternatives TEXT,
    used_with TEXT,
    when_to_use TEXT,
    when_not TEXT,
    install_cmd TEXT,
    minimal_example TEXT,
    docs_url TEXT,
    source_url TEXT,
    changelog_url TEXT,
    issues_url TEXT,
    extracted_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_meta_type ON resource_meta(type);
CREATE INDEX IF NOT EXISTS idx_meta_domains ON resource_meta(domains);
CREATE INDEX IF NOT EXISTS idx_meta_complexity ON resource_meta(complexity);
"""


def ensure_schema(kb):
    kb.conn.executescript(META_SCHEMA)
    kb.conn.commit()


# ─── تشخیص نوع منبع ───
TYPE_PATTERNS = {
    "library":     [r"pip install", r"import ", r"from .* import"],
    "framework":   [r"framework", r"built on top", r"foundation"],
    "cli-tool":    [r"command line", r"cli", r"usage: "],
    "tutorial":    [r"tutorial", r"step-by-step", r"getting started"],
    "article":     [r"blog", r"article", r"read more"],
    "paper":       [r"arxiv", r"abstract", r"we propose"],
    "awesome":     [r"awesome", r"curated", r"collection"],
    "cheatsheet":  [r"cheat sheet", r"quick reference"],
    "course":      [r"course", r"lesson", r"chapter"],
}


def detect_type(title, content):
    text = ((title or "") + " " + (content or "")).lower()
    scores = {}
    for t, pats in TYPE_PATTERNS.items():
        s = sum(1 for p in pats if re.search(p, text))
        if s:
            scores[t] = s
    if not scores:
        return "resource"
    return max(scores, key=scores.get)


# ─── تشخیص دامنه ───
DOMAINS = {
    "web":         [r"flask|django|fastapi|starlette|aiohttp|sanic"],
    "async":       [r"asyncio|await|coroutine|aio"],
    "ml":          [r"machine learning|neural|model|training"],
    "dl":          [r"pytorch|tensorflow|keras|jax|deep learning"],
    "nlp":         [r"nlp|token|embedding|transformer|bert|gpt"],
    "cv":          [r"opencv|image|vision|yolo"],
    "data":        [r"pandas|numpy|polars|dataframe"],
    "db":          [r"sql|postgres|mysql|sqlite|mongo"],
    "graphics":    [r"matplotlib|pygame|opengl|pillow|plotly"],
    "automation":  [r"selenium|playwright|pyautogui|schedule"],
    "testing":     [r"pytest|unittest|hypothesis|mock"],
    "devops":      [r"docker|kubernetes|ci/cd|ansible"],
    "security":    [r"crypto|jwt|encrypt|auth"],
    "parsing":     [r"parse|regex|beautifulsoup|lxml|scrapy"],
    "cli":         [r"click|typer|argparse|rich"],
}


def detect_domains(text):
    text = (text or "").lower()
    out = []
    for d, pats in DOMAINS.items():
        for p in pats:
            if re.search(p, text):
                out.append(d)
                break
    return out[:5]


# ─── وابستگی‌ها ───
def extract_deps(text):
    if not text:
        return []
    pats = [
        r"pip\s+install\s+([a-zA-Z][a-zA-Z0-9_\-]{1,30})",
        r"(?:requires|depend(?:s|ency)?)\s*:?\s*([a-zA-Z][a-zA-Z0-9_\-]{1,30})",
    ]
    deps = set()
    STOP = {"python", "pip", "install", "the", "and", "for"}
    for p in pats:
        for m in re.findall(p, text, re.I):
            m = m.lower()
            if m not in STOP and len(m) > 2:
                deps.add(m)
    return list(deps)[:15]


# ─── جایگزین‌ها از گراف ───
def find_alternatives(graph, pkg):
    """پکیج‌های هم‌دسته = جایگزین‌های بالقوه"""
    try:
        nodes = graph.get("nodes", {})
        info = nodes.get(pkg.lower(), {})
        cats = info.get("cats", {})
        if not cats:
            return []
        main = max(cats, key=cats.get)
        out = []
        for n, v in nodes.items():
            if v.get("type") != "entity" or n == pkg.lower():
                continue
            if v.get("cats", {}).get(main):
                out.append(n)
        return out[:8]
    except Exception:
        return []


# ─── زمان استفاده ───
def when_to_use(title, content, domain_list):
    if not domain_list:
        return ""
    dom = domain_list[0]
    hints = {
        "web":        "برای ساخت API یا وب‌سایت",
        "async":      "برای عملیات همزمان و I/O-bound",
        "ml":         "برای یادگیری ماشین کلاسیک",
        "dl":         "برای یادگیری عمیق و شبکه عصبی",
        "nlp":        "برای پردازش متن و زبان",
        "cv":         "برای پردازش تصویر و بینایی",
        "data":       "برای تحلیل داده و DataFrame",
        "db":         "برای ذخیره‌سازی و کوئری داده",
        "graphics":   "برای رندر و رسم گرافیکی",
        "automation": "برای خودکارسازی و وب‌اسکرپینگ",
        "testing":    "برای تست نرم‌افزار",
        "devops":     "برای استقرار و CI/CD",
        "security":   "برای رمزنگاری و احراز هویت",
        "parsing":    "برای پارس و استخراج داده",
        "cli":        "برای ابزارهای خط فرمان",
    }
    return hints.get(dom, "")


# ─── نصب ───
def detect_install(title, content):
    if not title or "/" not in title:
        return ""
    repo = title.split("/")[-1]
    if content and f"pip install {repo}" in content.lower():
        return f"pip install {repo}"
    return f"pip install {repo.lower()}"


# ─── مثال حداقلی ───
def find_minimal_example(content):
    if not content:
        return ""
    blocks = re.findall(r"```(?:python|py)?\s*\n([\s\S]*?)```", content)
    for b in blocks:
        b = b.strip()
        if 20 < len(b) < 400:
            return b
    return blocks[0][:300] if blocks else ""


# ─── URLهای مرتبط ───
def extract_urls(content, base_url=""):
    out = {"docs": "", "source": "", "changelog": "", "issues": ""}
    if not content:
        return out
    urls = re.findall(r'https?://[^\s\)\]\"]+', content)
    for u in urls[:30]:
        ul = u.lower()
        if "docs" in ul and not out["docs"]:
            out["docs"] = u
        elif "changelog" in ul and not out["changelog"]:
            out["changelog"] = u
        elif "/issues" in ul and not out["issues"]:
            out["issues"] = u
        elif "github.com" in ul and not out["source"]:
            out["source"] = u
    return out


# ─── استخراج کامل ───
def extract_one(kb, graph, hash_, title, content, url):
    title = title or ""
    content = content or ""
    text = title + "\n" + content

    rtype = detect_type(title, content)
    domains = detect_domains(text)
    deps = extract_deps(content)

    pkg = title.split("/")[-1].lower() if "/" in title else title.lower()
    alternatives = find_alternatives(graph, pkg)

    meta = {
        "hash": hash_,
        "type": rtype,
        "domains": ",".join(domains),
        "complexity": classify_complexity(content),
        "python_version": detect_python_version(content),
        "dependencies": ",".join(deps),
        "alternatives": ",".join(alternatives),
        "used_with": ",".join(alternatives[:5]),
        "when_to_use": when_to_use(title, content, domains),
        "when_not": "",
        "install_cmd": detect_install(title, content),
        "minimal_example": find_minimal_example(content),
        "docs_url": extract_urls(content)["docs"],
        "source_url": url or extract_urls(content)["source"],
        "changelog_url": extract_urls(content)["changelog"],
        "issues_url": extract_urls(content)["issues"],
        "extracted_at": datetime.now().isoformat(),
    }
    return meta


def classify_complexity(text):
    if not text:
        return "intermediate"
    t = text.lower()
    if any(w in t for w in ["getting started", "basics", "hello world"]):
        return "beginner"
    if any(w in t for w in ["optimization", "internals", "compiler"]):
        return "advanced"
    if any(w in t for w in ["gpu", "shader", "vulkan", "kernel"]):
        return "specialist"
    return "intermediate"


def detect_python_version(content):
    if not content:
        return ""
    m = re.search(r"python\s*(?:>=|>|requires?\s*:?\s*)?(\d\.\d+)", content, re.I)
    return m.group(1) if m else ""


# ─── اجرای گروهی ───
def extract_all(kb, limit=1000):
    ensure_schema(kb)

    graph = {}
    gfile = BASE / "graph.json"
    if gfile.exists():
        try:
            graph = json.loads(gfile.read_text())
        except Exception:
            pass

    rows = kb.conn.execute(
        "SELECT hash, title, content, url FROM resources "
        "WHERE length(COALESCE(content,'')) > 100 LIMIT ?", (limit,)
    ).fetchall()

    print(f"\n📇 استخراج فراداده از {len(rows)} منبع...\n")

    n_ok = 0
    for h, t, c, u in rows:
        try:
            m = extract_one(kb, graph, h, t, c, u or "")
            kb.conn.execute(
                """INSERT OR REPLACE INTO resource_meta
                   (hash,type,domains,complexity,python_version,
                    dependencies,alternatives,used_with,when_to_use,
                    when_not,install_cmd,minimal_example,docs_url,
                    source_url,changelog_url,issues_url,extracted_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (m["hash"], m["type"], m["domains"], m["complexity"],
                 m["python_version"], m["dependencies"],
                 m["alternatives"], m["used_with"], m["when_to_use"],
                 m["when_not"], m["install_cmd"],
                 m["minimal_example"][:500], m["docs_url"],
                 m["source_url"], m["changelog_url"],
                 m["issues_url"], m["extracted_at"])
            )
            n_ok += 1
            if n_ok % 50 == 0:
                print(f"  {n_ok}/{len(rows)}")
        except Exception as e:
            print(f"  ! {t[:40]}: {e}")
            continue

    kb.conn.commit()
    print(f"\n✓ {n_ok} فراداده ذخیره شد")
    return n_ok


def stats(kb):
    ensure_schema(kb)
    print("\n=== Metadata Stats ===\n")
    n = kb.conn.execute("SELECT COUNT(*) FROM resource_meta").fetchone()[0]
    print(f"  کل: {n}")
    print("\n  توسط type:")
    for t, c in kb.conn.execute(
            "SELECT type, COUNT(*) FROM resource_meta GROUP BY type "
            "ORDER BY COUNT(*) DESC").fetchall():
        print(f"    {t:14s} {c}")
    print("\n  توسط complexity:")
    for t, c in kb.conn.execute(
            "SELECT complexity, COUNT(*) FROM resource_meta GROUP BY complexity "
            "ORDER BY COUNT(*) DESC").fetchall():
        print(f"    {t:14s} {c}")
    print("\n  top domains:")
    dom_count = {}
    for (d,) in kb.conn.execute("SELECT domains FROM resource_meta").fetchall():
        for x in (d or "").split(","):
            if x:
                dom_count[x] = dom_count.get(x, 0) + 1
    for d, c in sorted(dom_count.items(), key=lambda x: -x[1])[:10]:
        print(f"    {d:14s} {c}")


def find_by_type(kb, t):
    ensure_schema(kb)
    rows = kb.conn.execute(
        "SELECT r.title, r.url, m.install_cmd, m.when_to_use "
        "FROM resource_meta m JOIN resources r ON r.hash = m.hash "
        "WHERE m.type = ? ORDER BY r.score DESC LIMIT 20", (t,)
    ).fetchall()
    print(f"\n  [{t}] {len(rows)} مورد:\n")
    for title, url, install, when in rows:
        print(f"    {title[:50]:50s} {url}")
        if install:
            print(f"      → {install}")
        if when:
            print(f"      {when}")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(BASE))
    from evoscanner_v2 import KB
    kb = KB()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "extract"
    if cmd == "extract":
        extract_all(kb)
    elif cmd == "stats":
        stats(kb)
    elif cmd == "type" and len(sys.argv) > 2:
        find_by_type(kb, sys.argv[2])
    elif cmd == "card" and len(sys.argv) > 2:
        ensure_schema(kb)
        row = kb.conn.execute(
            "SELECT * FROM resource_meta m JOIN resources r "
            "ON r.hash = m.hash WHERE LOWER(r.title) LIKE ?",
            (f"%{sys.argv[2].lower()}%",)).fetchone()
        if row:
            print(row)
        else:
            print("not found")

