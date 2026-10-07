"""Learn Skill — یادگیری یک قابلیت از منابع"""
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BASE = Path.home() / "evoscanner"
SKILLS_DIR = BASE / "skills"
SKILLS_DIR.mkdir(exist_ok=True)

# قابلیت‌های پروژه — با منابع مرتبط
SKILLS = {
    "rag": {
        "name": "RAG (Retrieval-Augmented Generation)",
        "desc": "پاسخ به سؤال از منابع",
        "keywords": ["rag", "retrieval", "bm25", "vector search", "embedding"],
        "files": ["feature_rag_v2.py"],
    },
    "graph": {
        "name": "Knowledge Graph",
        "desc": "گراف دانش با co-occurrence",
        "keywords": ["knowledge graph", "graph database", "networkx", "neo4j"],
        "files": ["graph.py"],
    },
    "extract": {
        "name": "Knowledge Extraction",
        "desc": "استخراج تکنیک و کد",
        "keywords": ["nlp extraction", "regex", "information extraction"],
        "files": ["extractor.py"],
    },
    "classify": {
        "name": "Auto Classification",
        "desc": "دسته‌بندی خودکار منابع",
        "keywords": ["classification", "text classification", "tf-idf"],
        "files": ["classifier.py"],
    },
    "agents": {
        "name": "Multi-Agent System",
        "desc": "چهار ایجنت خودمختار",
        "keywords": ["multi agent", "agent framework", "autonomous agents"],
        "files": ["agents.py", "feature_agent_chain.py"],
    },
    "meta": {
        "name": "Meta-Learning",
        "desc": "یادگیری درباره یادگیری",
        "keywords": ["meta learning", "auto ml", "neural architecture search"],
        "files": ["feature_meta.py"],
    },
    "llm": {
        "name": "LLM Integration",
        "desc": "اتصال به مدل زبانی",
        "keywords": ["llm", "openai api", "prompt engineering", "langchain"],
        "files": ["ai_agent.py"],
    },
    "scraper": {
        "name": "Web Scraping",
        "desc": "جمع‌آوری از اینترنت",
        "keywords": ["scraping", "crawler", "beautifulsoup", "selenium"],
        "files": ["sources.py"],
    },
    "web": {
        "name": "Web Server",
        "desc": "سرور HTTP + API",
        "keywords": ["http server", "rest api", "fastapi", "flask"],
        "files": ["api.py", "webui.py"],
    },
    "async": {
        "name": "Async Programming",
        "desc": "همزمانی و موازی",
        "keywords": ["asyncio", "async await", "concurrency"],
        "files": [],
    },
    "graphics": {
        "name": "Terminal Graphics",
        "desc": "رنگ و ASCII",
        "keywords": ["ansi color", "terminal graphics", "ascii art"],
        "files": ["graph_web.py", "cycle_ui.py"],
    },
    "self": {
        "name": "Self-Modification",
        "desc": "خودبازنویسی",
        "keywords": ["self modifying", "godel agent", "code rewriting"],
        "files": ["selfmod.py", "selfupgrade.py"],
    },
}


def find_resources(kb, keywords, limit=20):
    """جستجو در منابع برای یک قابلیت"""
    results = []
    seen_urls = set()

    for kw in keywords:
        rows = kb.conn.execute(
            """SELECT title, url, source, content, score
               FROM resources
               WHERE LOWER(title) LIKE ? OR LOWER(content) LIKE ?
               ORDER BY score DESC LIMIT ?""",
            (f"%{kw.lower()}%", f"%{kw.lower()}%", limit)
        ).fetchall()

        for title, url, source, content, score in rows:
            if url in seen_urls:
                continue
            seen_urls.add(url)
            results.append({
                "title": title,
                "url": url,
                "source": source,
                "content": (content or "")[:1000],
                "score": score,
                "matched": kw,
            })

    results.sort(key=lambda x: -x["score"])
    return results[:limit]


def find_techniques(kb, keywords):
    """تکنیک‌های استخراج‌شده مرتبط"""
    results = []
    for kw in keywords:
        try:
            rows = kb.conn.execute(
                """SELECT name, source_url, difficulty
                   FROM techniques
                   WHERE LOWER(name) LIKE ?
                   LIMIT 10""",
                (f"%{kw.lower()}%",)
            ).fetchall()
            results.extend(rows)
        except Exception:
            pass
    return list(set(results))[:15]


def find_snippets(kb, keywords, limit=10):
    """قطعات کد مرتبط"""
    results = []
    seen = set()
    for kw in keywords:
        try:
            rows = kb.conn.execute(
                """SELECT purpose, code, source_url
                   FROM snippets
                   WHERE LOWER(purpose) LIKE ? OR LOWER(code) LIKE ?
                   LIMIT ?""",
                (f"%{kw.lower()}%", f"%{kw.lower()}%", limit)
            ).fetchall()
            for purpose, code, url in rows:
                if code in seen:
                    continue
                seen.add(code)
                results.append((purpose, code, url))
        except Exception:
            pass
    return results[:limit]


def build_skill_guide(skill_key, kb):
    """ساخت راهنمای یادگیری یک قابلیت"""
    skill = SKILLS.get(skill_key)
    if not skill:
        return None

    print()
    print(f"  {'=' * 60}")
    print(f"  🎓 یادگیری قابلیت: {skill['name']}")
    print(f"  {'=' * 60}")
    print()
    print(f"  {skill['desc']}")
    print()

    # ۱. منابع
    print(f"  [1] منابع مرتبط")
    resources = find_resources(kb, skill["keywords"])
    if resources:
        for r in resources[:8]:
            print(f"    • [{r['source']:12s}] {r['title'][:55]}")
            print(f"      {r['url']}")
    else:
        print(f"    (چیزی پیدا نشد — اول run بزن)")

    # ۲. تکنیک‌ها
    print()
    print(f"  [2] تکنیک‌های مرتبط")
    techs = find_techniques(kb, skill["keywords"])
    if techs:
        for name, url, diff in techs[:8]:
            print(f"    • {name[:50]}")
    else:
        print(f"    (خالی — اول extract بزن)")

    # ۳. قطعات کد
    print()
    print(f"  [3] قطعات کد")
    snippets = find_snippets(kb, skill["keywords"], limit=5)
    if snippets:
        for purpose, code, url in snippets[:3]:
            print(f"    ─── {purpose[:50]}")
            for line in code.split("\n")[:6]:
                print(f"      {line}")
            print()
    else:
        print(f"    (خالی)")

    # ۴. فایل‌های پروژه
    print()
    print(f"  [4] فایل‌های پروژه")
    for f in skill["files"]:
        path = BASE / f
        if path.exists():
            lines = path.read_text().count("\n")
            print(f"    ✓ {f}  ({lines} خط)")
        else:
            print(f"    ✗ {f}  (نیست)")

    # ۵. ذخیره راهنما
    guide = {
        "skill": skill["name"],
        "desc": skill["desc"],
        "keywords": skill["keywords"],
        "resources": resources,
        "techniques": [{"name": n, "url": u} for n, u, d in techs],
        "snippets": [{"purpose": p, "code": c[:500]} for p, c, u in snippets],
        "project_files": skill["files"],
        "generated": datetime.now().isoformat(),
    }

    out = SKILLS_DIR / f"{skill_key}.json"
    out.write_text(json.dumps(guide, indent=2, ensure_ascii=False))
    print()
    print(f"  ✓ راهنما ذخیره شد: {out.name}")
    print()


def build_prompt(skill_key, kb):
    """ساخت پرامپت برای AI"""
    skill = SKILLS.get(skill_key)
    if not skill:
        return None

    resources = find_resources(kb, skill["keywords"], limit=15)
    techs = find_techniques(kb, skill["keywords"])
    snippets = find_snippets(kb, skill["keywords"], limit=8)

    resources_txt = "\n".join(
        f"  - [{r['source']}] {r['title']} — {r['url']}"
        for r in resources[:10])

    techs_txt = "\n".join(f"  - {n}" for n, _, _ in techs[:10])

    snippets_txt = ""
    for p, c, u in snippets[:3]:
        snippets_txt += f"\n### {p}\n```\n{c[:400]}\n```\n"

    prompt = f"""پروژه EvoScanner — یادگیری و پیاده‌سازی قابلیت: {skill['name']}

## قابلیت مورد نظر

**نام:** {skill['name']}
**توضیح:** {skill['desc']}

## منابع مرتبط (از پایگاه خودم)

{resources_txt}

## تکنیک‌های استخراج‌شده

{techs_txt}

## قطعات کد موجود

{snippets_txt}

## فایل‌های پروژه که این قابلیت را دارند

{chr(10).join('  - ' + f for f in skill['files'])}

## درخواست من

لطفاً:

۱. **تحلیل عمیق** — این قابلیت چطور کار می‌کند، چه الگوریتمی دارد
۲. **بهترین منابع** — از لیست بالا، کدام‌ها را بخوانم و به چه ترتیب
۳. **پیاده‌سازی از صفر** — اگر بخواهم این قابلیت را از ابتدا بسازم
۴. **پیشنهادهای بهبود** — پروژه فعلی چه چیزی کم دارد
۵. **کد نمونه** — مثال ساده برای درک بهتر

محیط: Termux اندروید، فقط stdlib پایتون

هدف: من می‌خواهم این قابلیت را کامل یاد بگیرم و بهتر پیاده کنم.
"""

    out = SKILLS_DIR / f"{skill_key}_prompt.md"
    out.write_text(prompt, encoding="utf-8")
    return out, prompt


def list_skills():
    print()
    print(f"  {'=' * 60}")
    print(f"  📚 قابلیت‌های پروژه")
    print(f"  {'=' * 60}")
    print()
    for key, skill in SKILLS.items():
        print(f"  {key:12s}  {skill['name']}")
        print(f"                {skill['desc']}")
    print()


def choose_skill():
    print()
    print(f"  {'=' * 60}")
    print(f"  🎓 انتخاب قابلیت برای یادگیری")
    print(f"  {'=' * 60}")
    print()
    keys = list(SKILLS.keys())
    for i, key in enumerate(keys, 1):
        skill = SKILLS[key]
        print(f"  [{i:2d}]  {skill['name']:35s}")
        print(f"        {skill['desc']}")
    print()

    try:
        c = input(f"  انتخاب (1-{len(keys)}): ").strip()
        idx = int(c) - 1
        if 0 <= idx < len(keys):
            return keys[idx]
    except (ValueError, EOFError, KeyboardInterrupt):
        pass
    return None


def run():
    import sys
    sys.path.insert(0, str(BASE))
    from evoscanner_v2 import KB
    kb = KB()

    os.system("clear")

    key = choose_skill()
    if not key:
        return

    # ساخت راهنما
    build_skill_guide(key, kb)

    # ساخت پرامپت
    result = build_prompt(key, kb)
    if result:
        out, prompt = result
        print(f"  ✓ پرامپت ساخته شد: {out.name}")
        print()

        # کپی به clipboard
        try:
            r = subprocess.run(["termux-clipboard-set"],
                               input=prompt.encode(), timeout=5)
            if r.returncode == 0:
                print(f"  ✓ در clipboard کپی شد")
                print(f"    الان به AI دیگر paste کن")
        except Exception:
            pass

        print()
        print(f"  {'─' * 60}")
        print(f"  فایل‌ها:")
        print(f"    راهنما: {SKILLS_DIR}/{key}.json")
        print(f"    پرامپت: {out}")
        print(f"  {'─' * 60}")
        print()

        c = input("  پرامپت را نشان دهم؟ (b/n): ").strip().lower()
        if c == "b":
            print()
            print("=" * 60)
            print(prompt)
            print("=" * 60)


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print()

