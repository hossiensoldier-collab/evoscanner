"""Hunter فیدبکی — یادگیری از نتایج با Upper Confidence Bound"""
import math, random, json
from pathlib import Path

BASE = Path.home() / "evoscanner"
LEARN = BASE / "learned_queries.json"


class FeedbackHunter:
    def __init__(self, kb):
        self.kb = kb
        self.stats = self._load()

    def _load(self):
        if LEARN.exists():
            try:
                return json.loads(LEARN.read_text())
            except Exception:
                pass
        # بار اول: از جدول queries
        rows = self.kb.conn.execute("""
            SELECT query, COUNT(*), SUM(new_hits), AVG(new_hits)
            FROM queries GROUP BY query
        """).fetchall()
        stats = {}
        for q, tried, total, avg in rows:
            stats[q] = {"tried": tried or 0,
                        "total": total or 0,
                        "avg": avg or 0.0}
        return stats

    def _save(self):
        LEARN.write_text(json.dumps(self.stats, indent=2, ensure_ascii=False),
                         encoding="utf-8")

    def _ucb(self, q, total_tries, c=1.5):
        s = self.stats.get(q, {"tried": 0, "avg": 0})
        if s["tried"] == 0:
            return 1e9  # ناشناخته = اولویت بالا
        exploit = s["avg"]
        explore = c * math.sqrt(math.log(max(total_tries, 2)) / s["tried"])
        return exploit + explore

    def _mutate(self, q):
        """جهش ساختاری — از الگوهای موفق"""
        patterns = [
            f"{q} advanced", f"{q} 2025", f"{q} 2026",
            f"best {q}", f"{q} patterns", f"{q} production",
            f"{q} benchmark", f"{q} internals", f"{q} case study",
            f"{q} best practices", f"{q} deep dive",
        ]
        return random.sample(patterns, 2)

    def select(self, n=6):
        """انتخاب n کوئری با UCB"""
        total = sum(s["tried"] for s in self.stats.values()) + 1

        # کاندیدها
        candidates = set(self.stats.keys())

        # جهش از ۵ بهترین
        top = sorted(self.stats.items(),
                     key=lambda x: -x[1]["avg"])[:5]
        for q, _ in top:
            candidates.update(self._mutate(q))

        # دسته‌های ضعیف از KB
        try:
            cats = {c: cnt for c, cnt, _ in self.kb.categories_stats()}
            for c, cnt in cats.items():
                if 0 < cnt < 5 and c != "other":
                    candidates.add(f"python {c}")
        except Exception:
            pass

        # UCB scoring
        scored = [(self._ucb(q, total), q) for q in candidates]
        scored.sort(reverse=True)

        # تنوع: چک کلمه دوم (نه اول چون همه python هستند)
        picked = []
        for _, q in scored:
            picked.append(q)
            if len(picked) >= n:
                break
        return picked

    def update(self, query, new_hits, avg_score=0.0):
        """بروزرسانی پس از اجرا"""
        s = self.stats.setdefault(query, {"tried": 0, "total": 0, "avg": 0.0})
        s["tried"] += 1
        s["total"] += new_hits
        # میانگین متحرک
        s["avg"] = (s["avg"] * (s["tried"] - 1) + new_hits) / s["tried"]
        self._save()

    def report(self, top_n=15):
        """پرفورمنس کوئری‌ها"""
        rows = sorted(
            self.stats.items(),
            key=lambda x: (-x[1]["avg"], -x[1]["total"])
        )[:top_n]
        print(f"\n🏆 {top_n} کوئری برتر (UCB):\n")
        print(f"  {'کوئری':40s} {'تلاش':>5s} {'جدید':>6s} {'میانگین':>8s}")
        print("  " + "─" * 62)
        for q, s in rows:
            print(f"  {q[:40]:40s} {s['tried']:5d} {s['total']:6d} {s['avg']:8.2f}")

    def weak_queries(self, min_tries=3, limit=10):
        """کوئری‌های بی‌ثمر"""
        weak = [(q, s) for q, s in self.stats.items()
                if s["tried"] >= min_tries and s["avg"] < 0.3]
        weak.sort(key=lambda x: x[1]["avg"])
        return weak[:limit]

