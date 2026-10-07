"""Feature Generator — تولید میلیون‌ها ایده قابلیت"""
import json
import random
from datetime import datetime
from pathlib import Path

BASE = Path.home() / "evoscanner"
OUT = BASE / "feature_ideas"
OUT.mkdir(exist_ok=True)

# ═══════════════════════════════════════════════════
#  فعل‌ها — کاری که قابلیت می‌کند
# ═══════════════════════════════════════════════════

VERBS = [
    # تحلیل
    "analyze", "profile", "inspect", "diagnose", "trace", "measure",
    "benchmark", "audit", "review", "evaluate", "score", "rank",
    "compare", "contrast", "diff", "correlate", "cluster", "classify",
    # پیش‌بینی
    "predict", "forecast", "estimate", "project", "simulate",
    "model", "infer", "extrapolate", "hypothesize",
    # تولید
    "generate", "create", "build", "craft", "compose", "synthesize",
    "assemble", "draft", "prototype", "mock", "sketch",
    # کشف
    "discover", "explore", "mine", "extract", "harvest", "scrape",
    "crawl", "aggregate", "collect", "gather", "survey", "scan",
    # بهینه‌سازی
    "optimize", "tune", "refine", "polish", "improve", "enhance",
    "boost", "accelerate", "compress", "shrink", "cache",
    # تبدیل
    "convert", "translate", "transform", "normalize", "reformat",
    "port", "migrate", "rewrite", "refactor", "modularize",
    # نگه‌داری
    "monitor", "watch", "track", "observe", "log", "record",
    "archive", "backup", "snapshot", "version", "restore",
    # یادگیری
    "learn", "train", "teach", "study", "practice", "memorize",
    "reinforce", "adapt", "evolve", "grow",
    # تعامل
    "interact", "chat", "ask", "answer", "respond", "reply",
    "notify", "alert", "warn", "remind", "suggest", "recommend",
    # شبکه
    "connect", "link", "bridge", "sync", "share", "publish",
    "broadcast", "stream", "tunnel", "proxy", "route",
    # تزئین
    "visualize", "render", "draw", "plot", "chart", "illustrate",
    "diagram", "animate", "style", "theme", "beautify",
    # امنیت
    "secure", "encrypt", "sign", "verify", "authenticate", "authorize",
    "protect", "sandbox", "isolate", "guard",
    # تست
    "test", "validate", "check", "assert", "probe", "fuzz",
    "stress", "load", "replay", "record-replay",
]

# ═══════════════════════════════════════════════════
#  اشیاء — روی چه چیزی عمل می‌کند
# ═══════════════════════════════════════════════════

OBJECTS = [
    # داده‌های موجود
    "resources", "knowledge base", "graph", "co-occurrence", "edges",
    "nodes", "entities", "categories", "techniques", "snippets",
    "concepts", "graphics_topics", "learn_paths", "queries",
    "patches", "files", "modules", "classes", "functions",
    # متادیتا
    "metadata", "tags", "annotations", "timestamps", "hashes",
    "scores", "ranks", "versions", "changelog",
    # گراف
    "graph structure", "subgraphs", "clusters", "communities",
    "paths", "cycles", "hubs", "bridges", "shortest paths",
    "centrality", "density", "pagerank",
    # هوش
    "predictions", "patterns", "insights", "hypotheses",
    "anomalies", "outliers", "trends", "signals", "recommendations",
    # منابع
    "GitHub repos", "arXiv papers", "StackOverflow Q&A",
    "Dev.to articles", "PyPI packages", "RSS feeds",
    "documentation", "cheatsheets", "tutorials",
    # فعل‌ها
    "user queries", "search history", "bookmarks", "sessions",
    "logs", "events", "triggers", "webhooks", "notifications",
    # حالت سیستم
    "performance", "memory", "cpu", "disk", "network",
    "battery", "temperature", "bandwidth",
    # امنیت
    "secrets", "tokens", "keys", "passwords", "certificates",
    "permissions", "access", "audit trail",
    # علم
    "learning paths", "curriculum", "progress", "mastery",
    "skills", "competency", "prerequisites",
    # گرافیک
    "rendering", "colors", "layout", "typography", "animations",
    "3D scenes", "shaders", "textures", "meshes",
    # AI
    "LLM responses", "prompts", "contexts", "embeddings",
    "vectors", "tokens", "generations",
]

# ═══════════════════════════════════════════════════
#  صفت‌ها — چطور عمل می‌کند
# ═══════════════════════════════════════════════════

MODIFIERS = [
    # سرعت
    "real-time", "fast", "instant", "incremental", "streaming",
    "async", "parallel", "concurrent", "background", "batched",
    # اندازه
    "scalable", "distributed", "sharded", "federated", "peer-to-peer",
    "edge", "mobile", "embedded", "minimal", "lightweight",
    # هوش
    "smart", "adaptive", "self-learning", "predictive", "contextual",
    "personalized", "customized", "dynamic", "semantic",
    # کیفیت
    "robust", "reliable", "accurate", "precise", "thorough",
    "deep", "comprehensive", "exhaustive", "curated",
    # ظاهر
    "beautiful", "elegant", "clean", "minimalist", "colorful",
    "interactive", "animated", "responsive", "accessible",
    # زبان
    "Persian", "Finglish", "multi-lingual", "translated",
    "natural-language", "voice", "chat", "conversational",
    # امنیت
    "encrypted", "private", "anonymous", "auditable", "sandboxed",
    "zero-trust", "verifiable", "signed",
    # خودکارسازی
    "automatic", "auto-scheduled", "event-driven", "cron",
    "trigger-based", "rule-based", "ML-driven",
    # توزیع
    "cloud", "local", "hybrid", "offline-capable", "sync",
    "p2p", "mesh", "on-premise",
    # تجربه
    "voice-controlled", "gesture", "keyboard-only", "touch",
    "one-click", "batch", "wizard-guided",
    # متا
    "self-improving", "self-healing", "self-documenting",
    "self-testing", "self-evolving", "meta",
    # پیشرفته
    "quantum-inspired", "neural", "graph-based", "probabilistic",
    "Bayesian", "fuzzy", "heuristic", "evolutionary",
]

# ═══════════════════════════════════════════════════
#  قالب‌های جمله
# ═══════════════════════════════════════════════════

TEMPLATES = [
    "{verb} {obj}",
    "{verb} {obj} {mod}",
    "{mod} {verb} of {obj}",
    "{verb} {obj} via {mod}",
    "{verb} {obj} for {mod} use",
    "{verb} {mod} {obj}",
    "auto-{verb} {obj}",
    "{verb} {obj} in real-time",
    "{verb} all {obj}",
    "{verb} {obj} with {mod}",
]


# ═══════════════════════════════════════════════════
#  تولید
# ═══════════════════════════════════════════════════

def total_combinations():
    """چند ترکیب ممکن"""
    n = len(VERBS) * len(OBJECTS) * (1 + len(MODIFIERS)) * len(TEMPLATES)
    return n


def generate_one():
    """یک قابلیت تصادفی"""
    v = random.choice(VERBS)
    o = random.choice(OBJECTS)
    m = random.choice(MODIFIERS)
    t = random.choice(TEMPLATES)
    text = t.format(verb=v, obj=o, mod=m)
    return {
        "text": text,
        "verb": v, "object": o, "modifier": m,
        "template": t,
    }


def generate_batch(n=100):
    """تولید n قابلیت یکتا"""
    seen = set()
    out = []
    tries = 0
    while len(out) < n and tries < n * 20:
        tries += 1
        f = generate_one()
        if f["text"] not in seen:
            seen.add(f["text"])
            out.append(f)
    return out


def save_batch(n=1000, tag="batch"):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    items = generate_batch(n)
    f = OUT / f"ideas_{tag}_{ts}.json"
    f.write_text(json.dumps(items, indent=2, ensure_ascii=False))
    return f, items


def report():
    total = total_combinations()
    print()
    print("=" * 60)
    print("  Feature Generator")
    print("=" * 60)
    print()
    print(f"  افعال:      {len(VERBS)}")
    print(f"  اشیاء:      {len(OBJECTS)}")
    print(f"  صفت‌ها:     {len(MODIFIERS)}")
    print(f"  قالب‌ها:     {len(TEMPLATES)}")
    print()
    print(f"  کل ترکیب ممکن: {total:,}")
    print()
    print(f"  نمونه ۱۰ ایده تصادفی:")
    print()
    for f in generate_batch(10):
        print(f"    • {f['text']}")
    print()


def generate_million():
    """تولید یک میلیون ترکیب (به فایل)"""
    print()
    print("  تولید 1,000,000 ترکیب...")
    print("  (ممکن است ۱-۲ دقیقه طول بکشد)")
    print()

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    f = OUT / f"million_{ts}.txt"

    seen = set()
    count = 0
    total = total_combinations()

    with f.open("w", encoding="utf-8") as out:
        while count < 1_000_000:
            item = generate_one()
            text = item["text"]
            if text in seen:
                continue
            seen.add(text)
            out.write(text + "\n")
            count += 1
            if count % 100_000 == 0:
                print(f"    {count:,}...")

    print()
    print(f"  ✓ {count:,} ایده ذخیره شد")
    print(f"  فایل: {f}")
    print(f"  حجم: {f.stat().st_size // 1024} KB")
    print()
    return f


def search_ideas(query, limit=20):
    """جستجو در ایده‌های تولیدشده"""
    files = sorted(OUT.glob("million_*.txt"), reverse=True)
    if not files:
        print("  ! هنوز میلیونی نساخته‌ای. اجرا کن: python feature_gen.py million")
        return

    latest = files[0]
    q = query.lower()
    results = []
    with latest.open() as f:
        for line in f:
            if q in line.lower():
                results.append(line.strip())
                if len(results) >= limit:
                    break

    print()
    print(f"  جستجوی '{query}' در {latest.name}")
    print(f"  {len(results)} نتیجه:")
    print()
    for r in results:
        print(f"    • {r}")
    print()


def pick_random(n=20):
    """انتخاب تصادفی از میلیونی"""
    files = sorted(OUT.glob("million_*.txt"), reverse=True)
    if not files:
        print("  ! اول million بساز")
        return

    latest = files[0]
    lines = latest.read_text().splitlines()
    picks = random.sample(lines, min(n, len(lines)))

    print()
    print(f"  {len(picks)} ایده تصادفی:")
    print()
    for p in picks:
        print(f"    • {p}")
    print()


def to_prompt(idea_text):
    """تبدیل یک ایده به پرامپت"""
    prompt = f"""پروژه EvoScanner — افزودن قابلیت جدید

## قابلیت

{idea_text}

## درباره پروژه

EvoScanner یک سیستم خودتکامل‌گر پایتون است:
- منابع را از GitHub, arXiv, StackOverflow, Dev.to جمع می‌کند
- تکنیک‌ها و کد استخراج می‌کند
- گراف دانش می‌سازد
- RAG محلی دارد
- پنل متنی + API + وب دارد
- ایجنت‌های خودکار دارد

محیط: Termux اندروید، فقط کتابخانه استاندارد، مسیر ~/evoscanner/

## درخواست

لطفاً:

۱. توضیح کوتاه — این قابلیت چه می‌کند
۲. کد کامل — `cat > feature_xxx.py << 'PYEOF' ... PYEOF`
۳. اسکریپت پچ برای `panel.py`
۴. دستور تست
۵. بدون توضیح اضافه

قیدها:
- فقط stdlib
- فرمت منو: `print(f"  {{C['Y']}}[N]{{C['D']}} Title  {{C['Dim']}}sub{{C['D']}}")`
- تابع `menu_xxx()` که با `0` برمی‌گردد
"""
    return prompt


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"

    if cmd == "report":
        report()
    elif cmd == "sample":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        for f in generate_batch(n):
            print(f"  • {f['text']}")
    elif cmd == "million":
        generate_million()
    elif cmd == "search" and len(sys.argv) > 2:
        search_ideas(" ".join(sys.argv[2:]))
    elif cmd == "random":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        pick_random(n)
    elif cmd == "prompt" and len(sys.argv) > 2:
        print(to_prompt(" ".join(sys.argv[2:])))

