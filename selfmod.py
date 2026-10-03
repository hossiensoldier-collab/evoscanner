"""خودتکاملی: کد خود را تحلیل و بهبود می‌کند"""
import ast
import re
from datetime import datetime
from pathlib import Path

BASE = Path.home() / "evoscanner"
LOG = BASE / "selfmod.json"


class SelfMod:
    def __init__(self, target="evoscanner_v2.py"):
        self.target = BASE / target
        self.log = self._load_log()

    def _load_log(self):
        if LOG.exists():
            try:
                return __import__("json").loads(LOG.read_text())
            except Exception:
                pass
        return {"changes": [], "analyses": []}

    def _save_log(self):
        LOG.write_text(
            __import__("json").dumps(self.log, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    def _read(self):
        return self.target.read_text(encoding="utf-8")

    def analyze(self):
        """تحلیل استاتیک کد خود"""
        code = self._read()
        issues = []

        # ۱. خطوط بلند
        for i, line in enumerate(code.split("\n"), 1):
            if len(line) > 100 and not line.lstrip().startswith("#"):
                issues.append({
                    "type": "long_line",
                    "line": i,
                    "detail": f"طول {len(line)} کاراکتر",
                })

        # ۲. TODO/FIXME
        for i, line in enumerate(code.split("\n"), 1):
            if "TODO" in line or "FIXME" in line:
                issues.append({
                    "type": "todo",
                    "line": i,
                    "detail": line.strip()[:80],
                })

        # ۳. توابع بلند
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    length = node.end_lineno - node.lineno
                    if length > 50:
                        issues.append({
                            "type": "long_function",
                            "line": node.lineno,
                            "detail": f"{node.name}: {length} خط",
                        })
        except SyntaxError as e:
            issues.append({
                "type": "syntax_error",
                "line": e.lineno or 0,
                "detail": str(e),
            })

        # ۴. importهای تکراری
        imports = re.findall(r"^(?:import|from)\s+(\S+)", code, re.M)
        seen = {}
        for imp in imports:
            seen[imp] = seen.get(imp, 0) + 1
        for imp, n in seen.items():
            if n > 1:
                issues.append({
                    "type": "dup_import",
                    "line": 0,
                    "detail": f"{imp} × {n}",
                })

        self.log["analyses"].append({
            "ts": datetime.now().isoformat(),
            "issues_count": len(issues),
        })
        self._save_log()
        return issues

    def report(self):
        """چاپ گزارش تحلیل"""
        issues = self.analyze()
        if not issues:
            print("✅ کد تمیز است — مشکلی یافت نشد")
            return issues

        print(f"\n🔬 تحلیل کد — {len(issues)} مورد:\n")
        groups = {}
        for it in issues:
            groups.setdefault(it["type"], []).append(it)

        names = {
            "long_line": "خطوط بلند",
            "todo": "TODO/FIXME",
            "long_function": "توابع بلند",
            "dup_import": "import تکراری",
            "syntax_error": "خطای نحوی",
        }
        for typ, items in groups.items():
            print(f"  ── {names.get(typ, typ)} ({len(items)}) ──")
            for it in items[:10]:
                line = f"خط {it['line']}: " if it['line'] else ""
                print(f"    • {line}{it['detail']}")
            print()
        return issues

    def propose_queries(self, kb):
        """پیشنهاد اصلاح GAP_QUERIES بر اساس شکاف‌های واقعی"""
        cats = dict((c, n) for c, n, _ in kb.categories_stats())
        try:
            from suggest import GAP_QUERIES
        except ImportError:
            print("  ! suggest.py یافت نشد")
            return None

        missing_cats = [c for c in cats if c not in GAP_QUERIES and c != "other"]
        empty_in_gap = [c for c in GAP_QUERIES if c not in cats]

        print("\n🔧 پیشنهاد اصلاح GAP_QUERIES:\n")
        if missing_cats:
            print(f"  ! این دسته‌ها در GAP_QUERIES نیستند: {missing_cats}")
        if empty_in_gap:
            print(f"  ! این دسته‌ها در GAP_QUERIES هستند ولی خالی: {empty_in_gap}")
        if not missing_cats and not empty_in_gap:
            print("  ✓ GAP_QUERIES با دسته‌های فعلی همخوان است")
        return {"missing": missing_cats, "empty": empty_in_gap}

    def optimize_health(self):
        """پیشنهاد اصلاح آستانه Health"""
        try:
            import json
            hf = BASE / "health.json"
            if not hf.exists():
                print("  ! health.json نیست")
                return
            data = json.loads(hf.read_text())
            dead = [n for n, v in data.items() if v.get("fails", 0) >= 3]
            if dead:
                print(f"\n💤 منابع خاموش: {', '.join(dead)}")
                print(f"  پیشنهاد: اگر شبکه پایدار است، "
                      f"`reset-health` بزن")
        except Exception as e:
            print(f"  ! خطا: {e}")

    def safe_replace(self, old, new, desc=""):
        """جایگزینی امن با پشتیبان"""
        code = self._read()
        if old not in code:
            print(f"  ✗ الگو یافت نشد: {desc}")
            return False

        backup = self.target.with_suffix(
            ".py." + datetime.now().strftime("%Y%m%d_%H%M%S") + ".bak"
        )
        backup.write_text(code, encoding="utf-8")

        new_code = code.replace(old, new, 1)
        try:
            compile(new_code, str(self.target), "exec")
        except SyntaxError as e:
            print(f"  ✗ خطای نحوی، لغو: {e}")
            return False

        self.target.write_text(new_code, encoding="utf-8")
        self.log["changes"].append({
            "ts": datetime.now().isoformat(),
            "desc": desc,
            "backup": str(backup),
        })
        self._save_log()
        print(f"  ✓ اعمال شد: {desc}")
        print(f"    پشتیبان: {backup.name}")
        return True

    def rollback(self):
        """بازگردانی آخرین تغییر"""
        changes = self.log.get("changes", [])
        if not changes:
            print("  ! تغییری ثبت نشده")
            return False
        last = changes[-1]
        backup = Path(last["backup"])
        if not backup.exists():
            print(f"  ! پشتیبان نیست: {backup}")
            return False
        self.target.write_text(backup.read_text(), encoding="utf-8")
        self.log["changes"].pop()
        self._save_log()
        print(f"  ✓ بازگشت: {last['desc']}")
        return True

    def history(self):
        changes = self.log.get("changes", [])
        if not changes:
            print("  (خالی)")
            return
        print(f"\n📜 {len(changes)} تغییر:\n")
        for i, c in enumerate(changes, 1):
            print(f"  {i}. [{c['ts'][:16]}] {c['desc']}")
            print(f"     پشتیبان: {Path(c['backup']).name}")
