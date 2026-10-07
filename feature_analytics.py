"""Graph Analytics — Betweenness, K-Core, Cycles, SimRank"""
import json, math, random, sys
from collections import defaultdict, deque, Counter
from pathlib import Path

BASE = Path.home() / "evoscanner"
DEPS = BASE / "deps_graph.json"

PU="\033[38;2;180;140;255m"
WH="\033[38;2;230;230;240m"
GY="\033[38;2;130;135;150m"
GR="\033[38;2;120;230;150m"
YL="\033[38;2;255;215;80m"
CY="\033[38;2;100;220;230m"
RD="\033[38;2;255;110;110m"
R="\033[0m"; B="\033[1m"; D="\033[2m"


def load():
    if not DEPS.exists(): return None
    try: return json.loads(DEPS.read_text())
    except: return None


def adj_of(g):
    adj = defaultdict(set); rev = defaultdict(set); nodes = set()
    for k, e in g.get("edges", {}).items():
        a, b = e["a"], e["b"]
        adj[a].add(b); rev[b].add(a)
        nodes.add(a); nodes.add(b)
    return adj, rev, nodes


def betweenness(adj, rev, nodes):
    nodes = list(nodes)
    BC = {n: 0.0 for n in nodes}
    for s in nodes:
        S = []; P = {n: [] for n in nodes}
        sigma = {n: 0.0 for n in nodes}; sigma[s] = 1.0
        d = {n: -1 for n in nodes}; d[s] = 0
        Q = deque([s])
        while Q:
            v = Q.popleft(); S.append(v)
            for w in adj[v] | rev[v]:
                if d[w] < 0:
                    Q.append(w); d[w] = d[v] + 1
                if d[w] == d[v] + 1:
                    sigma[w] += sigma[v]; P[w].append(v)
        delta = {n: 0.0 for n in nodes}
        while S:
            w = S.pop()
            for v in P[w]:
                if sigma[w] > 0:
                    delta[v] += (sigma[v] / sigma[w]) * (1 + delta[w])
            if w != s: BC[w] += delta[w]
    for n in BC: BC[n] /= 2.0
    return BC


def kcore(adj, rev, nodes):
    und = defaultdict(set)
    for n in nodes:
        for m in adj[n] | rev[n]:
            und[n].add(m); und[m].add(n)
    deg = {n: len(und[n]) for n in nodes}
    core = {}; remaining = set(nodes); k = 0
    while remaining:
        changed = True
        while changed:
            changed = False
            tr = [n for n in remaining if deg[n] <= k]
            for n in tr:
                core[n] = k
                remaining.discard(n)
                for m in und[n]:
                    if m in remaining: deg[m] -= 1
                changed = True
        k += 1
    return core


def find_cycles(adj, nodes, max_n=50, max_len=6):
    cycles = []; seen_global = set()
    def dfs(node, path, seen):
        if len(cycles) >= max_n or len(path) > max_len: return
        for nxt in adj[node]:
            if nxt == path[0] and len(path) >= 2:
                cycles.append(list(path))
                if len(cycles) >= max_n: return
            elif nxt not in seen and nxt not in seen_global:
                seen.add(nxt); path.append(nxt)
                dfs(nxt, path, seen)
                path.pop(); seen.discard(nxt)
    for s in sorted(nodes):
        if len(cycles) >= max_n: break
        dfs(s, [s], {s}); seen_global.add(s)
    uniq = []; keys = set()
    for c in cycles:
        key = tuple(sorted(c))
        if key not in keys: keys.add(key); uniq.append(c)
    return uniq


def simrank(adj, rev, nodes, target, top_k=15, iters=8, decay=0.8):
    nbrs = defaultdict(set)
    for n in nodes:
        for m in adj[n] | rev[n]:
            nbrs[n].add(m); nbrs[m].add(n)
    cand = {target}
    for n in nbrs[target]:
        cand.add(n)
        for m in nbrs[n]: cand.add(m)
    cand.discard(target)
    all_n = cand | {target}
    for n in list(all_n):
        for m in nbrs[n]:
            all_n.add(m); cand.add(m)
    cand.discard(target)
    S = {n: {m: (1.0 if n == m else 0.0) for m in all_n} for n in all_n}
    for _ in range(iters):
        ns = {}
        for a in all_n:
            ns[a] = {}
            a_n = [x for x in nbrs[a] if x in all_n]
            for b in all_n:
                if a == b: ns[a][b] = 1.0
                else:
                    b_n = [x for x in nbrs[b] if x in all_n]
                    if not a_n or not b_n: ns[a][b] = 0.0
                    else:
                        t = 0.0
                        for x in a_n:
                            for y in b_n: t += S[x].get(y, 0.0)
                        ns[a][b] = (decay / (len(a_n) * len(b_n))) * t
        S = ns
    scores = sorted([(n, S[target].get(n, 0.0)) for n in cand if n in S[target]],
                     key=lambda x: -x[1])
    return scores[:top_k]



def cmd_btw(limit=15):
    g = load()
    if not g: print(f"  {RD}✗ گراف نیست{R}"); return
    adj, rev, nodes = adj_of(g)
    print(f"  {D}محاسبه Betweenness روی {len(nodes)} نود...{R}")
    bc = betweenness(adj, rev, nodes)
    print()
    print(f"  {PU}{B}◆ Betweenness — پکیج‌های پل{R}")
    print()
    top = sorted(bc.items(), key=lambda x: -x[1])[:limit]
    mx = top[0][1] if top else 1
    for i, (n, s) in enumerate(top, 1):
        bar = int((s / mx) * 30) if mx else 0
        c = GR if i <= 3 else (YL if i <= 8 else CY)
        print(f"  {c}{i:2d}.{R} {WH}{n:25s}{R} {c}{s:8.2f}{R}  {D}{'█'*bar}{R}")


def cmd_kcore():
    g = load()
    if not g: print(f"  {RD}✗ گراف نیست{R}"); return
    adj, rev, nodes = adj_of(g)
    core = kcore(adj, rev, nodes)
    print()
    print(f"  {PU}{B}◆ K-Core Decomposition{R}")
    print()
    dist = Counter(core.values())
    mx = max(core.values()) if core else 0
    for k in range(mx, -1, -1):
        n = dist.get(k, 0)
        if n == 0: continue
        bar = "█" * min(n, 40)
        c = GR if k >= 4 else (YL if k >= 2 else CY)
        print(f"    {c}k={k:2d}{R}  {WH}{n:4d}{R} نود  {c}{bar}{R}")
    print()
    for k in range(mx, -1, -1):
        members = [x for x, c in core.items() if c == k]
        if not members or k < 2: continue
        print(f"  {GR}{B}k={k}{R} {D}({len(members)} پکیج){R}")
        for n in sorted(members)[:8]:
            print(f"    {D}•{R} {n}")
        if len(members) > 8:
            print(f"    {D}... و {len(members)-8} بیشتر{R}")
        print()


def cmd_cycles():
    g = load()
    if not g: print(f"  {RD}✗ گراف نیست{R}"); return
    adj, rev, nodes = adj_of(g)
    print(f"  {D}جستجوی دورها...{R}")
    cycles = find_cycles(adj, nodes)
    print()
    print(f"  {PU}{B}◆ Cycle Detection{R}")
    print()
    if not cycles:
        print(f"  {GR}✓ هیچ دوره‌ای نیست{R}")
        return
    print(f"  {RD}{len(cycles)} دور پیدا شد{R}\n")
    for i, c in enumerate(cycles[:20], 1):
        print(f"  {RD}[{i}]{R} {WH}{' → '.join(c + [c[0]])}{R}")


def cmd_simrank(target, limit=15):
    g = load()
    if not g: print(f"  {RD}✗ گراف نیست{R}"); return
    adj, rev, nodes = adj_of(g)
    if target not in nodes:
        print(f"  {RD}✗ {target} در گراف نیست{R}"); return
    print(f"  {D}محاسبه شباهت...{R}")
    scores = simrank(adj, rev, nodes, target, top_k=limit)
    print()
    print(f"  {PU}{B}◆ SimRank: شبیه‌های {target}{R}")
    print()
    for i, (n, s) in enumerate(scores, 1):
        if s < 0.01: continue
        bar = int(s * 30)
        c = GR if i <= 3 else (YL if i <= 8 else CY)
        print(f"  {c}{i:2d}.{R} {WH}{n:25s}{R} {c}{s:.4f}{R}  {D}{'█'*bar}{R}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"\n  {PU}{B}◆ GRAPH ANALYTICS{R}\n")
        print(f"  betweenness     → پکیج‌های پل")
        print(f"  kcore           → لایه‌های تراکم")
        print(f"  cycles          → دورهای وابستگی")
        print(f"  simrank <pkg>   → شبیه‌ها\n")
    else:
        c = sys.argv[1]
        if c == "betweenness": cmd_btw()
        elif c == "kcore": cmd_kcore()
        elif c == "cycles": cmd_cycles()
        elif c == "simrank" and len(sys.argv) > 2: cmd_simrank(sys.argv[2])
        else: print(f"  {RD}نامعتبر{R}")
