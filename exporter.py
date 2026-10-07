"""خروجی گرفتن از پایگاه دانش در فرمت‌های مختلف"""
import csv
import json
from datetime import datetime
from pathlib import Path

BASE = Path.home() / "evoscanner"
OUT = BASE / "exports"
OUT.mkdir(exist_ok=True)


def _ts():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def to_json(kb, cat=None):
    """خروجی JSON کامل"""
    if cat:
        rows = kb.by_category(cat, 10000)
        data = [{"source": s, "title": t, "url": u, "score": sc}
                for s, t, u, sc in rows]
        path = OUT / f"{cat}_{_ts()}.json"
    else:
        rows = kb.conn.execute(
            """SELECT hash, url, title, content, source, score, tags,
                      found_at, category FROM resources"""
        ).fetchall()
        data = [dict(zip(
            ["hash","url","title","content","source","score","tags",
             "found_at","category"], r)) for r in rows]
        path = OUT / f"all_{_ts()}.json"

    path.write_text(json.dumps(data, indent=2, ensure_ascii=False),
                    encoding="utf-8")
    print(f"  ✓ {path}  ({len(data)} مورد)")
    return path


def to_csv(kb):
    """خروجی CSV مرتب‌شده بر اساس دسته و امتیاز"""
    path = OUT / f"all_{_ts()}.csv"
    rows = kb.conn.execute(
        """SELECT category, source, score, title, url, tags
           FROM resources
           ORDER BY category, score DESC"""
    ).fetchall()
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["category", "source", "score", "title", "url", "tags"])
        w.writerows(rows)
    print(f"  ✓ {path}  ({len(rows)} مورد)")
    return path


def to_markdown(kb, top=30):
    """گزارش Markdown زیبا با گروه‌بندی"""
    path = OUT / f"report_{_ts()}.md"
    lines = [
        "# EvoScanner Report",
        f"\n**تاریخ:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**کل منابع:** {kb.total()}\n",
        "## فهرست\n",
    ]

    # فهرست دسته‌ها
    cats = kb.categories_stats()
    for i, (cat, n, avg) in enumerate(cats, 1):
        lines.append(f"{i}. [{cat}](#{cat}) — {n} منبع (⌀ {avg:.2f})")
    lines.append("")

    # بخش هر دسته
    for cat, n, avg in cats:
        lines.append(f"\n## {cat}\n")
        lines.append(f"*{n} منبع، میانگین امتیاز {avg:.2f}*\n")
        rows = kb.by_category(cat, top)
        for i, (src, title, url, score) in enumerate(rows, 1):
            lines.append(f"{i}. **[{title}]({url})**  ")
            lines.append(f"   `{src}` ⭐ {score:.2f}\n")

    # آمار منابع
    lines.append("\n## آمار منابع\n")
    lines.append("| منبع | تعداد | میانگین امتیاز |")
    lines.append("|---|---|---|")
    for src, n, avg in kb.stats():
        lines.append(f"| {src} | {n} | {avg:.2f} |")

    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  ✓ {path}")
    return path


def export_all(kb):
    """همه فرمت‌ها یکجا"""
    print("📦 خروجی کامل:\n")
    to_json(kb)
    to_csv(kb)
    to_markdown(kb)
    # یک فایل برای هر دسته ضعیف
    cats = kb.categories_stats()
    for cat, n, _ in cats:
        if n < 100:
            to_json(kb, cat)
    print(f"\n  همه فایل‌ها در: {OUT}")

