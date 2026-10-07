"""Agent Chain — ایجنت‌ها که خودشان ایجنت می‌سازند"""
import json
import re
from datetime import datetime
from pathlib import Path

BASE = Path.home() / "evoscanner"
CHAIN_LOG = BASE / "agent_chain.json"
CUSTOM_AGENTS = BASE / "custom_agents.json"


def load_chain():
    if CHAIN_LOG.exists():
        try:
            return json.loads(CHAIN_LOG.read_text())
        except Exception:
            pass
    return {"runs": [], "insights": [], "created_agents": []}


def save_chain(c):
    CHAIN_LOG.write_text(json.dumps(c, indent=2, ensure_ascii=False))


def load_custom():
    if CUSTOM_AGENTS.exists():
        try:
            return json.loads(CUSTOM_AGENTS.read_text())
        except Exception:
            pass
    return {}


def save_custom(c):
    CUSTOM_AGENTS.write_text(json.dumps(c, indent=2, ensure_ascii=False))


# ─── ایجنت‌های پایه ───
class BaseAgent:
    name = "base"

    def run(self, kb, evo, ctx):
        return {}

    def observe(self, results):
        """ایجنت می‌تواند از نتایج خودش یاد بگیرد"""
        return None


class Hunter(BaseAgent):
    name = "Hunter"
    MUTATORS = ["{} advanced", "{} 2025", "{} patterns", "best {}",
                "{} production", "{} benchmark", "{} tutorial"]

    def run(self, kb, evo, ctx):
        import random
        best = [q for q, _ in kb.best_queries(10)]
        cats = {c: n for c, n, _ in kb.categories_stats()}
        weak = [c for c, n in cats.items() if n < 5 and c != "other"]

        new_q = []
        for q in best[:3]:
            for _ in range(2):
                new_q.append(random.choice(self.MUTATORS).format(q))
        for c in weak:
            new_q.append(f"python {c}")

        state = evo.state
        state["active"] = list(dict.fromkeys(
            state.get("active", []) + new_q))[:40]
        evo._save()
        return {"new_queries": new_q[:10]}


class Judge(BaseAgent):
    name = "Judge"

    def run(self, kb, evo, ctx):
        low = kb.conn.execute(
            "SELECT COUNT(*) FROM resources WHERE score < 0.05"
        ).fetchone()[0]
        return {"low_quality": low}


class Archivist(BaseAgent):
    name = "Archivist"

    def run(self, kb, evo, ctx):
        try:
            from classifier import recategorize
            recategorize(kb)
        except Exception:
            pass
        try:
            from graph import Graph
            g = Graph()
            n, e = g.build_from_kb(kb)
            return {"nodes": n, "edges": e}
        except Exception:
            return {}


class Critic(BaseAgent):
    name = "Critic"

    def run(self, kb, evo, ctx):
        issues = []
        cats = {c: n for c, n, _ in kb.categories_stats()}
        for c, n in cats.items():
            if n == 0 and c != "other":
                issues.append(f"empty: {c}")
        return {"issues": issues}


# ─── Analyst — تحلیلگر ───
class Analyst(BaseAgent):
    name = "Analyst"

    def run(self, kb, evo, ctx):
        """تحلیل الگوهای موفق/ناموفق"""
        insights = []

        # پکیج‌های پر رشد
        try:
            rows = kb.conn.execute(
                "SELECT source, COUNT(*) FROM resources "
                "GROUP BY source ORDER BY COUNT(*) DESC").fetchall()
            for src, n in rows:
                if n < 5:
                    insights.append({
                        "type": "weak_source",
                        "detail": f"{src} فقط {n} منبع",
                        "action": f"افزودن کوئری برای {src}"
                    })
        except Exception:
            pass

        # دسته‌های خالی
        cats = {c: n for c, n, _ in kb.categories_stats()}
        empty = [c for c, n in cats.items() if n == 0 and c != "other"]
        if empty:
            insights.append({
                "type": "empty_categories",
                "detail": f"{len(empty)} دسته خالی: {','.join(empty[:3])}",
                "action": "افزودن کوئری برای این دسته‌ها"
            })

        # growth rate
        try:
            h = json.loads((BASE / "evolution.json").read_text())
            hist = h.get("history", [])
            if len(hist) >= 5:
                recent = hist[-5:]
                avg = sum(x.get("active", 0) for x in recent) / len(recent)
                if avg < 10:
                    insights.append({
                        "type": "low_activity",
                        "detail": f"میانگین کوئری فعال: {avg:.1f}",
                        "action": "افزایش MUTATORS یا کوئری دستی"
                    })
        except Exception:
            pass

        return {"insights": insights}


# ─── MetaAgent — سازنده ایجنت ───
class MetaAgent(BaseAgent):
    name = "MetaAgent"

    def run(self, kb, evo, ctx):
        """از insights ایجنت جدید می‌سازد"""
        insights = ctx.get("Analyst", {}).get("insights", [])
        created = []

        existing = load_custom()

        for ins in insights:
            t = ins.get("type")
            if t == "weak_source" and "SourceBooster" not in existing:
                self._create_source_booster(kb, evo, ins)
                created.append("SourceBooster")

            elif t == "empty_categories" and "CategoryHunter" not in existing:
                self._create_category_hunter(kb, evo, ins)
                created.append("CategoryHunter")

            elif t == "low_activity" and "QueryExploder" not in existing:
                self._create_query_exploder(kb, evo, ins)
                created.append("QueryExploder")

        if created:
            log = load_chain()
            log["created_agents"].extend([
                {"name": n, "ts": datetime.now().isoformat()}
                for n in created
            ])
            save_chain(log)

        return {"created": created}

    def _create_source_booster(self, kb, evo, ins):
        """SourceBooster — روی منابع ضعیف تمرکز می‌کند"""
        agent_code = {
            "name": "SourceBooster",
            "purpose": "boosts weak sources",
            "queries": [
                "python advanced tutorial", "python expert patterns",
                "python production", "python deep dive",
            ],
            "created_at": datetime.now().isoformat(),
        }
        c = load_custom()
        c["SourceBooster"] = agent_code
        save_custom(c)

    def _create_category_hunter(self, kb, evo, ins):
        """CategoryHunter — دسته‌های خالی را پر می‌کند"""
        cats = {c: n for c, n, _ in kb.categories_stats()}
        empty = [c for c, n in cats.items() if n == 0 and c != "other"]

        c = load_custom()
        c["CategoryHunter"] = {
            "name": "CategoryHunter",
            "purpose": "fills empty categories",
            "targets": empty,
            "created_at": datetime.now().isoformat(),
        }
        save_custom(c)

        # کوئری‌ها را به صف اضافه کن
        new_q = [f"python {cat} tutorial" for cat in empty[:10]]
        state = evo.state
        state["active"] = list(dict.fromkeys(
            state.get("active", []) + new_q))[:40]
        evo._save()

    def _create_query_exploder(self, kb, evo, ins):
        """QueryExploder — کوئری‌های ترکیبی می‌سازد"""
        c = load_custom()
        c["QueryExploder"] = {
            "name": "QueryExploder",
            "purpose": "combines queries",
            "created_at": datetime.now().isoformat(),
        }
        save_custom(c)


# ─── Custom Agent Runner ───
def run_custom_agents(kb, evo):
    """ایجنت‌های ساخته‌شده را اجرا می‌کند"""
    custom = load_custom()
    results = {}
    for name, cfg in custom.items():
        if name == "SourceBooster":
            qs = cfg.get("queries", [])
            state = evo.state
            state["active"] = list(dict.fromkeys(
                state.get("active", []) + qs))[:40]
            evo._save()
            results[name] = {"added_queries": len(qs)}
        elif name == "CategoryHunter":
            targets = cfg.get("targets", [])
            qs = [f"python {t}" for t in targets]
            state = evo.state
            state["active"] = list(dict.fromkeys(
                state.get("active", []) + qs))[:40]
            evo._save()
            results[name] = {"added_queries": len(qs)}
        elif name == "QueryExploder":
            results[name] = {"info": "ready"}
    return results


# ─── Orchestrator ───
class ChainOrchestrator:
    def __init__(self):
        self.agents = [Hunter(), Judge(), Archivist(), Critic(),
                       Analyst(), MetaAgent()]

    def run(self, kb, evo):
        ctx = {}
        results = {}
        for a in self.agents:
            try:
                results[a.name] = a.run(kb, evo, ctx)
                ctx[a.name] = results[a.name]
            except Exception as e:
                results[a.name] = {"error": str(e)[:80]}

        # اجرای ایجنت‌های ساخته‌شده
        custom_results = run_custom_agents(kb, evo)
        results["custom"] = custom_results

        log = load_chain()
        log["runs"].append({
            "ts": datetime.now().isoformat(),
            "results": results,
        })
        log["runs"] = log["runs"][-50:]
        save_chain(log)

        return results

    def report(self):
        log = load_chain()
        if not log["runs"]:
            print("  (empty)")
            return
        last = log["runs"][-1]
        print(f"\n{'=' * 60}")
        print(f"  Agent Chain Report — {last['ts'][:19]}")
        print(f"{'=' * 60}\n")

        for name, res in last["results"].items():
            if name == "custom":
                if res:
                    print(f"  [custom agents]")
                    for cname, cinfo in res.items():
                        print(f"    • {cname}: {cinfo}")
                continue
            if isinstance(res, dict) and "error" in res:
                print(f"  ✗ {name}: {res['error']}")
            else:
                print(f"  ✓ {name}")
                if isinstance(res, dict):
                    for k, v in res.items():
                        if isinstance(v, list):
                            print(f"      {k}: {len(v)} مورد")
                        else:
                            print(f"      {k}: {v}")

        created = log.get("created_agents", [])
        if created:
            print(f"\n  🎯 ایجنت‌های ساخته‌شده ({len(created)}):")
            for c in created[-5:]:
                print(f"    • {c['name']} ({c['ts'][:10]})")
        print()


def show_custom_agents():
    custom = load_custom()
    if not custom:
        print("  (هیچ ایجنت سفارشی ساخته نشده)")
        return
    print(f"\n  ایجنت‌های سفارشی ({len(custom)}):\n")
    for name, cfg in custom.items():
        print(f"    {name}")
        print(f"      purpose: {cfg.get('purpose', '?')}")
        print(f"      created: {cfg.get('created_at', '?')[:19]}")
        print()


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(BASE))
    from evoscanner_v2 import KB
    from evoscanner_v2 import Evolver
    kb = KB()
    evo = Evolver(kb)
    orch = ChainOrchestrator()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"
    if cmd == "run":
        print("🎭 اجرای زنجیره ایجنت‌ها...\n")
        r = orch.run(kb, evo)
        print("✓ تمام شد")
        orch.report()
    elif cmd == "report":
        orch.report()
    elif cmd == "custom":
        show_custom_agents()

