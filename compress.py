"""فشرده‌سازی گراف + آرشیو منابع کهنه"""
from datetime import datetime, timedelta
from pathlib import Path


def merge_similar_entities(g, min_cooc=2):
    """ادغام موجودیت‌های مشابه با DSU"""
    nodes = g.data["nodes"]
    edges = g.data["edges"]
    cooc = g.data.get("cooc", {})

    # پیدا کردن جفت‌های ادغام‌پذیر
    pairs = []
    for k, w in cooc.items():
        if w < min_cooc:
            continue
        a, b = k.split("|", 1)
        if a.startswith("cat:") or b.startswith("cat:"):
            continue
        na, nb = nodes.get(a, {}), nodes.get(b, {})
        if na.get("type") != "entity" or nb.get("type") != "entity":
            continue
        cats_a = set(na.get("cats", {}).keys())
        cats_b = set(nb.get("cats", {}).keys())
        # فقط اگر در یک دسته هستند
        if cats_a & cats_b:
            # فقط اگر از نظر متنی مشابه‌اند
            # قاعده: یکی زیررشته دیگری، یا طول مشابه
            if a in b or b in a or abs(len(a) - len(b)) <= 2:
                pairs.append((a, b, w))

    # DSU
    parent = {}
    def find(x):
        r = x
        while parent.get(r, r) != r:
            r = parent[r]
        while parent.get(x, x) != x:
            parent[x], x = r, parent[x]
        return r
    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for a, b, _ in pairs:
        union(a, b)

    # گروه‌بندی
    groups = {}
    for n in list(nodes.keys()):
        if nodes[n].get("type") != "entity" or n.startswith("cat:"):
            continue
        groups.setdefault(find(n), []).append(n)

    # ادغام
    merged = 0
    for root, members in groups.items():
        if len(members) < 2:
            continue
        # نماینده: بیشترین count
        members.sort(key=lambda x: -nodes[x].get("count", 0))
        rep = members[0]
        for m in members[1:]:
            # انتقال یال‌های خروجی
            for key in list(edges.keys()):
                if key.startswith(m + "\u2192"):
                    nk = key.replace(m + "\u2192", rep + "\u2192", 1)
                    edges[nk] = edges.get(nk, 0) + edges[key]
                    del edges[key]
                elif key.endswith("\u2192" + m):
                    nk = key.replace("\u2192" + m, "\u2192" + rep, 1)
                    edges[nk] = edges.get(nk, 0) + edges[key]
                    del edges[key]
            # انتقال count
            nodes[rep]["count"] = nodes[rep].get("count", 0) + nodes[m].get("count", 0)
            # انتقال cats
            for c, v in nodes[m].get("cats", {}).items():
                nodes[rep].setdefault("cats", {})[c] = nodes[rep].get("cats", {}).get(c, 0) + v
            del nodes[m]
            merged += 1

    g.save()
    return merged


def archive_old(kb, min_age_days=60, max_score=0.4):
    """آرشیو منابع کهنه و کم‌ارزش"""
    kb.conn.execute("""
        CREATE TABLE IF NOT EXISTS archived (
            hash TEXT PRIMARY KEY, url TEXT, title TEXT, content TEXT,
            source TEXT, score REAL, tags TEXT, found_at TEXT, category TEXT
        )
    """)
    # آرشیو منابع کم‌ارزش (بدون در نظر گرفتن سن)
    rows = kb.conn.execute("""
        SELECT hash FROM resources
        WHERE score < ? AND source NOT IN ('github', 'arxiv', 'stackoverflow')
        AND length(COALESCE(content,'')) < 1500
    """, (max_score,)).fetchall()

    n = 0
    for (h,) in rows:
        kb.conn.execute("""
            INSERT OR IGNORE INTO archived
            SELECT hash, url, title, content, source, score, tags, found_at, category
            FROM resources WHERE hash = ?
        """, (h,))
        kb.conn.execute("DELETE FROM resources WHERE hash = ?", (h,))
        n += 1
    kb.conn.commit()
    return n


def report(g, kb):
    """گزارش فشرده‌سازی"""
    nodes = g.data["nodes"]
    ents = sum(1 for v in nodes.values() if v.get("type") == "entity")
    res = sum(1 for v in nodes.values() if v.get("type") == "resource")
    archived = kb.conn.execute(
        "SELECT COUNT(*) FROM archived"
    ).fetchone()[0] if _has_table(kb, "archived") else 0

    print(f"\n📦 وضعیت فشرده‌سازی:")
    print(f"  گراف: {ents} موجودیت، {res} منبع، {len(g.data['edges'])} یال")
    print(f"  آرشیو: {archived} منبع")
    print(f"  پایگاه فعال: {kb.total()} منبع")


def _has_table(kb, name):
    r = kb.conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (name,)
    ).fetchone()
    return bool(r)

