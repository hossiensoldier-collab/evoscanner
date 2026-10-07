"""Advanced Graph Algorithms — Influence, Weighted Community, Link Prediction"""
import json, math, random, sys
from collections import defaultdict, Counter, deque
from pathlib import Path

BASE = Path.home() / "evoscanner"
DEPS = BASE / "deps_graph.json"

PU="\033[38;2;180;140;255m"; WH="\033[38;2;230;230;240m"
GY="\033[38;2;130;135;150m"; GR="\033[38;2;120;230;150m"
YL="\033[38;2;255;215;80m"; CY="\033[38;2;100;220;230m"
RD="\033[38;2;255;110;110m"; PK="\033[38;2;255;140;200m"
R="\033[0m"; B="\033[1m"; D="\033[2m"


def load():
    if not DEPS.exists(): return None
    try: return json.loads(DEPS.read_text())
    except: return None


def adj_of(g, weighted=False):
    """گراف جهت‌دار. اگر weighted، وزن یال‌ها."""
    adj = defaultdict(dict)  # a → {b: weight}
    rev = defaultdict(dict)
    und = defaultdict(dict)  # بدون جهت برای community/link
    nodes = set()
    for k, e in g.get("edges", {}).items():
        a, b = e["a"], e["b"]
        w = e.get("observations", 1)
        adj[a][b] = w
        rev[b][a] = w
        und[a][b] = und[a].get(b, 0) + w
        und[b][a] = und[b].get(a, 0) + w
        nodes.add(a); nodes.add(b)
    return adj, rev, und, nodes


# ═══════════════════════════════════════════════════
#  1. INFLUENCE MAXIMIZATION (Kempe 2003)
# ═══════════════════════════════════════════════════

def ic_spread(und, seed, simulations=200):
    """
    Independent Cascade Model.
    هر یال احتمال p = 1/(1+exp(-w)) دارد.
    """
    if not seed: return 0
    total = 0
    for _ in range(simulations):
        activated = set(seed)
        frontier = list(seed)
        while frontier:
            new_frontier = []
            for u in frontier:
                for v, w in und[u].items():
                    if v in activated: continue
                    # احتمال سرایت
                    # احتمال واقعی: با w=1 → p=0.15، با w=3 → p=0.5
                    p = min(w * 0.15, 0.55)
                    if random.random() < p:
                        activated.add(v)
                        new_frontier.append(v)
            frontier = new_frontier
        total += len(activated)
    return total / simulations


DEV_TOOLS = {
    "flake8", "black", "ruff", "isort", "pylint", "mypy",
    "coverage", "pytest", "tox", "nox", "hypothesis",
    "pre-commit", "build", "twine", "wheel", "setuptools",
}


def greedy_influence(und, nodes, k=5, simulations=100):
    """
    Greedy: هر بار نودی که بیشترین spread اضافی دارد.
    """
    selected = []
    # حذف dev tools
    remaining = set(n for n in nodes if n not in DEV_TOOLS)

    for i in range(k):
        best_node = None
        best_score = -1

        for node in list(remaining):
            score = ic_spread(und, selected + [node], simulations=simulations)
            if score > best_score:
                best_score = score
                best_node = node

        if best_node is None:
            break
        selected.append(best_node)
        remaining.discard(best_node)

    return selected


def cmd_influence(k=5):
    g = load()
    if not g: print(f"  {RD}✗ گراف نیست{R}"); return
    adj, rev, und, nodes = adj_of(g)

    print(f"  {D}محاسبه Influence Maximization...{R}")
    print(f"  {D}الگوریتم: Greedy + Independent Cascade + Monte Carlo{R}")

    seeds = greedy_influence(und, nodes, k=k, simulations=50)

    # محاسبه spread نهایی
    final_spread = ic_spread(und, seeds, simulations=300)

    print()
    print(f"  {PU}{B}◆ Influence Maximization (k={k}){R}")
    print(f"  {D}اگر این {k} پکیج را انتخاب کنی، به {int(final_spread)} نود اثر می‌گذاری{R}")
    print(f"  {D}(از {len(nodes)} نود کل = {final_spread/len(nodes)*100:.1f}%){R}")
    print()

    for i, name in enumerate(seeds, 1):
        # spread انفرادی
        alone = ic_spread(und, [name], simulations=100)
        bar = int((alone / len(nodes)) * 40)
        col = GR if i <= 2 else (YL if i <= 4 else CY)
        print(f"  {col}{i}.{R} {WH}{name:25s}{R} {col}{alone:6.1f}{R} نود  {D}{'█'*bar}{R}")


def cmd_spread(pkg):
    g = load()
    if not g: print(f"  {RD}✗ گراف نیست{R}"); return
    adj, rev, und, nodes = adj_of(g)

    if pkg not in nodes:
        print(f"  {RD}✗ {pkg} در گراف نیست{R}"); return

    print(f"  {D}محاسبه اثر {pkg}...{R}")
    alone = ic_spread(und, [pkg], simulations=500)
    print()
    print(f"  {PU}{B}◆ اثر {pkg}{R}")
    print()
    print(f"  اگر فقط {pkg} را فعال کنی:")
    print(f"    → {GR}{alone:.1f}{R} نود تحت تأثیر")
    print(f"    → {GR}{alone/len(nodes)*100:.1f}%{R} از کل شبکه")
    print()

    # top neighbors
    print(f"  {D}مستقیم‌ترین سرایت‌ها:{R}")
    nbrs = sorted(und[pkg].items(), key=lambda x: -x[1])[:10]
    for n, w in nbrs:
        p = 1.0 / (1.0 + math.exp(-w))
        print(f"    {CY}{n:25s}{R} p={p:.2f}")


# ═══════════════════════════════════════════════════
#  2. WEIGHTED COMMUNITY (Label Propagation)
# ═══════════════════════════════════════════════════

def weighted_label_prop(und, nodes, iters=30, seed=42):
    """
    Label Propagation با وزن یال‌ها.
    هر نود لیبل همسایه با بیشترین weight مجموع را می‌گیرد.
    """
    random.seed(seed)
    labels = {n: n for n in nodes}

    for it in range(iters):
        order = list(nodes)
        random.shuffle(order)
        changed = 0

        for n in order:
            if not und[n]: continue

            # وزن هر لیبل
            label_weights = defaultdict(float)
            for m, w in und[n].items():
                label_weights[labels[m]] += w

            if not label_weights: continue

            # بهترین
            best_label = max(label_weights.items(), key=lambda x: (x[1], x[0]))[0]
            if labels[n] != best_label:
                labels[n] = best_label
                changed += 1

        if changed == 0:
            break

    # گروه‌بندی
    groups = defaultdict(list)
    for n, lb in labels.items():
        groups[lb].append(n)

    return {k: v for k, v in groups.items() if len(v) >= 3}


def modularity(und, nodes, communities):
    """
    Modularity Q = (1/2m) Σ [Aij - kikj/2m] δ(ci, cj)
    """
    # weight کل
    m = sum(w for n in und for w in und[n].values()) / 2.0
    if m == 0: return 0

    # درجه هر نود
    deg = {n: sum(und[n].values()) for n in nodes}

    # لیبل هر نود
    label_of = {}
    for label, members in communities.items():
        for n in members:
            label_of[n] = label

    Q = 0.0
    for i in nodes:
        for j, w in und[i].items():
            if label_of.get(i) == label_of.get(j):
                Q += w - (deg[i] * deg[j]) / (2 * m)
    return Q / (2 * m)


def cmd_community():
    g = load()
    if not g: print(f"  {RD}✗ گراف نیست{R}"); return
    adj, rev, und, nodes = adj_of(g)

    print(f"  {D}محاسبه Community (weighted)...{R}")
    groups = weighted_label_prop(und, nodes)

    # modularity
    Q = modularity(und, nodes, groups)

    print()
    print(f"  {PU}{B}◆ Weighted Communities{R}")
    print(f"  {D}الگوریتم: Label Propagation با وزن یال{R}")
    print(f"  {D}Modularity Q = {Q:.4f}{R}  ", end="")
    if Q > 0.3: print(f"{GR}(خوب){R}")
    elif Q > 0.15: print(f"{YL}(متوسط){R}")
    else: print(f"{RD}(ضعیف){R}")
    print()

    sorted_groups = sorted(groups.values(), key=lambda x: -len(x))

    for i, group in enumerate(sorted_groups[:12], 1):
        if len(group) < 3: continue
        print(f"  {CY}[{i}]{R} {WH}{len(group)} پکیج{R}")
        for n in sorted(group)[:6]:
            print(f"    {D}•{R} {n}")
        if len(group) > 6:
            print(f"    {D}... و {len(group)-6} بیشتر{R}")
        print()


# ═══════════════════════════════════════════════════
#  3. LINK PREDICTION
# ═══════════════════════════════════════════════════

def common_neighbors(und, a, b):
    return len(set(und[a].keys()) & set(und[b].keys()))


def jaccard(und, a, b):
    A = set(und[a].keys())
    B = set(und[b].keys())
    if not (A | B): return 0
    return len(A & B) / len(A | B)


def adamic_adar(und, a, b):
    """AA = Σ 1/log(deg(z)) برای z در همسایه‌های مشترک"""
    common = set(und[a].keys()) & set(und[b].keys())
    score = 0.0
    for z in common:
        deg = len(und[z])
        if deg > 1:
            score += 1.0 / math.log(deg)
    return score


def resource_allocation(und, a, b):
    """RA = Σ 1/deg(z)"""
    common = set(und[a].keys()) & set(und[b].keys())
    return sum(1.0 / len(und[z]) for z in common if len(und[z]) > 0)


def predict_links(und, nodes, top_k=20, method="adamic_adar"):
    """
    برای هر جفت بدون یال، امتیاز شباهت را محاسبه کن.
    """
    existing = set()
    for a in und:
        for b in und[a]:
            existing.add(tuple(sorted([a, b])))

    scores = []
    nodes_list = list(nodes)

    # برای هر نود، فقط ۲-hop ها را چک کن (کارایی)
    for a in nodes_list:
        candidates = set()
        for nbr in und[a]:
            for nbr2 in und[nbr]:
                if nbr2 != a and nbr2 not in und[a]:
                    candidates.add(nbr2)

        for b in candidates:
            key = tuple(sorted([a, b]))
            if key in existing:
                continue

            if method == "common":
                s = common_neighbors(und, a, b)
            elif method == "jaccard":
                s = jaccard(und, a, b)
            elif method == "ra":
                s = resource_allocation(und, a, b)
            else:  # adamic_adar
                s = adamic_adar(und, a, b)

            if s > 0:
                scores.append((a, b, s))

    # حذف تکراری
    seen = set()
    uniq = []
    for a, b, s in sorted(scores, key=lambda x: -x[2]):
        key = tuple(sorted([a, b]))
        if key in seen: continue
        seen.add(key)
        uniq.append((a, b, s))
        if len(uniq) >= top_k:
            break

    return uniq


def cmd_predict(method="adamic_adar", top_k=20):
    g = load()
    if not g: print(f"  {RD}✗ گراف نیست{R}"); return
    adj, rev, und, nodes = adj_of(g)

    print(f"  {D}محاسبه Link Prediction ({method})...{R}")

    preds = predict_links(und, nodes, top_k=top_k, method=method)

    names = {
        "adamic_adar": "Adamic-Adar",
        "jaccard": "Jaccard",
        "common": "Common Neighbors",
        "ra": "Resource Allocation",
    }

    print()
    print(f"  {PU}{B}◆ Link Prediction — {names.get(method, method)}{R}")
    print(f"  {D}یال‌هایی که احتمالاً در آینده شکل می‌گیرند{R}")
    print()

    for i, (a, b, s) in enumerate(preds, 1):
        bar = int(min(s, 5) * 6)
        col = GR if i <= 5 else (YL if i <= 12 else CY)
        print(f"  {col}{i:2d}.{R} {WH}{a:22s}{R} ↔ {WH}{b:22s}{R} "
              f"{col}{s:6.3f}{R}  {D}{'█'*bar}{R}")


def cmd_predict_all():
    g = load()
    if not g: print(f"  {RD}✗ گراف نیست{R}"); return
    adj, rev, und, nodes = adj_of(g)

    print()
    print(f"  {PU}{B}◆ Link Prediction — همه روش‌ها{R}")
    print()

    for method in ("adamic_adar", "jaccard", "common", "ra"):
        preds = predict_links(und, nodes, top_k=5, method=method)
        print(f"  {CY}{B}{method}{R}:")
        for a, b, s in preds:
            print(f"    {WH}{a}{R} ↔ {WH}{b}{R}  ({s:.3f})")
        print()


# ═══════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print()
        print(f"  {PU}{B}◆ ADVANCED ALGORITHMS{R}")
        print()
        print(f"  influence [k]       → Influence Maximization (Kempe 2003)")
        print(f"  spread <pkg>        → اثر یک پکیج")
        print(f"  community           → Weighted Community Detection")
        print(f"  predict [method]    → Link Prediction")
        print(f"  predict-all         → همه روش‌های Link Prediction")
        print()
        print(f"  {D}روش‌ها: adamic_adar, jaccard, common, ra{R}")
        print()
    else:
        c = sys.argv[1]
        if c == "influence":
            k = int(sys.argv[2]) if len(sys.argv) > 2 else 5
            cmd_influence(k)
        elif c == "spread" and len(sys.argv) > 2:
            cmd_spread(sys.argv[2])
        elif c == "community":
            cmd_community()
        elif c == "predict":
            m = sys.argv[2] if len(sys.argv) > 2 else "adamic_adar"
            cmd_predict(m)
        elif c == "predict-all":
            cmd_predict_all()
        else:
            print(f"  {RD}نامعتبر{R}")
