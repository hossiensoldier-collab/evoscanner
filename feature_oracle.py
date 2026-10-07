"""Ecosystem Oracle — PageRank، Topological Sort، Community، Anomaly"""
import json
import math
import sys
from collections import defaultdict, Counter, deque
from pathlib import Path

BASE = Path.home() / "evoscanner"
DEPS = BASE / "deps_graph.json"

CY = "\033[38;2;100;220;230m"
WH = "\033[38;2;230;230;240m"
GY = "\033[38;2;130;135;150m"
GR = "\033[38;2;120;230;150m"
YL = "\033[38;2;255;215;80m"
PU = "\033[38;2;180;140;255m"
PK = "\033[38;2;255;140;200m"
RD = "\033[38;2;255;110;110m"
BL = "\033[38;2;120;170;255m"
OR = "\033[38;2;255;160;80m"
R = "\033[0m"
B = "\033[1m"
D = "\033[2m"


# ═══════════════════════════════════════════════════
#  بارگذاری گراف
# ═══════════════════════════════════════════════════

def load_graph():
    if not DEPS.exists():
        return None
    try:
        return json.loads(DEPS.read_text())
    except Exception:
        return None


def build_adj(g):
    """گراف جهت‌دار: پکیج → چه چیزهایی نیاز دارد"""
    adj = defaultdict(set)      # A → {B, C}  (A needs B, C)
    rev = defaultdict(set)      # B → {A, X}  (who needs B)
    nodes = set()

    for key, e in g.get("edges", {}).items():
        a, b = e["a"], e["b"]
        adj[a].add(b)
        rev[b].add(a)
        nodes.add(a)
        nodes.add(b)

    return adj, rev, nodes


# ═══════════════════════════════════════════════════
#  1. PageRank — iterative power method
# ═══════════════════════════════════════════════════

def pagerank(adj, rev, nodes, damping=0.85, iters=50, tol=1e-6):
    """
    PageRank در گراف جهت‌دار.
    یالی A→B یعنی A به B وابسته است.
    PageRank می‌گوید چه پکیجی «مهم‌ترین» است (بیشترین وابستگی ورودی).
    """
    N = len(nodes)
    if N == 0:
        return {}

    pr = {n: 1.0 / N for n in nodes}

    for _ in range(iters):
        new_pr = {}
        total_dangling = 0.0

        # جمع سهم dangling nodes
        for n in nodes:
            if not adj[n]:
                total_dangling += pr[n]

        for n in nodes:
            rank = (1.0 - damping) / N
            rank += damping * total_dangling / N

            # از ورودی‌ها
            for src in rev[n]:
                out_deg = len(adj[src])
                if out_deg > 0:
                    rank += damping * pr[src] / out_deg

            new_pr[n] = rank

        # چک همگرایی
        diff = sum(abs(new_pr[n] - pr[n]) for n in nodes)
        pr = new_pr
        if diff < tol:
            break

    return pr


# ═══════════════════════════════════════════════════
#  2. Topological Sort — Kahn's algorithm
# ═══════════════════════════════════════════════════

def topo_sort(adj, nodes):
    """
    ترتیب نصب: چیزهایی که وابستگی ندارند اول.
    yal A→B یعنی A به B نیاز دارد → B قبل از A نصب شود.
    """
    in_deg = {n: 0 for n in nodes}
    for n in nodes:
        for dep in adj[n]:
            in_deg[dep] += 1

    # صف نودهای بدون وابستگی
    queue = deque([n for n in nodes if in_deg[n] == 0])
    order = []

    while queue:
        n = queue.popleft()
        order.append(n)
        for dep in adj[n]:
            in_deg[dep] -= 1
            if in_deg[dep] == 0:
                queue.append(dep)

    # برگشت ترتیب تا نصب درست شود
    # در واقع: کسی که وابستگی ندارد اول نصب می‌شود
    # adj[n] = وابستگی‌های n
    # پس dep قبل از n باید نصب شود
    # در الگوریتم بالا dep بعد از n ظاهر می‌شود
    # پس reverse می‌کنیم
    return order[::-1]


def install_order(adj, nodes, targets):
    """ترتیب نصب برای مجموعه‌ای از پکیج‌ها"""
    # پیدا کردن زیرگراف مورد نیاز
    needed = set()
    q = list(targets)
    while q:
        n = q.pop()
        if n in needed:
            continue
        needed.add(n)
        for dep in adj[n]:
            if dep not in needed:
                q.append(dep)

    # topological sort روی زیرگراف
    return topo_sort(adj, needed), needed


# ═══════════════════════════════════════════════════
#  3. Community Detection — Label Propagation
# ═══════════════════════════════════════════════════

def communities(adj, rev, nodes, iters=20):
    """
    Label Propagation — هر نود لیبل همسایه‌ی غالب را می‌گیرد.
    یال‌ها دوطرفه می‌شوند برای کشف جوامع.
    """
    # گراف بدون جهت
    undirected = defaultdict(set)
    for n in nodes:
        for m in adj[n]:
            undirected[n].add(m)
            undirected[m].add(n)

    # هر نود لیبل خودش
    labels = {n: n for n in nodes}

    import random
    random.seed(42)

    for _ in range(iters):
        order = list(nodes)
        random.shuffle(order)
        changed = 0

        for n in order:
            neighbors = undirected[n]
            if not neighbors:
                continue

            counts = Counter(labels[m] for m in neighbors)
            if not counts:
                continue

            # اگر بهترین لیبل فعلی نیست، تغییر
            new_label = counts.most_common(1)[0][0]
            if labels[n] != new_label:
                labels[n] = new_label
                changed += 1

        if changed == 0:
            break

    # گروه‌بندی
    groups = defaultdict(list)
    for n, label in labels.items():
        groups[label].append(n)

    # فقط گروه‌های با حداقل ۲ عضو
    return {k: v for k, v in groups.items() if len(v) >= 2}


# ═══════════════════════════════════════════════════
#  4. Anomaly Detection — Z-score
# ═══════════════════════════════════════════════════

def anomalies(adj, rev, nodes, threshold=2.0):
    """
    پیدا کردن پکیج‌های غیرمعمول.
    معیارها: تعداد وابستگی، نسبت in/out، همسایه‌های منحصربفرد.
    """
    stats = []
    for n in nodes:
        in_d = len(rev[n])
        out_d = len(adj[n])

        # نسبت وابستگی
        ratio = in_d / max(out_d, 1)

        stats.append({
            "name": n,
            "in": in_d,
            "out": out_d,
            "ratio": ratio,
            "total": in_d + out_d,
        })

    if len(stats) < 5:
        return []

    # میانگین و انحراف معیار برای ratio
    ratios = [s["ratio"] for s in stats]
    mean = sum(ratios) / len(ratios)
    var = sum((r - mean) ** 2 for r in ratios) / len(ratios)
    std = math.sqrt(var) if var > 0 else 1

    # z-score
    for s in stats:
        s["z"] = (s["ratio"] - mean) / std if std > 0 else 0

    # پکیج‌هایی که ratio آن‌ها از حد بیرون است
    anom = [s for s in stats if abs(s["z"]) > threshold]
    anom.sort(key=lambda x: -abs(x["z"]))

    return anom[:15]


# ═══════════════════════════════════════════════════
#  5. Shortest Path — BFS دوطرفه
# ═══════════════════════════════════════════════════

def shortest_path(adj, rev, start, end, max_depth=4):
    """BFS دوطرفه"""
    if start == end: return [start]
    if end in adj[start]: return [start, end]
    if start in adj[end]: return [start, end]
    q = deque([(start, [start])])
    seen = {start}
    while q:
        n, path = q.popleft()
        if len(path) > max_depth: continue
        neighbors = list(adj[n])
        neighbors.sort(key=lambda x: -len(rev[x]))
        for m in neighbors:
            if m == end: return path + [m]
            if m not in seen:
                seen.add(m); q.append((m, path + [m]))
    undirected = defaultdict(set)
    for n in set(adj.keys()):
        for dep in adj[n]:
            undirected[n].add(dep)
            undirected[dep].add(n)
    q = deque([(start, [start])]); seen = {start}
    while q:
        n, path = q.popleft()
        if len(path) > max_depth: continue
        for m in undirected[n]:
            if m == end: return path + [m]
            if m not in seen:
                seen.add(m); q.append((m, path + [m]))
    return None



# ═══════════════════════════════════════════════════
#  نمایش
# ═══════════════════════════════════════════════════

def cmd_rank(limit=20):
    g = load_graph()
    if not g:
        print(f"  {RD}✗ گراف نیست. اول: python feature_deps.py build --limit=100{R}")
        return

    adj, rev, nodes = build_adj(g)
    pr = pagerank(adj, rev, nodes)

    print()
    print(f"  {PU}{B}◆ PageRank — مهم‌ترین پکیج‌ها{R}")
    print(f"  {D}الگوریتم: iterative power method (damping=0.85){R}")
    print()

    top = sorted(pr.items(), key=lambda x: -x[1])[:limit]
    max_pr = top[0][1] if top else 1

    for i, (name, score) in enumerate(top, 1):
        bar_len = int((score / max_pr) * 30)
        col = GR if i <= 3 else (YL if i <= 10 else CY)
        print(f"  {col}{i:2d}.{R} {WH}{name:25s}{R} "
              f"{col}{score:.5f}{R}  {D}{'█' * bar_len}{R}")


def cmd_order(pkgs):
    g = load_graph()
    if not g:
        print(f"  {RD}✗ گراف نیست{R}")
        return

    adj, rev, nodes = build_adj(g)

    targets = [p.lower() for p in pkgs]
    missing = [t for t in targets if t not in nodes]
    if missing:
        print(f"  {YL}پیدا نشد: {', '.join(missing)}{R}")
        targets = [t for t in targets if t in nodes]

    if not targets:
        return

    order, needed = install_order(adj, nodes, targets)

    print()
    print(f"  {PU}{B}◆ Topological Install Order{R}")
    print(f"  {D}پکیج‌های هدف: {', '.join(targets)}{R}")
    print(f"  {D}کل پکیج‌های مورد نیاز: {len(needed)}{R}")
    print()

    for i, name in enumerate(order, 1):
        is_target = name in targets
        col = GR if is_target else CY
        mark = "★" if is_target else " "
        print(f"  {col}{mark}{R} {i:2d}. {WH}{name}{R}")


def cmd_community(min_size=3):
    g = load_graph()
    if not g:
        print(f"  {RD}✗ گراف نیست{R}")
        return

    adj, rev, nodes = build_adj(g)
    groups = communities(adj, rev, nodes)

    print()
    print(f"  {PU}{B}◆ Communities — جوامع پکیج{R}")
    print(f"  {D}الگوریتم: Label Propagation{R}")
    print()

    # مرتب بر اساس اندازه
    sorted_groups = sorted(groups.values(), key=lambda x: -len(x))

    for i, group in enumerate(sorted_groups[:15], 1):
        if len(group) < min_size:
            continue
        group = sorted(group)
        print(f"  {CY}[{i}]{R} {WH}{len(group)} پکیج{R}")
        # نمایش ۶ تا اول
        sample = group[:6]
        for name in sample:
            print(f"      {D}•{R} {name}")
        if len(group) > 6:
            print(f"      {D}... و {len(group) - 6} بیشتر{R}")
        print()


def cmd_path(a, b):
    g = load_graph()
    if not g:
        print(f"  {RD}✗ گراف نیست{R}")
        return

    adj, rev, nodes = build_adj(g)
    a, b = a.lower(), b.lower()

    if a not in nodes:
        print(f"  {RD}✗ {a} در گراف نیست{R}")
        return
    if b not in nodes:
        print(f"  {RD}✗ {b} در گراف نیست{R}")
        return

    path = shortest_path(adj, rev, a, b)

    print()
    print(f"  {PU}{B}◆ Path: {a} → {b}{R}")
    print()

    if not path:
        print(f"  {RD}✗ مسیری نیست (تا عمق ۶){R}")
        return

    print(f"  {D}طول مسیر: {len(path) - 1} گام{R}")
    print()
    for i, n in enumerate(path):
        col = GR if i == 0 or i == len(path) - 1 else CY
        prefix = "  " if i == 0 else "  → "
        print(f"  {prefix}{col}{n}{R}")


def cmd_anomaly(threshold=2.0):
    g = load_graph()
    if not g:
        print(f"  {RD}✗ گراف نیست{R}")
        return

    adj, rev, nodes = build_adj(g)
    anom = anomalies(adj, rev, nodes, threshold)

    print()
    print(f"  {PU}{B}◆ Anomalies — پکیج‌های غیرمعمول{R}")
    print(f"  {D}الگوریتم: Z-score > {threshold}{R}")
    print()

    if not anom:
        print(f"  {D}چیزی غیرمعمول نیست{R}")
        return

    for s in anom:
        direction = "ورودی زیاد" if s["z"] > 0 else "خروجی زیاد"
        col = GR if s["z"] > 0 else OR
        print(f"  {col}{s['name']:25s}{R} "
              f"in={s['in']:3d} out={s['out']:3d} "
              f"ratio={s['ratio']:5.1f}  z={s['z']:+.2f}  "
              f"{D}{direction}{R}")


def cmd_stats():
    g = load_graph()
    if not g:
        print(f"  {RD}✗ گراف نیست{R}")
        return

    adj, rev, nodes = build_adj(g)
    edges = sum(len(adj[n]) for n in nodes)

    # درجه توزیع
    in_degs = [len(rev[n]) for n in nodes]
    out_degs = [len(adj[n]) for n in nodes]

    in_degs.sort(reverse=True)
    out_degs.sort(reverse=True)

    print()
    print(f"  {PU}{B}◆ Ecosystem Stats{R}")
    print()
    print(f"  {WH}نودها:{R}  {len(nodes)}")
    print(f"  {WH}یال‌ها:{R}  {edges}")
    print(f"  {WH}میانگین in-degree:{R}  "
          f"{sum(in_degs)/max(len(in_degs),1):.2f}")
    print(f"  {WH}میانگین out-degree:{R} "
          f"{sum(out_degs)/max(len(out_degs),1):.2f}")
    print()

    print(f"  {WH}Top-5 most depended-on:{R}")
    for n in nodes:
        pass
    top_in = sorted(nodes, key=lambda x: -len(rev[x]))[:5]
    for n in top_in:
        print(f"    {GR}{n:25s}{R}  {len(rev[n])} پکیج وابسته")

    print()
    print(f"  {WH}Top-5 with most deps:{R}")
    top_out = sorted(nodes, key=lambda x: -len(adj[x]))[:5]
    for n in top_out:
        print(f"    {OR}{n:25s}{R}  {len(adj[n])} وابستگی")


# ═══════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════

def main():
    if len(sys.argv) < 2:
        print()
        print(f"  {PU}{B}◆ ECOSYSTEM ORACLE{R}")
        print()
        print(f"  {WH}استفاده:{R}")
        print(f"    python feature_oracle.py rank          → PageRank")
        print(f"    python feature_oracle.py order <pkgs>  → ترتیب نصب")
        print(f"    python feature_oracle.py community     → جوامع")
        print(f"    python feature_oracle.py path A B      → مسیر")
        print(f"    python feature_oracle.py anomaly       → غیرمعمول‌ها")
        print(f"    python feature_oracle.py stats         → آمار")
        print()
        print(f"  {D}مثال‌ها:{R}")
        print(f"    python feature_oracle.py rank")
        print(f"    python feature_oracle.py order fastapi pandas")
        print(f"    python feature_oracle.py community")
        print(f"    python feature_oracle.py path fastapi django")
        print(f"    python feature_oracle.py anomaly")
        print()
        return

    cmd = sys.argv[1]

    if cmd == "rank":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        cmd_rank(limit)
    elif cmd == "order" and len(sys.argv) > 2:
        cmd_order(sys.argv[2:])
    elif cmd == "community":
        cmd_community()
    elif cmd == "path" and len(sys.argv) > 3:
        cmd_path(sys.argv[2], sys.argv[3])
    elif cmd == "anomaly":
        threshold = float(sys.argv[2]) if len(sys.argv) > 2 else 2.0
        cmd_anomaly(threshold)
    elif cmd == "stats":
        cmd_stats()
    else:
        print(f"  {RD}دستور نامعتبر{R}")


if __name__ == "__main__":
    main()
