"""چهار ایجنت خودمختار: Hunter, Judge, Archivist, Critic"""
import json, random
from datetime import datetime
from pathlib import Path

BASE = Path.home() / "evoscanner"
AGENT_LOG = BASE / "agents.json"


class Hunter:
    name = "Hunter"
    MUTATORS = [
        "{} advanced", "{} 2025", "{} patterns",
        "{} internals", "{} production", "{} tutorial",
        "{} benchmark", "{} case study",
    ]

    def run(self, kb, evo, context=None):
        best = [q for q, _ in kb.best_queries(10)]
        cats = {c: n for c, n, _ in kb.categories_stats()}
        weak = [c for c, n in cats.items() if n < 5 and c != "other"]

        new_queries = []
        for q in best[:3]:
            for _ in range(2):
                new_queries.append(random.choice(self.MUTATORS).format(q))
        for c in weak:
            new_queries.append(f"python {c}")
        new_queries = list(dict.fromkeys(new_queries))[:10]

        state = evo.state
        state["active"] = list(dict.fromkeys(
            state["active"] + new_queries))[:25]
        evo._save()
        return {"new_queries": new_queries, "weak_cats": weak}


class Judge:
    name = "Judge"
    MIN_SCORE = 0.15

    def run(self, kb, evo, context=None):
        to_delete = kb.conn.execute(
            "SELECT hash, title FROM resources WHERE score < ?",
            (self.MIN_SCORE,)
        ).fetchall()
        deleted = 0
        for h, t in to_delete:
            kb.conn.execute("DELETE FROM resources WHERE hash=?", (h,))
            deleted += 1
        kb.conn.commit()

        rows = kb.conn.execute(
            "SELECT hash, title, source, score FROM resources WHERE score < 0.3"
        ).fetchall()
        low = [{"title": t, "source": s, "score": sc}
               for h, t, s, sc in rows]

        titles = {}
        for h, t in kb.conn.execute("SELECT hash, title FROM resources"):
            key = (t or "").lower()[:30]
            titles.setdefault(key, []).append(h)
        dupes = [v for v in titles.values() if len(v) > 1]

        return {"low_quality": len(low), "duplicates": len(dupes),
                "deleted": deleted, "low_list": low[:10]}


class Archivist:
    name = "Archivist"

    def run(self, kb, evo, context=None):
        n = 0
        try:
            from classifier import recategorize
            n = recategorize(kb)
        except Exception as e:
            print(f"  ! archivist reclassify: {e}")
        nodes, edges = 0, 0
        try:
            from graph import Graph
            g = Graph()
            nodes, edges = g.build_from_kb(kb)
        except Exception as e:
            print(f"  ! archivist graph: {e}")
        return {"reclassified": n, "nodes": nodes, "edges": edges}


class Critic:
    name = "Critic"

    def run(self, kb, evo, context=None):
        issues = []
        cats = {c: n for c, n, _ in kb.categories_stats()}
        for c, n in cats.items():
            if n == 0 and c != "other":
                issues.append(f"دسته خالی: {c}")

        try:
            hf = BASE / "health.json"
            if hf.exists():
                h = json.loads(hf.read_text())
                dead = [n for n, v in h.items() if v.get("fails", 0) >= 3]
                if dead:
                    issues.append(f"منابع خاموش: {', '.join(dead)}")
        except Exception:
            pass

        weak = [(c, n) for c, n in cats.items() if 0 < n < 3]
        if weak:
            issues.append(f"دسته‌های ضعیف: {', '.join(c for c, _ in weak)}")

        total = kb.total()
        if total < 200:
            issues.append(f"پایگاه کوچک: {total} منبع (هدف ۲۰۰+)")

        return {"issues": issues, "total": total, "cats": len(cats)}


class Orchestrator:
    def __init__(self):
        self.hunter = Hunter()
        self.judge = Judge()
        self.archivist = Archivist()
        self.critic = Critic()
        self.log = self._load()

    def _load(self):
        if AGENT_LOG.exists():
            try:
                return json.loads(AGENT_LOG.read_text())
            except Exception:
                pass
        return {"runs": []}

    def _save(self):
        AGENT_LOG.write_text(
            json.dumps(self.log, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    def run_cycle(self, kb, evo):
        results = {
            "hunter":    self.hunter.run(kb, evo),
            "judge":     self.judge.run(kb, evo),
            "archivist": self.archivist.run(kb, evo),
            "critic":    self.critic.run(kb, evo),
        }
        self.log["runs"].append({
            "ts": datetime.now().isoformat(),
            "results": results,
        })
        self._save()
        return results

    def report(self):
        if not self.log["runs"]:
            print("  (هیچ اجرایی ثبت نشده)")
            return
        last = self.log["runs"][-1]
        print(f"\n🎭 گزارش ایجنت‌ها — {last['ts'][:19]}\n")
        r = last["results"]

        h = r["hunter"]
        print(f"  🏹 Hunter: {len(h['new_queries'])} کوئری جدید")
        for q in h["new_queries"][:5]:
            print(f"     • {q}")

        j = r["judge"]
        print(f"\n  ⚖️  Judge: {j['low_quality']} ضعیف، "
              f"{j['duplicates']} تکراری، {j.get('deleted', 0)} حذف")

        a = r["archivist"]
        print(f"\n  📚 Archivist: {a['reclassified']} بازدسته، "
              f"{a['nodes']} نود، {a['edges']} یال")

        c = r["critic"]
        print(f"\n  🔍 Critic: {c['total']} منبع، {c['cats']} دسته")
        if c["issues"]:
            print("     مسائل:")
            for i in c["issues"]:
                print(f"     • {i}")
