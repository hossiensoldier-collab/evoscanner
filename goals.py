"""مسیر هدف‌محور"""
GOALS = {
    "backend": {"fa": "برنامه‌نویس بک‌اند", "levels": [
        ("پایتون پایه", ["python tutorial", "python basics"]),
        ("وب فریمورک", ["fastapi tutorial", "django tutorial", "flask tutorial"]),
        ("داده و ORM", ["sqlalchemy", "postgres python", "pydantic"]),
        ("API و احراز هویت", ["rest api python", "jwt python"]),
        ("تست و کیفیت", ["pytest", "python testing", "mypy"]),
        ("استقرار", ["docker python", "uvicorn", "python ci cd"])],
        "project": "ساخت API با FastAPI + PostgreSQL + JWT + Docker"},
    "ml": {"fa": "مهندس یادگیری ماشین", "levels": [
        ("مبانی ریاضی", ["linear algebra", "probability", "statistics ml"]),
        ("پایتون داده", ["numpy tutorial", "pandas tutorial"]),
        ("یادگیری ماشین", ["scikit-learn", "machine learning python"]),
        ("یادگیری عمیق", ["pytorch tutorial", "tensorflow", "deep learning"]),
        ("NLP و LLM", ["transformers", "huggingface", "langchain"]),
        ("MLOps", ["mlflow", "docker ml", "model deployment"])],
        "project": "مدل طبقه‌بندی + RAG + استقرار Docker"},
    "data": {"fa": "تحلیلگر داده", "levels": [
        ("پایتون داده", ["python for data", "numpy", "pandas"]),
        ("SQL", ["sql tutorial", "postgresql"]),
        ("مصورسازی", ["matplotlib", "seaborn", "plotly"]),
        ("آمار", ["statistics", "eda"]),
        ("Big Data", ["spark python", "duckdb", "polars"])],
        "project": "تحلیل ۱ میلیون ردیف + داشبورد"},
    "devops": {"fa": "مهندس DevOps", "levels": [
        ("لینوکس", ["linux basics", "bash"]),
        ("خودکارسازی", ["python automation", "subprocess"]),
        ("کانتینر", ["docker tutorial", "kubernetes"]),
        ("CI/CD", ["github actions", "gitlab ci"]),
        ("مانیتورینگ", ["prometheus", "grafana"])],
        "project": "پایپ‌لاین CI/CD با K8s"},
    "security": {"fa": "متخصص امنیت", "levels": [
        ("مبانی", ["security basics", "cryptography", "owasp"]),
        ("پایتون امنیت", ["python security", "bandit"]),
        ("تست نفوذ", ["pentest python", "scapy"]),
        ("بدافزار", ["malware analysis", "reverse engineering python"]),
        ("دفاع", ["ids", "siem"])],
        "project": "اسکنر آسیب‌پذیری وب"},
}

def list_goals():
    print("\n🎯 اهداف موجود:\n")
    for k, v in GOALS.items():
        print(f"  {k:12s} → {v['fa']}")
    print("\n  استفاده: python evoscanner_v2.py goal <name>")

def show_goal(kb, goal_key):
    if goal_key not in GOALS:
        print(f"اهداف: {', '.join(GOALS.keys())}"); return
    g = GOALS[goal_key]
    print(f"\n🎯 مسیر: {g['fa']}\n" + "═" * 55)
    total = 0
    for i, (level, queries) in enumerate(g["levels"], 1):
        found = []
        for q in queries:
            found.extend(kb.search(q, 3))
        seen = set(); uniq = []
        for src, title, url, score in found:
            if url not in seen:
                seen.add(url); uniq.append((src, title, url, score))
        print(f"\n📚 سطح {i}: {level}   ({len(uniq)} منبع)")
        if not uniq:
            print("   (خالی — در چرخه بعدی پر می‌شود)")
        for src, title, url, score in uniq[:4]:
            total += 1
            print(f"   • [{src:12s}] {title[:55]}")
            print(f"     {url}")
    print(f"\n🎯 پروژه: {g['project']}")
    print(f"\nجمع: {total} منبع")

def goal_queries(goal_key):
    if goal_key not in GOALS: return []
    out = []
    for _, qs in GOALS[goal_key]["levels"]: out.extend(qs)
    return out

