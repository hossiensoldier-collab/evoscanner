"""Causal-G — گراف علّی جهت‌دار با استخراج LLM + regex fallback"""
import json
import os
import re
import subprocess
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

BASE = Path.home() / "evoscanner"
GRAPH_FILE = BASE / "causal_graph.json"
CACHE_FILE = BASE / "causal_cache.json"

# ═══════════════════════════════════════════════════
#  دسته‌بندی فعل‌ها
# ═══════════════════════════════════════════════════

VERB_CATEGORIES = {
    "requires": {
        "weight": 1.0,
        "patterns": [
            r"(\w[\w\-]+)\s+(?:requires?|needs?|depends? on|must have)\s+(\w[\w\-]+)",
            r"(\w[\w\-]+)\s+is\s+required\s+by\s+(\w[\w\-]+)",
            r"(\w[\w\-]+)\s+is\s+needed\s+for\s+(\w[\w\-]+)",
        ],
    },
    "uses": {
        "weight": 0.8,
        "patterns": [
            r"(\w[\w\-]+)\s+(?:uses?|utilizes?|relies on|leverages?)\s+(\w[\w\-]+)",
            r"(\w[\w\-]+)\s+is\s+powered\s+by\s+(\w[\w\-]+)",
        ],
    },
    "extends": {
        "weight": 0.7,
        "patterns": [
            r"(\w[\w\-]+)\s+(?:extends?|builds? on|is based on)\s+(\w[\w\-]+)",
            r"(\w[\w\-]+)\s+is\s+a\s+(?:fork|wrapper|extension)\s+of\s+(\w[\w\-]+)",
        ],
    },
    "complements": {
        "weight": 0.6,
        "patterns": [
            r"(\w[\w\-]+)\s+(?:works? with|integrates? with|is compatible with)\s+(\w[\w\-]+)",
            r"(\w[\w\-]+)\s+and\s+(\w[\w\-]+)\s+work\s+well\s+together",
        ],
    },
    "replaces": {
        "weight": 0.5,
        "patterns": [
            r"(\w[\w\-]+)\s+(?:replaces?|is alternative to|instead of)\s+(\w[\w\-]+)",
            r"(\w[\w\-]+)\s+can\s+replace\s+(\w[\w\-]+)",
        ],
    },
    "competes": {
        "weight": 0.4,
        "patterns": [
            r"(\w[\w\-]+)\s+(?:vs\.?|versus)\s+(\w[\w\-]+)",
            r"(\w[\w\-]+)\s+competes?\s+with\s+(\w[\w\-]+)",
        ],
    },
}

STOP_WORDS = {
    "the", "a", "an", "and", "or", "of", "in", "on", "to", "for",
    "with", "is", "are", "was", "were", "be", "been", "this", "that",
    "it", "as", "at", "by", "if", "not", "you", "can", "will",
    "have", "has", "had", "do", "does", "did", "but", "from",
    "python", "py", "code", "file", "files", "use", "using", "used",
}


_KNOWN_PKGS = None
_KNOWN_PKGS_FILE = Path.home() / "evoscanner" / "graph.json"


NOISE_WORDS = {
    "examples", "example", "project", "projects", "your", "our",
    "their", "user", "users", "team", "teams", "only", "also",
    "with", "without", "using", "used", "such", "these", "those",
    "many", "much", "more", "less", "very", "well", "also",
    "data", "file", "files", "code", "codebase", "source",
    "library", "libraries", "package", "packages", "module",
    "modules", "test", "tests", "testing", "example",
    "python", "pypi", "pip", "install", "setup", "build",
    "docs", "documentation", "readme", "license", "version",
    "stable", "latest", "release", "releases", "branch",
    "feature", "features", "support", "supports", "help",
    "tools", "tool", "script", "scripts", "run", "runs",
    "work", "works", "working", "add", "adds", "make",
    "makes", "use", "uses", "used", "need", "needs",
    "require", "requires", "required", "depend", "depends",
    "based", "built", "comes", "gives", "provides", "includes",
    "means", "shows", "defines", "allows", "enables", "renders",
    "creates", "generates", "manages", "handles", "returns",
    "another", "other", "both", "each", "every", "some",
    "one", "two", "three", "first", "second", "third",
    "new", "old", "current", "previous", "next", "nextjs",
    "cli", "api", "sdk", "app", "apps", "demo", "demos",
    "config", "settings", "env", "environment",
    "main", "core", "base", "common", "utils", "helper",
    "start", "stop", "init", "setup", "install", "uninstall",
    "quick", "start", "quickstart", "tutorial", "guide",
    "note", "notes", "warning", "info", "error", "errors",
    "todo", "fixme", "deprecated", "experimental", "beta",
    "alpha", "stable", "unstable", "production", "dev",
    "development", "prod", "local", "remote", "server",
    "client", "host", "port", "url", "path", "dir",
    "directory", "folder", "extension", "extensions",
}


def _load_known_pkgs():
    """پکیج‌ها از گراف — با فیلتر قوی"""
    global _KNOWN_PKGS
    if _KNOWN_PKGS is not None:
        return _KNOWN_PKGS

    pkgs = set()
    try:
        g = json.loads(_KNOWN_PKGS_FILE.read_text())
        for name, v in g.get("nodes", {}).items():
            if v.get("type") != "entity":
                continue
            if name.startswith("cat:"):
                continue
            if name.lower() in NOISE_WORDS:
                continue
            if len(name) < 4:
                continue
            # فقط موجودیت‌هایی که حداقل ۲ بار دیده شده‌اند
            if v.get("count", 0) >= 2:
                pkgs.add(name.lower())
    except Exception:
        pass

    # whitelist معروف‌ها — حتی با count=1
    famous = [
        "fastapi", "django", "flask", "starlette", "sanic", "tornado",
        "aiohttp", "httpx", "requests", "urllib3", "uvicorn",
        "pydantic", "sqlalchemy", "alembic", "peewee", "sqlmodel",
        "numpy", "pandas", "polars", "pytorch", "torch", "tensorflow",
        "scikit-learn", "sklearn", "xgboost", "lightgbm", "catboost",
        "transformers", "huggingface", "datasets", "accelerate",
        "langchain", "llama-index", "openai", "anthropic", "ollama",
        "pytest", "hypothesis", "tox", "nox", "unittest", "mock",
        "pytest-asyncio", "pytest-cov", "pytest-mock",
        "celery", "dramatiq", "rq", "airflow", "prefect", "dagster",
        "matplotlib", "seaborn", "plotly", "bokeh", "altair",
        "pillow", "opencv", "opencv-python", "scikit-image",
        "pygame", "pyglet", "arcade",
        "scrapy", "beautifulsoup4", "lxml", "selenium", "playwright",
        "redis", "pymongo", "asyncpg", "psycopg2", "mysql",
        "boto3", "kubernetes", "docker",
        "click", "typer", "rich", "textual",
        "loguru", "structlog", "sentry-sdk", "opentelemetry",
        "gradio", "streamlit", "dash", "panel",
        "spacy", "nltk", "gensim",
        "networkx", "igraph",
        "faker", "marshmallow", "attrs",
        "orjson", "ujson", "pyyaml", "toml",
        "poetry", "hatch", "setuptools", "wheel",
        "uvloop", "httptools",
        "mypy", "pyright", "black", "ruff", "flake8", "isort",
        "jupyter", "ipython", "notebook",
        "numba", "cython", "pybind11",
        "grpc", "protobuf", "msgpack",
        "cryptography", "pyjwt", "bcrypt", "passlib",
        "jinja2", "markupsafe",
        "pymupdf", "pdfplumber",
        "openpyxl", "xlsxwriter",
        "websockets",
        "dask", "ray", "joblib",
        "anyio", "trio", "curio",
        "aiofiles", "aioredis", "aiomysql",
        "scipy", "sympy", "statsmodels",
        "dowhy", "causal-learn",
        "skrub", "skope-rules",
        "pytermgui", "pyfiglet",
    ]
    pkgs.update(famous)

    _KNOWN_PKGS = pkgs
    return pkgs



def is_package_name(s):
    """فقط پکیج‌های whitelist"""
    if not s:
        return False
    s = s.strip().lower()
    if len(s) < 3 or len(s) > 40:
        return False
    if s in NOISE_WORDS:
        return False
    if not re.match(r'^[a-z][a-z0-9_\-\.]*$', s):
        return False

    known = _load_known_pkgs()
    if s in known:
        return True
    # زیررشته
    for k in known:
        if len(k) >= 5 and (k == s or s.startswith(k + "-")
                            or s.startswith(k + "_")):
            return True
    return False



# ═══════════════════════════════════════════════════
#  استخراج regex (fallback + سریع)
# ═══════════════════════════════════════════════════

def extract_regex(text):
    """استخراج رابطه از متن با regex"""
    text_l = text.lower()
    relations = []

    for cat, spec in VERB_CATEGORIES.items():
        for pat in spec["patterns"]:
            for m in re.finditer(pat, text_l, re.IGNORECASE):
                a = m.group(1).strip()
                b = m.group(2).strip()
                if is_package_name(a) and is_package_name(b):
                    if a != b:
                        relations.append({
                            "a": a, "b": b, "cat": cat,
                            "weight": spec["weight"],
                            "source": "regex",
                        })

    return relations


# ═══════════════════════════════════════════════════
#  استخراج LLM
# ═══════════════════════════════════════════════════

def llm_available():
    """چک می‌کند LLM کار می‌کند"""
    try:
        import ai_agent
        key = ai_agent.get_key()
        return bool(key)
    except Exception:
        return False


def extract_llm_batch(sentences, timeout=60):
    """استخراج با LLM — یک batch از جملات"""
    if not sentences:
        return []

    # متن ترکیبی
    text = "\n".join(f"- {s}" for s in sentences)

    prompt = f"""You are a causal relationship extractor for Python packages.

Given sentences about Python packages, extract relationships in this JSON format:

[
  {{"a": "package1", "b": "package2", "relation": "requires|uses|extends|complements|replaces|competes"}},
  ...
]

Rules:
- Only extract relationships between two package names (not generic words)
- "requires" = a depends on b to work
- "uses" = a uses b as a tool
- "extends" = a builds on top of b
- "complements" = a and b work well together
- "replaces" = a is an alternative to b
- "competes" = a and b are competitors
- Ignore generic words (the, python, code, etc.)
- Return ONLY the JSON array, nothing else

Sentences:
{text}

JSON output:"""

    try:
        import ai_agent
        import urllib.request
        import ssl

        cfg = ai_agent.load_config()
        prov = cfg.get("provider", "groq")
        p = ai_agent.PROVIDERS.get(prov)
        if not p:
            print(f"  ! provider na-motabar: {prov}")
            return []

        # مدل‌های به‌روز
        MODELS = {
            "groq": "llama-3.3-70b-versatile",
            "openrouter": "meta-llama/llama-3.3-70b-instruct:free",
            "deepinfra": "meta-llama/Meta-Llama-3.1-8B-Instruct",
            "together": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
        }
        model = MODELS.get(prov, p.get("model", ""))

        body = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 2000,
        }).encode()

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        req = urllib.request.Request(
            p["url"], data=body,
            headers={
                "Authorization": "Bearer " + cfg.get("api_key", ""),
                "Content-Type": "application/json",
                "User-Agent": "EvoScanner-Causal",
            })

        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            data = json.loads(r.read())
            text = data["choices"][0]["message"]["content"]

        # پارس JSON
        text = text.strip()
        # حذف ```json
        text = re.sub(r'^```(?:json)?\s*', '', text)
        text = re.sub(r'\s*```\s*$', '', text)

        # پیدا کردن [ ... ]
        m = re.search(r'\[[\s\S]*\]', text)
        if not m:
            return []

        parsed = json.loads(m.group(0))

        out = []
        for item in parsed:
            a = item.get("a", "").strip().lower()
            b = item.get("b", "").strip().lower()
            rel = item.get("relation", "").strip().lower()
            if not (is_package_name(a) and is_package_name(b)):
                continue
            if a == b:
                continue
            if rel not in VERB_CATEGORIES:
                continue
            out.append({
                "a": a, "b": b, "cat": rel,
                "weight": VERB_CATEGORIES[rel]["weight"],
                "source": "llm",
            })
        return out

    except Exception as e:
        print(f"  ! LLM error: {str(e)[:80]}")
        return []


# ═══════════════════════════════════════════════════
#  گراف علّی
# ═══════════════════════════════════════════════════

def load_graph():
    if GRAPH_FILE.exists():
        try:
            return json.loads(GRAPH_FILE.read_text())
        except Exception:
            pass
    return {"edges": {}, "stats": {}}


def save_graph(g):
    GRAPH_FILE.write_text(json.dumps(g, indent=2, ensure_ascii=False))


def load_cache():
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text())
        except Exception:
            pass
    return {"processed": []}


def save_cache(c):
    CACHE_FILE.write_text(json.dumps(c, ensure_ascii=False))


def edge_key(a, b, cat):
    return f"{a}|{cat}|{b}"


def add_observation(graph, rel, source_score=0.5):
    """اضافه کردن یک مشاهده به گراف"""
    key = edge_key(rel["a"], rel["b"], rel["cat"])
    edges = graph.setdefault("edges", {})

    if key not in edges:
        edges[key] = {
            "a": rel["a"], "b": rel["b"], "cat": rel["cat"],
            "observations": 0,
            "total_weight": 0.0,
            "sources": [],
            "first_seen": datetime.now().isoformat(),
            "last_seen": datetime.now().isoformat(),
        }

    e = edges[key]
    e["observations"] += 1
    e["total_weight"] += rel["weight"] * source_score
    e["last_seen"] = datetime.now().isoformat()
    if rel.get("source"):
        e["sources"].append(rel["source"])
        e["sources"] = e["sources"][-20:]


def compute_confidence(edge):
    """محاسبه اطمینان بیزی"""
    # prior = 0.5، likelihood از مشاهدات
    n = edge.get("observations", 0)
    w = edge.get("total_weight", 0.0)
    if n == 0:
        return 0.0
    # posterior تقریبی: weight / (1 + weight)
    conf = w / (1.0 + w)
    # تنظیم برای تعداد کم
    if n < 3:
        conf *= 0.7
    return min(0.99, conf)


# ═══════════════════════════════════════════════════
#  ساخت گراف از منابع
# ═══════════════════════════════════════════════════

def get_sentences(kb, limit=500):
    """استخراج جملات از منابع"""
    rows = kb.conn.execute(
        """SELECT title, content, score FROM resources
           WHERE length(content) > 100 LIMIT ?""",
        (limit,)
    ).fetchall()

    known = _load_known_pkgs()

    sentences = []
    for title, content, score in rows:
        text = re.sub(r'```[\s\S]*?```', ' ', content)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\[.*?\]\(.*?\)', ' ', text)

        parts = re.split(r'(?<=[.!?])\s+|\n{2,}', text)
        for p in parts:
            p = p.strip()
            if not (30 < len(p) < 300):
                continue
            # فیلتر: جمله باید حداقل ۲ پکیج شناخته‌شده داشته باشد
            p_low = p.lower()
            hits = 0
            for k in known:
                if len(k) >= 5 and k in p_low:
                    hits += 1
                    if hits >= 2:
                        break
            if hits >= 2:
                sentences.append({
                    "text": p,
                    "title": title,
                    "score": score,
                })

    return sentences


def build(use_llm=True, limit=300, batch_size=15):
    """ساخت گراف علّی"""
    import sys
    sys.path.insert(0, str(BASE))
    from evoscanner_v2 import KB
    kb = KB()

    graph = load_graph()
    cache = load_cache()
    processed = set(cache.get("processed", []))

    print()
    print("=" * 60)
    print("  Causal-G — ساخت گراف علّی")
    print("=" * 60)
    print()

    print("  [1/3] استخراج جملات...")
    sentences = get_sentences(kb, limit=limit)
    # حذف تکراری
    seen = set()
    uniq = []
    for s in sentences:
        h = s["text"][:50]
        if h in seen:
            continue
        seen.add(h)
        uniq.append(s)
    print(f"        {len(uniq)} جمله یکتا")

    # regex (سریع، همیشه)
    print("  [2/3] استخراج regex...")
    regex_count = 0
    for s in uniq:
        rels = extract_regex(s["text"])
        for r in rels:
            add_observation(graph, r, source_score=s["score"])
            regex_count += 1
    print(f"        {regex_count} رابطه از regex")

    # LLM (کندتر، دقیق‌تر)
    if use_llm and llm_available():
        print("  [3/3] استخراج LLM...")
        llm_count = 0
        # فقط جملاتی که در cache نیستند
        todo = [s for s in uniq if s["text"][:80] not in processed]
        print(f"        {len(todo)} جمله برای LLM")

        for i in range(0, len(todo), batch_size):
            batch = todo[i:i + batch_size]
            texts = [s["text"] for s in batch]
            rels = extract_llm_batch(texts)
            for r in rels:
                add_observation(graph, r, source_score=0.7)
                llm_count += 1
            # ذخیره در cache
            for s in batch:
                processed.add(s["text"][:80])

            print(f"        batch {i//batch_size + 1}: "
                  f"+{len(rels)} رابطه")
            time.sleep(0.5)

        cache["processed"] = list(processed)
        save_cache(cache)
        print(f"        {llm_count} رابطه از LLM")
    else:
        print("  [3/3] LLM رد شد (بدون کلید یا خاموش)")

    # محاسبه اطمینان
    for key, e in graph.get("edges", {}).items():
        e["confidence"] = compute_confidence(e)

    graph["stats"] = {
        "edges": len(graph.get("edges", {})),
        "built_at": datetime.now().isoformat(),
        "regex_count": regex_count,
        "llm_count": llm_count if use_llm else 0,
    }
    save_graph(graph)

    print()
    print(f"  ✓ گراف ساخته شد: {graph['stats']['edges']} یال")
    print(f"    فایل: {GRAPH_FILE}")
    print()


# ═══════════════════════════════════════════════════
#  جستجو در گراف
# ═══════════════════════════════════════════════════

def get_relations(pkg, direction="both"):
    """روابط یک پکیج"""
    graph = load_graph()
    edges = graph.get("edges", {})
    pkg = pkg.lower()

    out = []
    for key, e in edges.items():
        if e["a"] == pkg and direction in ("both", "out"):
            out.append(("→", e["cat"], e["b"], e["confidence"],
                        e["observations"]))
        elif e["b"] == pkg and direction in ("both", "in"):
            out.append(("←", e["cat"], e["a"], e["confidence"],
                        e["observations"]))

    out.sort(key=lambda x: -x[3])
    return out


def show_requires(pkg):
    """چه چیزهایی نیاز دارد"""
    print()
    print(f"  {PU}{B}◆ requires {pkg}{R}")
    print()
    rels = get_relations(pkg, direction="out")
    if not rels:
        print(f"  {D}چیزی پیدا نشد{R}")
        return
    for arrow, cat, other, conf, n in rels[:20]:
        bar = "#" * int(conf * 20)
        col = GR if conf > 0.7 else (YL if conf > 0.4 else GY)
        print(f"  {col}{arrow} {cat:12s}{R} {WH}{other:25s}{R} "
              f"{col}{conf:.0%}{R}  {D}({n}){R}")


def show_breaks_if_removed(pkg):
    """اگر این پکیج حذف شود چه می‌شکند"""
    print()
    print(f"  {PU}{B}◆ breaks-if-removed {pkg}{R}")
    print()
    rels = get_relations(pkg, direction="in")
    requires = [r for r in rels if r[1] == "requires"]
    if not requires:
        print(f"  {D}هیچ پکیجی به آن وابسته نیست{R}")
        return
    print(f"  {YL}{len(requires)} پکیج به {pkg} وابسته‌اند:{R}")
    print()
    for arrow, cat, other, conf, n in requires[:15]:
        bar = "#" * int(conf * 20)
        col = RD if conf > 0.7 else (YL if conf > 0.4 else GY)
        print(f"  {col}{conf:.0%}{R}  {WH}{other:25s}{R}  {D}{bar}{R}")


def show_chain(pkg, max_depth=4):
    """زنجیره علّی"""
    print()
    print(f"  {PU}{B}◆ chain {pkg}{R}")
    print()

    graph = load_graph()
    edges = graph.get("edges", {})

    # BFS روی requires/uses
    visited = set()
    chain = []

    def dfs(node, depth, path):
        if depth > max_depth:
            return
        if node in visited:
            return
        visited.add(node)

        outs = [
            (e["cat"], e["b"], e["confidence"])
            for e in edges.values()
            if e["a"] == node and e["cat"] in ("requires", "uses")
        ]
        outs.sort(key=lambda x: -x[2])

        for cat, other, conf in outs[:3]:
            if other not in visited:
                chain.append((node, cat, other, conf))
                dfs(other, depth + 1, path + [other])

    dfs(pkg.lower(), 0, [pkg.lower()])

    if not chain:
        print(f"  {D}زنجیره‌ای پیدا نشد{R}")
        return

    for a, cat, b, conf in chain[:20]:
        col = GR if conf > 0.7 else YL
        print(f"  {WH}{a}{R} {col}--{cat}-->{R} {WH}{b}{R} "
              f"{D}({conf:.0%}){R}")


def show_predict(pkg):
    """پیش‌بینی بر اساس روند"""
    print()
    print(f"  {PU}{B}◆ predict {pkg}{R}")
    print()

    graph = load_graph()
    edges = graph.get("edges", {})
    pkg = pkg.lower()

    # جمع‌آوری: تعداد روابط ورودی و خروجی
    in_rel = [e for e in edges.values() if e["b"] == pkg]
    out_rel = [e for e in edges.values() if e["a"] == pkg]

    if not in_rel and not out_rel:
        print(f"  {D}داده کافی نیست{R}")
        return

    in_conf = sum(e.get("confidence", 0) for e in in_rel) / max(len(in_rel), 1)
    out_conf = sum(e.get("confidence", 0) for e in out_rel) / max(len(out_rel), 1)

    print(f"  {WH}input relations:{R}  {len(in_rel)}")
    print(f"  {WH}output relations:{R} {len(out_rel)}")
    print(f"  {WH}avg in confidence:{R}  {in_conf:.0%}")
    print(f"  {WH}avg out confidence:{R} {out_conf:.0%}")
    print()

    # پیش‌بینی
    if len(in_rel) >= 3 and in_conf > 0.6:
        print(f"  {GR}▸ احتمالاً پکیج مهمی است{R}")
        print(f"  {D}بسیاری از پکیج‌ها به آن نیاز دارند{R}")
    elif len(out_rel) >= 5:
        print(f"  {GR}▸ پکیج وابسته{R}")
        print(f"  {D}به چیزهای زیادی نیاز دارد{R}")
    else:
        print(f"  {YL}▸ اطلاعات کم — داده بیشتری لازم است{R}")


def show_stats():
    """آمار گراف علّی"""
    graph = load_graph()
    edges = graph.get("edges", {})
    stats = graph.get("stats", {})

    print()
    print(f"  {PU}{B}◆ Causal-G Stats{R}")
    print()

    if not edges:
        print(f"  {D}گراف ساخته نشده. اجرا کن: python feature_causal.py build{R}")
        return

    # per category
    cats = Counter(e["cat"] for e in edges.values())

    print(f"  {WH}کل یال‌ها:{R} {len(edges)}")
    print(f"  {WH}ساخته شده:{R} {stats.get('built_at', '?')[:19]}")
    print()

    print(f"  {WH}per category:{R}")
    for cat, n in cats.most_common():
        weight = VERB_CATEGORIES.get(cat, {}).get("weight", 0)
        print(f"    {cat:15s} {n:5d}  (وزن {weight})")
    print()

    # بالاترین اطمینان
    top = sorted(edges.values(), key=lambda x: -x.get("confidence", 0))[:10]
    print(f"  {WH}بالاترین اطمینان:{R}")
    for e in top:
        col = GR if e["confidence"] > 0.7 else YL
        print(f"    {col}{e['confidence']:.0%}{R}  "
              f"{e['a']} --{e['cat']}--> {e['b']}")


# ═══════════════════════════════════════════════════
#  رنگ‌ها
# ═══════════════════════════════════════════════════

CY = "\033[38;2;100;220;230m"
WH = "\033[38;2;230;230;240m"
GY = "\033[38;2;130;135;150m"
GR = "\033[38;2;120;230;150m"
YL = "\033[38;2;255;215;80m"
PU = "\033[38;2;180;140;255m"
PK = "\033[38;2;255;140;200m"
RD = "\033[38;2;255;110;110m"
R = "\033[0m"
B = "\033[1m"
D = "\033[2m"


# ═══════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "stats"

    if cmd == "build":
        use_llm = "--no-llm" not in sys.argv
        limit = 300
        for a in sys.argv[2:]:
            if a.startswith("--limit="):
                limit = int(a.split("=")[1])
        build(use_llm=use_llm, limit=limit)
    elif cmd == "stats":
        show_stats()
    elif cmd == "requires" and len(sys.argv) > 2:
        show_requires(sys.argv[2])
    elif cmd == "breaks" and len(sys.argv) > 2:
        show_breaks_if_removed(sys.argv[2])
    elif cmd == "chain" and len(sys.argv) > 2:
        show_chain(sys.argv[2])
    elif cmd == "predict" and len(sys.argv) > 2:
        show_predict(sys.argv[2])
    elif cmd == "reset":
        if GRAPH_FILE.exists():
            GRAPH_FILE.unlink()
        if CACHE_FILE.exists():
            CACHE_FILE.unlink()
        print("✓ پاک شد")
    else:
        print("usage:")
        print("  python feature_causal.py build [--no-llm] [--limit=300]")
        print("  python feature_causal.py stats")
        print("  python feature_causal.py requires <pkg>")
        print("  python feature_causal.py breaks <pkg>")
        print("  python feature_causal.py chain <pkg>")
        print("  python feature_causal.py predict <pkg>")
        print("  python feature_causal.py reset")

