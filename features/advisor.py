"""Package advisor — best package for a task"""
from pathlib import Path
import json

BASE = Path.home() / "evoscanner"

# نقشه کار → پکیج‌های کاندید
TASKS = {
    "web framework": ["fastapi", "django", "flask", "starlette", "sanic"],
    "http client": ["httpx", "requests", "aiohttp", "urllib3"],
    "async": ["asyncio", "anyio", "trio", "curio"],
    "testing": ["pytest", "unittest", "nose", "hypothesis", "tox"],
    "data frame": ["pandas", "polars", "dask", "modin"],
    "numerical": ["numpy", "scipy", "jax", "cupy"],
    "plotting": ["matplotlib", "seaborn", "plotly", "bokeh", "altair"],
    "image": ["pillow", "opencv-python", "scikit-image", "imageio"],
    "game": ["pygame", "arcade", "pyglet"],
    "3d": ["trimesh", "open3d", "vtk", "pyrender", "moderngl"],
    "gui": ["tkinter", "pyqt", "pyside", "kivy", "wxpython"],
    "cli": ["typer", "click", "argparse", "rich"],
    "validation": ["pydantic", "attrs", "marshmallow", "cerberus"],
    "orm": ["sqlalchemy", "peewee", "tortoise-orm", "pony"],
    "database": ["sqlite3", "psycopg2", "asyncpg", "pymongo", "redis"],
    "task queue": ["celery", "rq", "dramatiq", "huey"],
    "workflow": ["airflow", "prefect", "dagster", "luigi"],
    "browser": ["selenium", "playwright", "pyppeteer"],
    "scraping": ["scrapy", "beautifulsoup4", "lxml", "requests-html"],
    "parsing": ["lxml", "beautifulsoup4", "html5lib", "xmltodict"],
    "regex": ["regex", "re", "pyparsing"],
    "ml": ["scikit-learn", "xgboost", "lightgbm", "catboost"],
    "dl": ["torch", "tensorflow", "jax", "keras"],
    "nlp": ["transformers", "spacy", "nltk", "gensim"],
    "llm": ["langchain", "llama-index", "openai", "transformers"],
    "bot": ["python-telegram-bot", "aiogram", "discord.py"],
    "security": ["cryptography", "pyjwt", "passlib", "bcrypt"],
    "logging": ["loguru", "structlog", "logging"],
    "config": ["pydantic-settings", "python-dotenv", "dynaconf"],
    "packaging": ["poetry", "hatch", "uv", "setuptools"],
    "video": ["moviepy", "opencv-python", "av", "ffmpeg-python"],
    "audio": ["librosa", "soundfile", "pydub", "pyaudio"],
    "graph": ["networkx", "igraph", "graph-tool"],
    "dashboards": ["dash", "streamlit", "panel", "gradio"],
}


def _pkg_stats(kb, pkg):
    """آمار یک پکیج"""
    try:
        n = kb.conn.execute(
            "SELECT COUNT(*) FROM resources "
            "WHERE LOWER(title) LIKE ? OR LOWER(content) LIKE ?",
            (f"%{pkg.lower()}%", f"%{pkg.lower()}%")
        ).fetchone()[0]
    except Exception:
        n = 0

    try:
        sc = kb.conn.execute(
            "SELECT AVG(score) FROM resources "
            "WHERE LOWER(title) LIKE ? OR LOWER(content) LIKE ?",
            (f"%{pkg.lower()}%", f"%{pkg.lower()}%")
        ).fetchone()[0] or 0
    except Exception:
        sc = 0

    # related count از گراف
    rc = 0
    try:
        g = json.loads((BASE / "graph.json").read_text())
        cooc = g.get("cooc", {})
        for pair in cooc:
            a, b = pair.split("|", 1)
            if a == pkg.lower() or b == pkg.lower():
                rc += 1
    except Exception:
        pass

    return {"resources": n, "score": sc, "related": rc}


def advise(kb, task):
    """بهترین پکیج برای یک کار"""
    t = task.lower().strip()
    if t not in TASKS:
        # جستجوی فازی
        for k in TASKS:
            if t in k or k in t:
                t = k
                break
        else:
            print(f"\n  کار '{task}' شناخته نشد.")
            print(f"  کارهای موجود:")
            keys = sorted(TASKS.keys())
            for i in range(0, len(keys), 3):
                row = keys[i:i + 3]
                print("    " + "  ".join(f"{k:20s}" for k in row))
            return

    print()
    print("=" * 62)
    print(f"  🎓 مشاور — بهترین برای '{t}'")
    print("=" * 62)
    print()

    rows = []
    for pkg in TASKS[t]:
        s = _pkg_stats(kb, pkg)
        rows.append((pkg, s["resources"], s["score"], s["related"]))

    rows.sort(key=lambda x: -(x[1] * 10 + x[3]))

    print(f"  {'پکیج':<20s} {'منابع':>6s} {'امتیاز':>8s} {'روابط':>6s}")
    print("  " + "─" * 46)
    for pkg, n, sc, rc in rows:
        marker = ""
        if rows and rows[0][0] == pkg:
            marker = " ⭐"
        print(f"  {pkg:<20s} {n:>6d} {sc:>8.2f} {rc:>6d}{marker}")

    print()
    print(f"  💡 پیشنهاد: {rows[0][0]}")


def show_tasks():
    print("\n  کارهای موجود:\n")
    keys = sorted(TASKS.keys())
    for i in range(0, len(keys), 3):
        row = keys[i:i + 3]
        print("    " + "  ".join(f"{k:22s}" for k in row))
