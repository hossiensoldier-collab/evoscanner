"""Weekly summary report"""
import json
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path.home() / "evoscanner"


def generate(kb):
    """گزارش هفته گذشته"""
    now = datetime.now()
    week_ago = (now - timedelta(days=7)).isoformat()

    print()
    print("=" * 60)
    print(f"  📊 گزارش هفتگی EvoScanner")
    print(f"  {now:%Y-%m-%d}  |  ۷ روز گذشته")
    print("=" * 60)
    print()

    # منابع جدید در هفته
    rows = kb.conn.execute(
        """SELECT source, COUNT(*), AVG(score)
           FROM resources WHERE found_at >= ?
           GROUP BY source ORDER BY COUNT(*) DESC""",
        (week_ago,)).fetchall()

    if rows:
        print("  📥 منابع جدید هفته:")
        total_new = 0
        for src, n, avg in rows:
            bar = "#" * min(n, 30)
            print(f"    {src:15s} {n:4d}  {avg:.2f}  {bar}")
            total_new += n
        print(f"    {'':15s} {'-'*4}")
        print(f"    {'جمع':15s} {total_new:4d}")
    else:
        print("  ⚠ منابع جدید در هفته نیست")

    print()

    # دسته‌های جدید
    print("  🏷  توزیع دسته‌ها:")
    for cat, n, avg in kb.conn.execute(
        """SELECT category, COUNT(*), AVG(score)
           FROM resources GROUP BY category
           ORDER BY COUNT(*) DESC LIMIT 12""").fetchall():
        bar = "#" * min(n // 3, 30)
        print(f"    {cat:15s} {n:4d}  {bar}")

    print()

    # دانش
    stats = {}
    for t in ("techniques", "concepts", "snippets", "graphics_topics"):
        try:
            stats[t] = kb.conn.execute(
                f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        except Exception:
            stats[t] = 0

    print("  🧠 دانش انبارشده:")
    for k, v in stats.items():
        print(f"    {k:20s} {v:5d}")

    print()

    # گراف
    try:
        g = json.loads((BASE / "graph.json").read_text())
        ents = sum(1 for v in g["nodes"].values()
                   if v.get("type") == "entity")
        print(f"  🕸  گراف: {ents} موجودیت، "
              f"{len(g['edges'])} یال، "
              f"{len(g.get('cooc', {}))} cooc")
        # پکیج داغ هفته
        degree = {}
        for key, w in g["edges"].items():
            a, b = key.split("\u2192", 1)
            degree[a] = degree.get(a, 0) + w
        top = sorted(degree.items(), key=lambda x: -x[1])[:5]
        print(f"\n  🔥 داغ‌های گراف:")
        for n, d in top:
            print(f"    {n:25s} {d}")
    except Exception:
        pass

    print()

    # پیشنهاد
    print("  💡 پیشنهاد هفته آینده:")
    # دسته ضعیف
    weak = kb.conn.execute(
        """SELECT category, COUNT(*) FROM resources
           GROUP BY category HAVING COUNT(*) < 5
           ORDER BY COUNT(*) ASC LIMIT 3""").fetchall()
    if weak:
        for c, n in weak:
            print(f"    • تقویت دسته {c} ({n} منبع)")
    else:
        print("    • دسته‌ها متعادل — موضوعات تازه اضافه کن")

    print(f"\n  {'─' * 55}")
    print(f"  📅 پایان گزارش · {now:%H:%M:%S}")
    print()
