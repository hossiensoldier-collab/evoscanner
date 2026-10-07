"""Suggest project ideas based on what's in the knowledge base"""
import random
from pathlib import Path


# قالب‌های پروژه — هر قالب از منابع موجود تغذیه می‌شود
TEMPLATES = {
    "web_api": {
        "title": "REST API با {framework}",
        "need": ["fastapi", "flask", "django", "starlette"],
        "extra": ["sqlalchemy", "pydantic", "uvicorn", "jwt"],
        "size": "متوسط",
        "days": "۵–۷",
    },
    "web_ui": {
        "title": "داشبورد وب با {lib}",
        "need": ["dash", "streamlit", "gradio", "panel"],
        "extra": ["plotly", "pandas", "matplotlib"],
        "size": "متوسط",
        "days": "۳–۵",
    },
    "scraper": {
        "title": "خزنده وب با {lib}",
        "need": ["scrapy", "beautifulsoup", "selenium", "playwright"],
        "extra": ["requests", "lxml", "pandas"],
        "size": "کوچک",
        "days": "۲–۳",
    },
    "telegram_bot": {
        "title": "ربات تلگرام با {lib}",
        "need": ["aiogram", "python-telegram-bot", "telebot"],
        "extra": ["asyncio", "sqlite", "httpx"],
        "size": "کوچک",
        "days": "۲–۴",
    },
    "ml_classifier": {
        "title": "طبقه‌بندی با {lib}",
        "need": ["scikit-learn", "pandas", "numpy", "xgboost"],
        "extra": ["matplotlib", "seaborn", "joblib"],
        "size": "متوسط",
        "days": "۵–۷",
    },
    "ml_llm": {
        "title": "چت‌بات LLM با {lib}",
        "need": ["transformers", "langchain", "huggingface", "openai"],
        "extra": ["fastapi", "gradio", "pydantic"],
        "size": "متوسط",
        "days": "۷–۱۰",
    },
    "async_service": {
        "title": "سرویس async با {lib}",
        "need": ["aiohttp", "asyncio", "httpx", "uvicorn"],
        "extra": ["sqlalchemy", "pydantic", "redis"],
        "size": "متوسط",
        "days": "۵–۷",
    },
    "game_2d": {
        "title": "بازی ۲بعدی با {lib}",
        "need": ["pygame", "arcade", "pyglet"],
        "extra": ["pymunk", "numpy"],
        "size": "متوسط",
        "days": "۷–۱۰",
    },
    "graphics_visual": {
        "title": "مصورسازی داده با {lib}",
        "need": ["matplotlib", "plotly", "seaborn", "bokeh"],
        "extra": ["pandas", "numpy", "jupyter"],
        "size": "کوچک",
        "days": "۲–۴",
    },
    "opencv_app": {
        "title": "پردازش تصویر با {lib}",
        "need": ["opencv", "pillow", "scikit-image", "imageio"],
        "extra": ["numpy", "matplotlib"],
        "size": "متوسط",
        "days": "۵–۷",
    },
    "cli_tool": {
        "title": "ابزار CLI با {lib}",
        "need": ["typer", "click", "argparse", "rich"],
        "extra": ["colorama", "tqdm"],
        "size": "کوچک",
        "days": "۲–۳",
    },
    "data_pipeline": {
        "title": "پایپ‌لاین داده با {lib}",
        "need": ["pandas", "polars", "duckdb", "dask"],
        "extra": ["pyarrow", "sqlalchemy", "prefect"],
        "size": "متوسط",
        "days": "۵–۷",
    },
    "automation": {
        "title": "اتوماسیون با {lib}",
        "need": ["selenium", "playwright", "pyautogui", "schedule"],
        "extra": ["requests", "pandas"],
        "size": "کوچک",
        "days": "۲–۴",
    },
}


def _resource_count(kb, name):
    """چند منبع برای این پکیج داریم؟"""
    try:
        n = kb.conn.execute(
            "SELECT COUNT(*) FROM resources "
            "WHERE LOWER(title) LIKE ? OR LOWER(content) LIKE ?",
            (f"%{name.lower()}%", f"%{name.lower()}%")
        ).fetchone()[0]
        return n
    except Exception:
        return 0


def suggest(kb, n=5, size_filter=None):
    """پیشنهاد n پروژه بر اساس منابع موجود"""
    scored = []
    for key, tmpl in TEMPLATES.items():
        if size_filter and tmpl["size"] != size_filter:
            continue

        # امتیاز بر اساس منابع موجود
        have = []
        missing = []
        for pkg in tmpl["need"]:
            c = _resource_count(kb, pkg)
            if c >= 2:
                have.append((pkg, c))
            else:
                missing.append(pkg)

        score = len(have) * 10 - len(missing) * 2
        if not have:
            continue

        # انتخاب یک از "have" به عنوان framework
        framework = have[0][0] if have else tmpl["need"][0]

        scored.append({
            "key": key,
            "title": tmpl["title"].format(
                lib=framework, framework=framework),
            "size": tmpl["size"],
            "days": tmpl["days"],
            "have": have,
            "missing": missing,
            "extra": tmpl["extra"],
            "score": score,
        })

    scored.sort(key=lambda x: -x["score"])
    return scored[:n]


def show(kb, n=5, size_filter=None):
    print()
    print("=" * 62)
    print("  🎯 پیشنهاد پروژه — بر اساس منابع موجود")
    print("=" * 62)
    print()

    ideas = suggest(kb, n=n, size_filter=size_filter)
    if not ideas:
        print("  ⚠ منابع کافی نیست. اول 'run' بزن.")
        return

    for i, idea in enumerate(ideas, 1):
        print(f"  [{i}] {idea['title']}")
        print(f"      {idea['size']}  |  {idea['days']} روز")
        have_s = ", ".join(f"{n}({c})" for n, c in idea["have"][:5])
        print(f"      دارید: {have_s}")
        if idea["missing"]:
            print(f"      کم: {', '.join(idea['missing'][:3])}")
        print(f"      اضافه: {', '.join(idea['extra'][:3])}")
        print()
