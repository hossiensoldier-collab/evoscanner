"""پیشنهاد کوئری برای پر کردن شکاف"""
import json
from pathlib import Path

BASE = Path.home() / "evoscanner"
EVO_FILE = BASE / "evolution.json"

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
    "performance": ["python numba jit", "cython tutorial",
                    "python memory profiler", "python async performance"],
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


def suggest(kb, top_n=5):
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
    print(f"\n📉 {len(weak)} دسته ضعیف — پیشنهاد کوئری:\n")
    for cat, cnt in weak[:top_n]:
        print(f"  ── {cat} ({cnt} منبع) ──")
        for q in GAP_QUERIES[cat][:3]:
            print(f"    • {q}")
            suggestions.append(q)
        print()

    if EVO_FILE.exists():
        try:
            state = json.loads(EVO_FILE.read_text())
            state.setdefault("suggested", [])
            state["suggested"] = list(dict.fromkeys(
                state["suggested"] + suggestions))[:30]
            state["active"] = list(dict.fromkeys(
                state["active"] + suggestions))[:25]
            EVO_FILE.write_text(json.dumps(state, indent=2))
            print(f"  ✓ {len(suggestions)} کوئری به لیست فعال اضافه شد")
            print(f"    در چرخه بعدی خودکار اجرا می‌شوند")
        except Exception as e:
            print(f"  ! خطا: {e}")

    return suggestions

