"""Meta Agent — ایجنت خودبازنویس که ایجنت‌های جدید می‌سازد"""
import ast
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

BASE = Path.home() / "evoscanner"
META_DIR = BASE / "meta_agents"
BACKUPS = BASE / "meta_backups"
LOG = BASE / "meta_log.json"

META_DIR.mkdir(exist_ok=True)
BACKUPS.mkdir(exist_ok=True)


def load_log():
    if LOG.exists():
        try:
            return json.loads(LOG.read_text())
        except Exception:
            pass
    return {"runs": [], "agents": [], "capabilities": []}


def save_log(d):
    LOG.write_text(json.dumps(d, indent=2, ensure_ascii=False))


# ═══════════════════════════════════════════════════
# 1. SELF-READER — خواندن کد خود
# ═══════════════════════════════════════════════════

def analyze_self():
    """تحلیل کد خودِ Meta Agent"""
    me = Path(__file__)
    code = me.read_text()
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return {"error": str(e)}

    funcs = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            funcs.append({
                "name": node.name,
                "line": node.lineno,
                "length": (node.end_lineno or node.lineno) - node.lineno,
                "args": [a.arg for a in node.args.args],
            })

    return {
        "lines": code.count("\n"),
        "funcs": funcs,
        "func_count": len(funcs),
        "sha256": hashlib.sha256(code.encode()).hexdigest()[:12],
    }


# ═══════════════════════════════════════════════════
# 2. PROJECT-ANALYZER — تحلیل کامل پروژه
# ═══════════════════════════════════════════════════

def analyze_project():
    """تحلیل وضعیت کامل پروژه"""
    project = {
        "files": [],
        "total_lines": 0,
        "total_size": 0,
        "issues": [],
        "opportunities": [],
    }

    for f in sorted(BASE.glob("*.py")):
        try:
            code = f.read_text()
            lines = code.count("\n")
            project["files"].append({
                "name": f.name,
                "lines": lines,
                "size": len(code),
            })
            project["total_lines"] += lines
            project["total_size"] += len(code)

            # بررسی مشکلات
            for i, line in enumerate(code.split("\n"), 1):
                if len(line) > 140 and not line.strip().startswith("#"):
                    project["issues"].append({
                        "file": f.name,
                        "line": i,
                        "type": "long_line",
                        "detail": f"{len(line)} chars",
                    })
                    break

        except Exception:
            pass

    # فرصت‌های بهبود
    # 1. فایل‌های بدون docstring
    nodoc = sum(1 for f in project["files"]
                if f["lines"] > 100)
    if nodoc > 10:
        project["opportunities"].append({
            "type": "add_docstrings",
            "detail": f"{nodoc} فایل بزرگ بدون مستندات",
            "impact": "medium",
        })

    # 2. فایل‌های تکراری
    hashes = {}
    for f in BASE.glob("*.py"):
        try:
            h = hashlib.sha256(f.read_bytes()).hexdigest()[:12]
            hashes.setdefault(h, []).append(f.name)
        except Exception:
            pass
    dupes = {h: n for h, n in hashes.items() if len(n) > 1}
    if dupes:
        project["opportunities"].append({
            "type": "dedupe_files",
            "detail": f"{len(dupes)} گروه فایل تکراری",
            "impact": "low",
        })

    # 3. تست نبود
    has_tests = any("test" in f["name"].lower() for f in project["files"])
    if not has_tests:
        project["opportunities"].append({
            "type": "add_tests",
            "detail": "هیچ فایل تست ندارد",
            "impact": "high",
        })

    return project


# ═══════════════════════════════════════════════════
# 3. AGENT FACTORY — ساخت ایجنت جدید
# ═══════════════════════════════════════════════════

AGENT_TEMPLATES = {
    "pattern_finder": {
        "purpose": "پیدا کردن الگوهای مشترک در منابع",
        "inputs": ["db", "graph"],
        "outputs": ["patterns"],
        "logic": """
def run(kb, graph):
    # تحلیل co-occurrence
    patterns = []
    cooc = graph.get("cooc", {})
    for pair, w in sorted(cooc.items(), key=lambda x: -x[1])[:20]:
        a, b = pair.split("|", 1)
        if a.startswith("cat:") or b.startswith("cat:"):
            continue
        if w >= 3:
            patterns.append({"a": a, "b": b, "weight": w})
    return {"patterns": patterns}
""",
    },
    "gap_finder": {
        "purpose": "پیدا کردن شکاف‌های دانشی",
        "inputs": ["db", "categories"],
        "outputs": ["gaps"],
        "logic": """
def run(kb, graph):
    gaps = []
    cats = {c: n for c, n, _ in kb.categories_stats()}
    for c, n in cats.items():
        if c != "other" and n < 10:
            gaps.append({"category": c, "count": n})
    return {"gaps": gaps}
""",
    },
    "quality_ranker": {
        "purpose": "رتبه‌بندی کیفیت منابع",
        "inputs": ["db"],
        "outputs": ["ranking"],
        "logic": """
def run(kb, graph):
    rows = kb.conn.execute(
        "SELECT title, score FROM resources ORDER BY score DESC LIMIT 20"
    ).fetchall()
    return {"top": [{"title": t, "score": s} for t, s in rows]}
""",
    },
    "cross_domain_finder": {
        "purpose": "پیدا کردن ترکیب‌های بین‌دامنه‌ای",
        "inputs": ["graph"],
        "outputs": ["combinations"],
        "logic": """
def run(kb, graph):
    combos = []
    nodes = graph.get("nodes", {})
    for n, v in nodes.items():
        if v.get("type") != "entity":
            continue
        cats = list(v.get("cats", {}).keys())
        if len(cats) >= 2:
            combos.append({"entity": n, "domains": cats})
    return {"combos": combos[:20]}
""",
    },
    "temporal_analyzer": {
        "purpose": "تحلیل روند زمانی",
        "inputs": ["db"],
        "outputs": ["trends"],
        "logic": """
def run(kb, graph):
    rows = kb.conn.execute(
        "SELECT DATE(found_at) as d, COUNT(*) FROM resources "
        "GROUP BY d ORDER BY d DESC LIMIT 14"
    ).fetchall()
    return {"daily": [{"date": d, "count": c} for d, c in rows]}
""",
    },
    "code_evolver": {
        "purpose": "پیشنهاد بازنویسی کد پروژه",
        "inputs": ["files"],
        "outputs": ["suggestions"],
        "logic": """
def run(kb, graph):
    sugg = []
    for f in sorted(Path.home().joinpath("evoscanner").glob("*.py")):
        try:
            code = f.read_text()
            if code.count("\\n") > 500 and "docstring" not in code.lower():
                sugg.append({"file": f.name, "action": "add_docstrings"})
        except Exception:
            pass
    return {"suggestions": sugg}
""",
    },
}


def create_agent(name, template_key=None, custom_code=None):
    """ساخت یک ایجنت جدید"""
    if template_key and template_key in AGENT_TEMPLATES:
        t = AGENT_TEMPLATES[template_key]
        code = f'''"""Auto-generated agent: {name}"""
import json
from datetime import datetime
from pathlib import Path

BASE = Path.home() / "evoscanner"

PURPOSE = {t["purpose"]!r}
INPUTS = {t["inputs"]!r}
OUTPUTS = {t["outputs"]!r}


{t["logic"]}


def report():
    print(f"Agent: {name}")
    print(f"Purpose: {{PURPOSE}}")
    print(f"Inputs: {{INPUTS}}")
    print(f"Outputs: {{OUTPUTS}}")


if __name__ == "__main__":
    report()
'''
    elif custom_code:
        code = custom_code
    else:
        return None, "no template or code"

    agent_file = META_DIR / f"agent_{name}.py"
    agent_file.write_text(code)

    # بررسی syntax
    try:
        import py_compile
        py_compile.compile(str(agent_file), doraise=True)
    except Exception as e:
        agent_file.unlink()
        return None, str(e)[:100]

    log = load_log()
    log["agents"].append({
        "name": name,
        "file": agent_file.name,
        "template": template_key,
        "ts": datetime.now().isoformat(),
    })
    save_log(log)

    return agent_file, None


def list_agents():
    return list(META_DIR.glob("agent_*.py"))


def run_agent(name, kb):
    """اجرای یک ایجنت"""
    f = META_DIR / f"agent_{name}.py"
    if not f.exists():
        return {"error": "not found"}

    try:
        sys.path.insert(0, str(META_DIR))
        mod_name = f.stem
        if mod_name in sys.modules:
            del sys.modules[mod_name]
        mod = __import__(mod_name)

        # گراف
        graph = {}
        gfile = BASE / "graph.json"
        if gfile.exists():
            graph = json.loads(gfile.read_text())

        return mod.run(kb, graph)
    except Exception as e:
        return {"error": str(e)[:150]}


# ═══════════════════════════════════════════════════
# 4. SELF-REWRITER — بازنویسی خود
# ═══════════════════════════════════════════════════

def backup_self():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = BACKUPS / ts
    dest.mkdir(exist_ok=True)
    shutil.copy(__file__, dest / Path(__file__).name)
    return dest


def propose_improvement():
    """پیشنهاد ارتقای خود Meta Agent"""
    ana = analyze_self()
    suggestions = []

    if ana["func_count"] < 20:
        suggestions.append({
            "type": "add_capability",
            "detail": "می‌توان قابلیت‌های جدید اضافه کرد",
        })

    if ana["lines"] > 500:
        suggestions.append({
            "type": "split_file",
            "detail": "فایل خیلی بزرگ شده",
        })

    # بررسی نودهای گراف
    try:
        g = json.loads((BASE / "graph.json").read_text())
        nodes = len(g.get("nodes", {}))
        if nodes > 2000:
            suggestions.append({
                "type": "graph_sharding",
                "detail": "گراف بزرگ شده، sharding لازم است",
            })
    except Exception:
        pass

    return suggestions


def capability_scan():
    """پیش‌بینی توانایی‌های آینده"""
    from feature_capability import predict
    return predict()


# ═══════════════════════════════════════════════════
# 5. META-LOOP
# ═══════════════════════════════════════════════════

def meta_cycle(kb):
    """یک چرخه کامل Meta Agent"""
    print()
    print("=" * 60)
    print("  🤖 Meta Agent Cycle")
    print("=" * 60)
    print()

    # 1. تحلیل خود
    print("  [1/5] تحلیل خود...")
    ana = analyze_self()
    print(f"        {ana['lines']} خط، {ana['func_count']} تابع")

    # 2. تحلیل پروژه
    print("  [2/5] تحلیل پروژه...")
    proj = analyze_project()
    print(f"        {len(proj['files'])} فایل، "
          f"{proj['total_lines']:,} خط، "
          f"{len(proj['issues'])} مشکل")

    # 3. کشف فرصت
    print("  [3/5] فرصت‌های بهبود...")
    opps = proj.get("opportunities", [])
    print(f"        {len(opps)} فرصت")

    # 4. ساخت ایجنت جدید اگر لازم است
    print("  [4/5] بررسی ایجنت‌های موجود...")
    existing = list_agents()
    print(f"        {len(existing)} ایجنت")

    if len(existing) < 3:
        print("  [4/5] ساخت ایجنت جدید...")
        for name, key in [("PatternFinder", "pattern_finder"),
                           ("GapFinder", "gap_finder"),
                           ("QualityRanker", "quality_ranker")]:
            if not any(name.lower() in f.name.lower() for f in existing):
                f, err = create_agent(name, key)
                if f:
                    print(f"        ✓ {name} ساخته شد")
                else:
                    print(f"        ✗ {name}: {err}")

    # 5. پیش‌بینی توانایی
    print("  [5/5] پیش‌بینی توانایی...")
    try:
        cap = capability_scan()
        print(f"        RAM: {cap['hardware']['ram_total_mb']} MB")
        print(f"        Days to 80%: {cap['prediction']['days_to_saturation']}")
    except Exception as e:
        print(f"        ✗ {e}")

    # ثبت
    log = load_log()
    log["runs"].append({
        "ts": datetime.now().isoformat(),
        "self": ana,
        "project": {
            "files": len(proj["files"]),
            "lines": proj["total_lines"],
        },
        "opportunities": opps,
        "agents": len(list_agents()),
    })
    log["runs"] = log["runs"][-50:]
    save_log(log)

    print()
    print("  ✓ چرخه تمام شد")
    print()


def report():
    log = load_log()
    if not log["runs"]:
        print("  (خالی)")
        return

    last = log["runs"][-1]
    print()
    print("=" * 60)
    print(f"  Meta Agent Report — {last['ts'][:19]}")
    print("=" * 60)
    print()

    print(f"  Self:")
    for k, v in last["self"].items():
        if k != "funcs":
            print(f"    {k:14s} {v}")

    print(f"\n  Project:")
    for k, v in last["project"].items():
        print(f"    {k:14s} {v}")

    print(f"\n  Opportunities ({len(last.get('opportunities', []))}):")
    for o in last.get("opportunities", []):
        print(f"    • {o['type']}: {o['detail']}")

    print(f"\n  Agents ({last.get('agents', 0)}):")
    for f in list_agents():
        print(f"    • {f.name}")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(BASE))
    from evoscanner_v2 import KB
    kb = KB()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "cycle"
    if cmd == "cycle":
        meta_cycle(kb)
    elif cmd == "report":
        report()
    elif cmd == "agents":
        for f in list_agents():
            print(f"  {f.name}")
    elif cmd == "analyze":
        a = analyze_self()
        print(json.dumps(a, indent=2))
    elif cmd == "create" and len(sys.argv) > 3:
        f, err = create_agent(sys.argv[2], sys.argv[3])
        print(f.name if f else f"error: {err}")
    elif cmd == "run" and len(sys.argv) > 2:
        r = run_agent(sys.argv[2], kb)
        print(json.dumps(r, indent=2, ensure_ascii=False)[:1500])

