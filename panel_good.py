#!/usr/bin/env python3
"""EvoScanner Control Panel - Finglish"""
import json, os, subprocess, sys, time, urllib.parse, urllib.request
from datetime import datetime
from pathlib import Path

DIR = Path(__file__).parent
API = "http://localhost:8081"
CONFIG = DIR / "panel_config.json"
HISTORY = DIR / "panel_history.json"
BOOKMARKS = DIR / "panel_bookmarks.json"
SNAPS = DIR / "snapshots"
SNAPS.mkdir(exist_ok=True)

THEMES = {
    "default": {
        "R":"\033[0;31m","G":"\033[0;32m","Y":"\033[1;33m",
        "B":"\033[0;34m","M":"\033[0;35m","Cy":"\033[0;36m",
        "W":"\033[1;37m","D":"\033[0m","Bold":"\033[1m","Dim":"\033[2m",
    },
    "green": {
        "R":"\033[0;91m","G":"\033[0;92m","Y":"\033[0;93m",
        "B":"\033[0;94m","M":"\033[0;95m","Cy":"\033[0;96m",
        "W":"\033[1;97m","D":"\033[0m","Bold":"\033[1m","Dim":"\033[2m",
    },
    "no-color": {k:"" for k in
        ["R","G","Y","B","M","Cy","W","D","Bold","Dim"]},
}

def load_config():
    global C
    if CONFIG.exists():
        try:
            cfg = json.loads(CONFIG.read_text())
            C = THEMES.get(cfg.get("theme","default"), THEMES["default"])
            return cfg
        except Exception:
            pass
    return {"theme":"default","confirm_dangerous":True}

def save_config(cfg):
    CONFIG.write_text(json.dumps(cfg, indent=2))

C = THEMES["default"]
CFG = load_config()


def clear(): os.system("clear")
def hr(w=62): print(C["Dim"] + "-"*w + C["D"])
def title(t):
    print()
    print(C["Bold"] + C["Cy"] + ">> " + t + C["D"])
    hr()
def ok(t):   print(C["G"] + "  [OK] " + C["D"] + t)
def warn(t): print(C["Y"] + "  [!!] " + C["D"] + t)
def err(t):  print(C["R"] + "  [XX] " + C["D"] + t)
def info(t): print(C["B"] + "  [i]  " + C["D"] + t)

def pause(msg="Enter bezan..."):
    try: input(C["Dim"] + "\n" + msg + C["D"])
    except (EOFError, KeyboardInterrupt): print()

def ask(p, default=""):
    try:
        s = input(C["Bold"] + C["M"] + "> " + C["D"] + p +
                  (f" [{default}]" if default else "") + ": ").strip()
        return s or default
    except (EOFError, KeyboardInterrupt): return ""

def confirm(p):
    if not CFG.get("confirm_dangerous", True): return True
    try:
        s = input(C["Y"] + "? " + C["D"] + p + " (b/n): ").strip().lower()
        return s in ("b","y","yes","بله")
    except (EOFError, KeyboardInterrupt): return False


# History/Bookmarks
def load_history():
    if HISTORY.exists():
        try: return json.loads(HISTORY.read_text())
        except Exception: pass
    return {"searches":[],"asks":[],"related":[],"commands":[]}

def save_history(h):
    for k in ("searches","asks","related"):
        h[k] = h.get(k,[])[-50:]
    h["commands"] = h.get("commands",[])[-100:]
    HISTORY.write_text(json.dumps(h, indent=2, ensure_ascii=False))

def hist_add(kind, value):
    h = load_history()
    h[kind] = [x for x in h.get(kind,[]) if x["value"] != value]
    h[kind].append({"value":value,"ts":datetime.now().isoformat()})
    save_history(h)

def load_bookmarks():
    if BOOKMARKS.exists():
        try: return json.loads(BOOKMARKS.read_text())
        except Exception: pass
    return {"packages":[],"queries":[],"resources":[]}

def save_bookmarks(b): BOOKMARKS.write_text(json.dumps(b, indent=2, ensure_ascii=False))

def bm_add(kind, value):
    b = load_bookmarks()
    if value not in b[kind]:
        b[kind].append(value); save_bookmarks(b); return True
    return False


# Snapshots
def snapshot():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    info = {"ts":ts,"db":0,"graph_ents":0,"graph_edges":0,"cooc":0}
    try:
        import sqlite3
        db = sqlite3.connect(DIR/"knowledge.db")
        info["db"] = db.execute("SELECT COUNT(*) FROM resources").fetchone()[0]
        db.close()
    except Exception: pass
    try:
        g = json.loads((DIR/"graph.json").read_text())
        info["graph_ents"] = sum(1 for v in g["nodes"].values() if v.get("type")=="entity")
        info["graph_edges"] = len(g.get("edges",{}))
        info["cooc"] = len(g.get("cooc",{}))
    except Exception: pass
    (SNAPS/f"{ts}.json").write_text(json.dumps(info, indent=2))
    return info

def diff_snaps():
    files = sorted(SNAPS.glob("*.json"))
    if len(files) < 2:
        warn("Hadaghal 2 snapshot lazem ast"); return
    a = json.loads(files[-2].read_text())
    b = json.loads(files[-1].read_text())
    print(f"\n{C['Cy']}Tafavot: {a['ts']}  →  {b['ts']}{C['D']}\n")
    hr()
    for f in ("db","graph_ents","graph_edges","cooc"):
        if f in a and f in b:
            d = b[f] - a[f]
            sign = "+" if d > 0 else ""
            col = C["G"] if d > 0 else (C["R"] if d < 0 else C["Dim"])
            print(f"  {f:14s} {a[f]:5d}  →  {b[f]:5d}   {col}{sign}{d}{C['D']}")
    print()


# API
def api_up():
    try:
        urllib.request.urlopen(API+"/health", timeout=2); return True
    except Exception: return False

def api_get(path):
    try:
        with urllib.request.urlopen(API+path, timeout=15) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e: return {"error":str(e)}

def api_post(path, data):
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(API+path, data=body,
        headers={"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e: return {"error":str(e)}

def start_api():
    if api_up(): return True
    subprocess.Popen([sys.executable,"api.py"], cwd=str(DIR),
                     stdout=open(DIR/"api.log","w"),
                     stderr=subprocess.STDOUT)
    time.sleep(2)
    return api_up()

def run(args):
    if isinstance(args, str): args = [args]
    hist_add("commands", " ".join(args))
    try:
        subprocess.run([sys.executable,"evoscanner_v2.py"]+args, cwd=str(DIR))
    except KeyboardInterrupt: print()


# Banner
def banner():
    clear()
    print()
    print(C["Cy"] + "  +======================================+" + C["D"])
    print(C["Cy"] + "  |    E V O S C A N N E R   C P  v3     |" + C["D"])
    print(C["Cy"] + "  +======================================+" + C["D"])
    print()

def show_status():
    a = C["G"]+"ONLINE"+C["D"] if api_up() else C["R"]+"OFFLINE"+C["D"]
    print(f"  API {a}", end="   ")
    try:
        import sqlite3
        db = sqlite3.connect(DIR/"knowledge.db")
        n = db.execute("SELECT COUNT(*) FROM resources").fetchone()[0]
        db.close()
        print(f"Manabe {C['Y']}{n}{C['D']}", end="   ")
    except Exception:
        print(f"Manabe {C['R']}-{C['D']}", end="   ")
    try:
        g = json.loads((DIR/"graph.json").read_text())
        ents = sum(1 for v in g["nodes"].values() if v.get("type")=="entity")
        print(f"Graph {C['Cy']}{ents}{C['D']}/{len(g['edges'])}", end="")
    except Exception:
        print("Graph -", end="")
    snaps = len(list(SNAPS.glob("*.json")))
    print(f"   Snap {snaps}")


def main_menu():
    banner()
    show_status()
    print()
    hr()
    print(f"  {C['Y']}[1]{C['D']}  Kavosh va Jostojo        {C['Dim']}jostjo, related, soaal{C['D']}")
    print(f"  {C['Y']}[2]{C['D']}  Jam'avari va Scan        {C['Dim']}run, enrich, hunter{C['D']}")
    print(f"  {C['Y']}[3]{C['D']}  Yadgiri va Hadaf        {C['Dim']}masir, ahdaf{C['D']}")
    print(f"  {C['Y']}[4]{C['D']}  Ejenthaye Khodkarpardaz  {C['Dim']}agents, selfmod{C['D']}")
    print(f"  {C['Y']}[5]{C['D']}  Data va Export           {C['Dim']}export, snapshot{C['D']}")
    print(f"  {C['Y']}[6]{C['D']}  Server-ha                {C['Dim']}API, web, IDE{C['D']}")
    print(f"  {C['Y']}[7]{C['D']}  Graph Explorer           {C['Dim']}entities, paths{C['D']}")
    print(f"  {C['Y']}[8]{C['D']}  Bookmark-ha va Tarikh    {C['Dim']}saved{C['D']}")
    print(f"  {C['Y']}[9]{C['D']}  Tanzimat                 {C['Dim']}theme, config{C['D']}")
    print(f"  {C['Y']}[0]{C['D']}  Khorooj")
    hr()
    return ask("Entekhab")


# ── Explore ──
def menu_explore():
    while True:
        banner()
        title("Kavosh va Jostojo")
        print(f"  {C['Y']}[1]{C['D']}  Jostjo dar database")
        print(f"  {C['Y']}[2]{C['D']}  Package-haye related")
        print(f"  {C['Y']}[3]{C['D']}  Soaal bepors (RAG)")
        print(f"  {C['Y']}[4]{C['D']}  Masir dar graph")
        print(f"  {C['Y']}[5]{C['D']}  Pishnahad import")
        print(f"  {C['Y']}[6]{C['D']}  Graph Explorer (zirmenu)")
        print(f"  {C['Y']}[7]{C['D']}  Bartarin manabe")
        print(f"  {C['Y']}[8]{C['D']}  Jostjo-haye akhir")
        print(f"  {C['Y']}[0]{C['D']}  Bargasht")
        hr()
        c = ask("Entekhab")
        if c == "0": return
        elif c == "1":
            q = ask("Query")
            if q:
                hist_add("searches", q); cmd_search(q)
                if confirm("Bookmark konam?"): bm_add("queries", q)
                pause()
        elif c == "2":
            h = load_history()
            recent = ", ".join(x["value"] for x in h["related"][-3:])
            p = ask("Package" + (f" [akhir: {recent}]" if recent else ""))
            if p:
                hist_add("related", p); cmd_related(p)
                if confirm("Bookmark konam?"): bm_add("packages", p)
                pause()
        elif c == "3":
            q = ask("Soaal")
            if q:
                hist_add("asks", q); cmd_ask(q); pause()
        elif c == "4":
            a = ask("Az"); b = ask("Be")
            if a and b: cmd_path(a, b); pause()
        elif c == "5":
            f = ask("File", str(Path.home()/"project.py"))
            cmd_suggest(f); pause()
        elif c == "6": menu_graph()
        elif c == "7": run(["top","25"]); pause()
        elif c == "8": show_recent("searches"); pause()


# ── Graph ──
def menu_graph():
    while True:
        banner()
        title("Graph Explorer")
        try:
            g = json.loads((DIR/"graph.json").read_text())
            ents = sum(1 for v in g["nodes"].values() if v.get("type")=="entity")
            print(f"  {C['Dim']}Graph: {ents} entity, "
                  f"{len(g['edges'])} yal, {len(g.get('cooc',{}))} cooc{C['D']}")
            print()
        except Exception:
            err("graph.json nist"); pause(); return
        print(f"  {C['Y']}[1]{C['D']}  Bartarin entity-ha")
        print(f"  {C['Y']}[2]{C['D']}  Related (co-occurrence)")
        print(f"  {C['Y']}[3]{C['D']}  Ham-daste (peers)")
        print(f"  {C['Y']}[4]{C['D']}  Hamsaye-ha (edges)")
        print(f"  {C['Y']}[5]{C['D']}  Kotah-tarin masir A -> B")
        print(f"  {C['Y']}[6]{C['D']}  Filter bar asas daste")
        print(f"  {C['Y']}[7]{C['D']}  Export graph (JSON)")
        print(f"  {C['Y']}[8]{C['D']}  Namayeshi ASCII")
        print(f"  {C['Y']}[9]{C['D']}  Amar-e tafsili")
        print(f"  {C['Y']}[0]{C['D']}  Bargasht")
        hr()
        c = ask("Entekhab")
        if c == "0": return
        elif c == "1": cmd_graph_top(25); pause()
        elif c == "2":
            p = ask("Package")
            if p: cmd_graph_related(p); pause()
        elif c == "3":
            p = ask("Package")
            if p: cmd_graph_peers(p); pause()
        elif c == "4":
            p = ask("Node")
            if p: cmd_graph_neighbors(p); pause()
        elif c == "5":
            a = ask("Az"); b = ask("Be")
            if a and b: cmd_path(a, b); pause()
        elif c == "6":
            cat = ask("Daste (web/ml-ai/async... khali=bame)")
            cmd_graph_by_cat(cat); pause()
        elif c == "7": cmd_graph_export(); pause()
        elif c == "8": cmd_graph_ascii(); pause()
        elif c == "9": cmd_graph_stats(); pause()


def cmd_graph_top(n=25):
    try: g = json.loads((DIR/"graph.json").read_text())
    except Exception: err("graph.json nist"); return
    ents = [(k,v.get("count",0),v.get("cats",{}))
            for k,v in g["nodes"].items()
            if v.get("type")=="entity" and not k.startswith("cat:")]
    ents.sort(key=lambda x:-x[1])
    print(f"\n{C['Cy']}Top {n} entity:{C['D']}\n")
    for name,cnt,cats in ents[:n]:
        main = max(cats,key=cats.get) if cats else "?"
        bar = C["Cy"] + "#"*min(cnt,30) + C["D"]
        print(f"  {name:28s} {cnt:4d}  {bar}  {C['Dim']}[{main}]{C['D']}")

def cmd_graph_related(pkg):
    try: g = json.loads((DIR/"graph.json").read_text())
    except Exception: err("graph.json nist"); return
    pkg = pkg.lower()
    cooc = g.get("cooc",{}); nodes = g.get("nodes",{})
    info = nodes.get(pkg,{})
    cats = info.get("cats",{})
    main = max(cats,key=cats.get) if cats else "?"
    print(f"\n{C['Cy']}{pkg}{C['D']}  {C['Dim']}[{main}]  {info.get('count',0)}x{C['D']}")
    hr()
    rels = []
    for pair,w in cooc.items():
        a,b = pair.split("|",1)
        if a.startswith("cat:") or b.startswith("cat:"): continue
        if a==pkg: rels.append((b,w))
        elif b==pkg: rels.append((a,w))
    rels.sort(key=lambda x:-x[1])
    if not rels: warn("Chizi peyda nashod"); return
    for name,w in rels[:30]:
        bar = C["G"] + "#"*min(w,30) + C["D"]
        print(f"  {name:28s} {w:4d}  {bar}")

def cmd_graph_peers(pkg):
    try: g = json.loads((DIR/"graph.json").read_text())
    except Exception: err("graph.json nist"); return
    pkg = pkg.lower()
    nodes = g.get("nodes",{})
    info = nodes.get(pkg,{})
    cats = info.get("cats",{})
    if not cats: warn(f"{pkg} daste nadarad"); return
    print(f"\n{C['Cy']}Ham-daste-haye {pkg} [{max(cats,key=cats.get)}]{C['D']}\n")
    peers = {}
    for n,v in nodes.items():
        if v.get("type")!="entity" or n==pkg or n.startswith("cat:"): continue
        for c in cats:
            if v.get("cats",{}).get(c):
                peers[n] = peers.get(n,0) + v["cats"][c]
    for name,w in sorted(peers.items(),key=lambda x:-x[1])[:25]:
        bar = C["M"] + "#"*min(w,25) + C["D"]
        print(f"  {name:28s} {w:4d}  {bar}")

def cmd_graph_neighbors(node):
    try: g = json.loads((DIR/"graph.json").read_text())
    except Exception: err("graph.json nist"); return
    node = node.lower()
    edges = g.get("edges",{}); nodes = g.get("nodes",{})
    print(f"\n{C['Cy']}Hamsaye-haye {node}{C['D']}\n")
    found = 0
    for key,w in edges.items():
        a,b = key.split("\u2192",1)
        if a == node:
            info = nodes.get(b,{})
            title = info.get("title",b)[:50]
            print(f"  {C['Dim']}->{C['D']} {b:30s} w={w}  {title}")
            found += 1
        elif b == node:
            info = nodes.get(a,{})
            title = info.get("title",a)[:50]
            print(f"  {C['Dim']}<-{C['D']} {a:30s} w={w}  {title}")
            found += 1
    if not found: warn("Hamsaye nadarad")

def cmd_graph_by_cat(cat):
    try: g = json.loads((DIR/"graph.json").read_text())
    except Exception: err("graph.json nist"); return
    nodes = g.get("nodes",{})
    cat = cat.strip()
    print(f"\n{C['Cy']}Entity-ha dar daste '{cat or 'hame'}':{C['D']}\n")
    items = []
    for n,v in nodes.items():
        if v.get("type")!="entity" or n.startswith("cat:"): continue
        cats = v.get("cats",{})
        if not cat or cat in cats:
            items.append((n,v.get("count",0),
                         max(cats,key=cats.get) if cats else "?"))
    items.sort(key=lambda x:-x[1])
    if not items: warn("Chizi nist"); return
    for name,cnt,c in items[:40]:
        print(f"  {name:28s} {cnt:4d}  {C['Dim']}[{c}]{C['D']}")
    print(f"\n  {C['Dim']}Jami: {len(items)}{C['D']}")

def cmd_graph_export():
    try: g = json.loads((DIR/"graph.json").read_text())
    except Exception: err("graph.json nist"); return
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = DIR/"exports"/f"graph_{ts}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(g, ensure_ascii=False, indent=2))
    ok(f"Export shod: {out.name}")
    print(f"  {C['Dim']}Andaze: {out.stat().st_size//1024} KB{C['D']}")

def cmd_graph_ascii():
    try: g = json.loads((DIR/"graph.json").read_text())
    except Exception: err("graph.json nist"); return
    nodes = g["nodes"]
    cats = {}
    for n,v in nodes.items():
        if v.get("type")!="entity" or n.startswith("cat:"): continue
        nc = v.get("cats",{})
        if not nc: continue
        main = max(nc,key=nc.get)
        cats.setdefault(main,[]).append((n,v.get("count",0)))
    print(f"\n{C['Cy']}Naghshe daste-ha{C['D']}\n")
    for cat,items in sorted(cats.items(),key=lambda x:-len(x[1])):
        items.sort(key=lambda x:-x[1])
        print(f"\n  {C['Bold']}{C['Y']}[{cat}]{C['D']}  "
              f"{C['Dim']}({len(items)} node){C['D']}")
        for name,cnt in items[:8]:
            dots = "."*min(cnt,30)
            print(f"    {name:26s} {C['Cy']}{dots}{C['D']}")

def cmd_graph_stats():
    try: g = json.loads((DIR/"graph.json").read_text())
    except Exception: err("graph.json nist"); return
    nodes = g["nodes"]
    ents = [v for v in nodes.values() if v.get("type")=="entity"]
    res = [v for v in nodes.values() if v.get("type")=="resource"]
    cooc = g.get("cooc",{})
    cats = {}
    for n,v in nodes.items():
        if v.get("type")!="entity" or n.startswith("cat:"): continue
        for c,cnt in v.get("cats",{}).items():
            cats[c] = cats.get(c,0) + cnt
    print(f"\n{C['Cy']}Amar-e Graph{C['D']}\n"); hr()
    print(f"  Entity-ha:  {len(ents)}")
    print(f"  Manabe:     {len(res)}")
    print(f"  Yal-ha:     {len(g['edges'])}")
    print(f"  Co-occur:   {len(cooc)}")
    print(f"\n  {C['Y']}Bar asas daste:{C['D']}")
    for cat,cnt in sorted(cats.items(),key=lambda x:-x[1]):
        print(f"    {cat:14s} {cnt:5d}")
    print(f"\n  {C['Y']}Top 5 connected:{C['D']}")
    degree = {}
    for key,w in g["edges"].items():
        a,b = key.split("\u2192",1)
        degree[a] = degree.get(a,0) + w
    for name,d in sorted(degree.items(),key=lambda x:-x[1])[:5]:
        print(f"    {name:24s} {d}")


# ── Collect ──
def menu_collect():
    while True:
        banner()
        title("Jam'avari va Scan")
        print(f"  {C['Y']}[1]{C['D']}  Ejraye cycle kashf")
        print(f"  {C['Y']}[2]{C['D']}  Reset health")
        print(f"  {C['Y']}[3]{C['D']}  Enrich (gereftan README)")
        print(f"  {C['Y']}[4]{C['D']}  Rebuild graph")
        print(f"  {C['Y']}[5]{C['D']}  Hunter (UCB query)")
        print(f"  {C['Y']}[6]{C['D']}  Pishnahad query baraye gap")
        print(f"  {C['Y']}[7]{C['D']}  Kashfe daste jadid")
        print(f"  {C['Y']}[8]{C['D']}  Gozaresh query-ha")
        print(f"  {C['Y']}[0]{C['D']}  Bargasht")
        hr()
        c = ask("Entekhab")
        if c == "0": return
        if c == "1":
            n = ask("Tedade cycle","2")
            run(["reset-health"]); run(["run",n]); run(["rebuild"]); pause()
        elif c == "2": run(["reset-health"]); pause()
        elif c == "3":
            n = ask("Tedad","30")
            if not api_up(): start_api()
            run(["enrich",n]); run(["rebuild"]); pause()
        elif c == "4": run(["rebuild"]); pause()
        elif c == "5": run(["learn"]); pause()
        elif c == "6": run(["suggest"]); pause()
        elif c == "7": run(["discover","8"]); pause()
        elif c == "8": run(["learn","report"]); pause()


# ── Learning ──
def menu_learning():
    while True:
        banner()
        title("Yadgiri va Hadaf")
        print(f"  {C['Y']}[1]{C['D']}  List ahdaf")
        print(f"  {C['Y']}[2]{C['D']}  Backend")
        print(f"  {C['Y']}[3]{C['D']}  Machine Learning")
        print(f"  {C['Y']}[4]{C['D']}  Data Analyst")
        print(f"  {C['Y']}[5]{C['D']}  DevOps")
        print(f"  {C['Y']}[6]{C['D']}  Security")
        print(f"  {C['Y']}[7]{C['D']}  Masire sojeye delkhah")
        print(f"  {C['Y']}[0]{C['D']}  Bargasht")
        hr()
        c = ask("Entekhab")
        if c == "0": return
        if c == "1": run(["goals"]); pause()
        elif c in "23456":
            g = ["backend","ml","data","devops","security"][int(c)-2]
            run(["goal",g]); pause()
        elif c == "7":
            t = ask("Sojeye (mesl asyncio)")
            if t: run(["path",t]); pause()


# ── Agents ──
def menu_agents():
    while True:
        banner()
        title("Ejenthaye Khodkarpardaz")
        print(f"  {C['Y']}[1]{C['D']}  Ejraye 4 ejent")
        print(f"  {C['Y']}[2]{C['D']}  Gozaresh ejent-ha")
        print(f"  {C['Y']}[3]{C['D']}  Tahlil code (Selfmod)")
        print(f"  {C['Y']}[4]{C['D']}  Tarikhche taghirat")
        print(f"  {C['Y']}[5]{C['D']}  Rollback akharin taghir")
        print(f"  {C['Y']}[6]{C['D']}  Compress graph")
        print(f"  {C['Y']}[0]{C['D']}  Bargasht")
        hr()
        c = ask("Entekhab")
        if c == "0": return
        if c == "1": run(["agents"]); pause()
        elif c == "2": run(["agents-report"]); pause()
        elif c == "3": run(["selfmod","all"]); pause()
        elif c == "4": run(["selfmod","history"]); pause()
        elif c == "5":
            if confirm("Rollback konam?"): run(["selfmod","rollback"]); pause()
        elif c == "6":
            if confirm("Compress konam?"): run(["compress"]); pause()


# ── Data ──
def menu_data():
    while True:
        banner()
        title("Data va Export")
        print(f"  {C['Y']}[1]{C['D']}  Export kamel")
        print(f"  {C['Y']}[2]{C['D']}  Gozaresh Markdown")
        print(f"  {C['Y']}[3]{C['D']}  Amar-e koli")
        print(f"  {C['Y']}[4]{C['D']}  Daste-ha")
        print(f"  {C['Y']}[5]{C['D']}  Liste file-haye exports")
        print(f"  {C['Y']}[6]{C['D']}  Sakhte snapshot")
        print(f"  {C['Y']}[7]{C['D']}  Tafavot 2 snapshot akhar")
        print(f"  {C['Y']}[8]{C['D']}  Liste snapshot-ha")
        print(f"  {C['Y']}[0]{C['D']}  Bargasht")
        hr()
        c = ask("Entekhab")
        if c == "0": return
        elif c == "1": run(["export"]); pause()
        elif c == "2": run(["report"]); pause()
        elif c == "3": run(["stats"]); pause()
        elif c == "4": run(["categories"]); pause()
        elif c == "5":
            print()
            ex = DIR/"exports"
            if ex.exists():
                files = sorted(ex.iterdir(), key=lambda f:f.stat().st_mtime, reverse=True)[:15]
                for f in files:
                    print(f"  {C['Cy']}{f.name}{C['D']}  {C['Dim']}{f.stat().st_size//1024}KB{C['D']}")
            pause()
        elif c == "6":
            i = snapshot()
            ok(f"Snapshot: {i['ts']}  DB={i['db']}  entity={i['graph_ents']}")
            pause()
        elif c == "7": diff_snaps(); pause()
        elif c == "8":
            for f in sorted(SNAPS.glob("*.json"), reverse=True):
                print(f"  {C['Cy']}{f.stem}{C['D']}")
            pause()


# ── Servers ──
def menu_servers():
    while True:
        banner()
        title("Server-ha")
        a = C["G"]+"ONLINE"+C["D"] if api_up() else C["R"]+"OFFLINE"+C["D"]
        print(f"  API: {a}")
        print()
        print(f"  {C['Y']}[1]{C['D']}  Start API (:8081)")
        print(f"  {C['Y']}[2]{C['D']}  Stop API")
        print(f"  {C['Y']}[3]{C['D']}  Graph web (:8080)")
        print(f"  {C['Y']}[4]{C['D']}  DB web (:8080)")
        print(f"  {C['Y']}[5]{C['D']}  Watch file")
        print(f"  {C['Y']}[6]{C['D']}  Text IDE")
        print(f"  {C['Y']}[0]{C['D']}  Bargasht")
        hr()
        c = ask("Entekhab")
        if c == "0": return
        if c == "1":
            if start_api(): ok("API roshan shod")
            else: err("API roshan nashod")
            pause()
        elif c == "2":
            subprocess.run(["pkill","-f","api.py"])
            ok("API khamoosh shod"); pause()
        elif c == "3":
            if not api_up(): start_api()
            print(f"\n{C['Cy']}http://localhost:8080{C['D']}\n")
            try:
                subprocess.run([sys.executable,"evoscanner_v2.py","graphweb"], cwd=str(DIR))
            except KeyboardInterrupt: pass
            pause()
        elif c == "4":
            print(f"\n{C['Cy']}http://localhost:8080{C['D']}\n")
            try:
                subprocess.run([sys.executable,"evoscanner_v2.py","web"], cwd=str(DIR))
            except KeyboardInterrupt: pass
            pause()
        elif c == "5":
            f = ask("File", str(Path.home()/"project.py"))
            print(f"\n{C['Dim']}Ctrl+C baraye tavaghof{C['D']}\n")
            try: subprocess.run(["bash","watch.sh",f], cwd=str(DIR))
            except KeyboardInterrupt: pass
            pause()
        elif c == "6":
            f = ask("File", str(Path.home()/"project.py"))
            if not api_up(): start_api()
            try: subprocess.run([sys.executable,"evoide.py",f], cwd=str(DIR))
            except KeyboardInterrupt: pass
            pause()


# ── Bookmarks ──
def menu_bookmarks():
    while True:
        banner()
        title("Bookmark-ha va Tarikhche")
        b = load_bookmarks(); h = load_history()
        print(f"  {C['Y']}[1]{C['D']}  Package-haye bookmark  {C['Dim']}({len(b['packages'])}){C['D']}")
        print(f"  {C['Y']}[2]{C['D']}  Query-haye bookmark   {C['Dim']}({len(b['queries'])}){C['D']}")
        print(f"  {C['Y']}[3]{C['D']}  Jostjo-haye akhir      {C['Dim']}({len(h['searches'])}){C['D']}")
        print(f"  {C['Y']}[4]{C['D']}  Soaal-haye akhir       {C['Dim']}({len(h['asks'])}){C['D']}")
        print(f"  {C['Y']}[5]{C['D']}  Package-haye akhir     {C['Dim']}({len(h['related'])}){C['D']}")
        print(f"  {C['Y']}[6]{C['D']}  Pak kardan tarikhche")
        print(f"  {C['Y']}[0]{C['D']}  Bargasht")
        hr()
        c = ask("Entekhab")
        if c == "0": return
        elif c == "1":
            for p in b["packages"]: print(f"  {C['Cy']}{p}{C['D']}")
            pause()
        elif c == "2":
            for q in b["queries"]: print(f"  {C['Cy']}{q}{C['D']}")
            pause()
        elif c == "3": show_recent("searches"); pause()
        elif c == "4": show_recent("asks"); pause()
        elif c == "5": show_recent("related"); pause()
        elif c == "6":
            if confirm("Tarikhche pak shavad?"):
                HISTORY.write_text("{}"); ok("Pak shod"); pause()


# ── Settings ──
def menu_settings():
    global C, CFG
    while True:
        banner()
        title("Tanzimat")
        print(f"  {C['Y']}[1]{C['D']}  Theme: {C['Cy']}{CFG.get('theme','default')}{C['D']}")
        print(f"  {C['Y']}[2]{C['D']}  Confirm dangerous: {C['Cy']}{CFG.get('confirm_dangerous',True)}{C['D']}")
        print(f"  {C['Y']}[3]{C['D']}  Reset be default")
        print(f"  {C['Y']}[4]{C['D']}  Namayesh config")
        print(f"  {C['Y']}[0]{C['D']}  Bargasht")
        hr()
        c = ask("Entekhab")
        if c == "0": return
        elif c == "1":
            print(f"\n  Mojood: {', '.join(THEMES.keys())}")
            t = ask("Theme", CFG.get("theme","default"))
            if t in THEMES:
                CFG["theme"] = t; save_config(CFG)
                C = THEMES[t]; ok(f"Theme shod {t}")
            else: err("Theme na-shenakhte")
            pause()
        elif c == "2":
            CFG["confirm_dangerous"] = not CFG.get("confirm_dangerous",True)
            save_config(CFG)
            ok(f"Confirm = {CFG['confirm_dangerous']}"); pause()
        elif c == "3":
            CFG = {"theme":"default","confirm_dangerous":True}
            save_config(CFG); C = THEMES["default"]
            ok("Reset shod"); pause()
        elif c == "4":
            print(f"\n  {CONFIG}")
            if CONFIG.exists(): print(CONFIG.read_text())
            pause()


# ── Commands ──
def cmd_search(q):
    if not api_up(): err("API khamoosh"); return
    d = api_get(f"/search?q={urllib.parse.quote(q)}&limit=15")
    if "error" in d: err(d["error"]); return
    print(f"\n{C['Cy']}Jostjo: '{q}' - {len(d)} natije{C['D']}\n")
    for i,r in enumerate(d,1):
        print(f"  {C['Dim']}{i:2d}.{C['D']} [{r['source']:14s}] {r['title'][:55]}")
        print(f"      {C['Cy']}{r['url']}{C['D']}")

def cmd_related(pkg):
    if not api_up(): err("API khamoosh"); return
    d = api_get(f"/related?pkg={urllib.parse.quote(pkg)}")
    if "error" in d: err(d["error"]); return
    print(f"\n{C['Cy']}Related: {pkg}{C['D']}  "
          f"{C['Dim']}[{d.get('category','?')}]  ({d.get('count',0)}x){C['D']}")
    hr()
    for r in d.get("related",[]):
        bar = C["G"] + "#"*min(r["weight"],25) + C["D"]
        print(f"  {r['name']:28s} {r['weight']:3d}  {bar}")
    for r in d.get("peers",[])[:10]:
        print(f"  {C['Dim']}[peer] {r['name']:22s} {r['weight']}{C['D']}")

def cmd_ask(q):
    if not api_up(): err("API khamoosh"); return
    d = api_get(f"/ask?q={urllib.parse.quote(q)}&top=3")
    if "error" in d: err(d["error"]); return
    print(f"\n{C['Cy']}Soaal: {q}{C['D']}")
    hr()
    for i,a in enumerate(d.get("answers",[]),1):
        print(f"\n{C['Bold']}[{i}] {a['title']}{C['D']}")
        print(f"   {a['text'][:400]}")
        print(f"   {C['Cy']}{a['url']}{C['D']}")
        print(f"   {C['Dim']}emtiyaz: {a['score']}{C['D']}")

def cmd_path(a,b):
    if not api_up(): err("API khamoosh"); return
    d = api_get(f"/path?a={urllib.parse.quote(a)}&b={urllib.parse.quote(b)}")
    if d.get("path"):
        print(f"\n{C['G']}Masir: " + " -> ".join(d["path"]) + C["D"] + "\n")
    else: err(f"Masiri beyn {a} va {b} nist")

def cmd_suggest(f):
    if not api_up(): err("API khamoosh"); return
    p = Path(f)
    if not p.exists(): err(f"File peyda nashod: {f}"); return
    code = p.read_text(encoding="utf-8", errors="ignore")
    d = api_post("/suggest", {"code":code})
    if "error" in d: err(d["error"]); return
    sugs = d.get("suggestions",[])
    if not sugs: warn("Pishnahadi nist"); return
    print(f"\n{C['Cy']}Pishnahad baraye {p.name}:{C['D']}\n")
    for i,s in enumerate(sugs,1):
        print(f"  {C['G']}{i:2d}. {s['pkg']:24s}{C['D']}  "
              f"{C['Dim']}(baraye {s['for']}, w={s['weight']}){C['D']}")

def show_recent(kind):
    h = load_history()
    items = h.get(kind,[])[-20:]
    if not items: warn("Tarikhche khali"); return
    print(f"\n{C['Cy']}Akhirin {kind}:{C['D']}\n")
    for i,x in enumerate(reversed(items),1):
        ts = x["ts"][:16].replace("T"," ")
        print(f"  {C['Dim']}{i:2d}.{C['D']} {x['value'][:55]}  {C['Dim']}{ts}{C['D']}")


MENUS = {
    "1":menu_explore,"2":menu_collect,"3":menu_learning,
    "4":menu_agents,"5":menu_data,"6":menu_servers,
    "7":menu_graph,"8":menu_bookmarks,"9":menu_settings,
}

def main():
    snapshot()
    while True:
        try:
            c = main_menu()
            if c in ("0","q","exit","quit","khorooj"):
                clear()
                print(f"\n{C['Cy']}Bedrood{C['D']}\n"); return
            if c in MENUS: MENUS[c]()
            elif c == "": continue
            else:
                warn("Entekhab na-motabar"); time.sleep(0.4)
        except KeyboardInterrupt:
            print(); continue
        except Exception as e:
            err(f"Khata: {e}"); pause()

if __name__ == "__main__":
    main()
