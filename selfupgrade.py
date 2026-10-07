"""Self-Upgrade Engine — تحلیل، پیشنهاد، اعمال با rollback"""
import ast
import json
import py_compile
import re
import shutil
from datetime import datetime
from pathlib import Path

DIR = Path(__file__).parent
TARGET = DIR / "panel.py"
BACKUP_DIR = DIR / "upgrade_backups"
BACKUP_DIR.mkdir(exist_ok=True)
LOG = DIR / "upgrade_history.json"
VERSION_FILE = DIR / "version.txt"


def load_version():
    if VERSION_FILE.exists():
        return VERSION_FILE.read_text().strip()
    return "3.0.0"


def save_version(v):
    VERSION_FILE.write_text(v)


def bump_version(v, kind="patch"):
    parts = v.split(".")
    while len(parts) < 3:
        parts.append("0")
    major, minor, patch = map(int, parts[:3])
    if kind == "major": return f"{major+1}.0.0"
    if kind == "minor": return f"{major}.{minor+1}.0"
    return f"{major}.{minor}.{patch+1}"


def load_history():
    if LOG.exists():
        try: return json.loads(LOG.read_text())
        except Exception: return []
    return []


def save_history(h):
    LOG.write_text(json.dumps(h, indent=2, ensure_ascii=False))


class Analyzer:
    def __init__(self, path=TARGET):
        self.path = path
        self.code = path.read_text(encoding="utf-8")
        self.lines = self.code.split("\n")

    def analyze(self):
        try:
            tree = ast.parse(self.code)
        except SyntaxError as e:
            return {"error": str(e), "line": e.lineno}

        funcs = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                funcs.append({
                    "name": node.name,
                    "line": node.lineno,
                    "length": (node.end_lineno or node.lineno) - node.lineno,
                    "doc": bool(ast.get_docstring(node)),
                })

        imports = list(dict.fromkeys(
            re.findall(r"^(?:import|from)\s+(\S+)", self.code, re.M)))

        return {
            "total_lines": len(self.lines),
            "code_lines": sum(1 for l in self.lines
                              if l.strip() and not l.strip().startswith("#")),
            "blank_lines": sum(1 for l in self.lines if not l.strip()),
            "comment_lines": sum(1 for l in self.lines
                                  if l.strip().startswith("#")),
            "functions": funcs,
            "func_count": len(funcs),
            "avg_func_len": sum(f["length"] for f in funcs) / max(len(funcs), 1),
            "imports": imports,
            "issues": self._issues(funcs, imports),
        }

    def _issues(self, funcs, imports):
        issues = []
        # توابع بلند
        for f in sorted(funcs, key=lambda x: -x["length"])[:3]:
            if f["length"] > 100:
                issues.append({
                    "type": "long_func",
                    "msg": f"تابع بلند: {f['name']} ({f['length']} خط)",
                })
        # بدون docstring
        nodoc = [f for f in funcs if not f["doc"]]
        if len(nodoc) > 5:
            issues.append({
                "type": "no_docs",
                "msg": f"{len(nodoc)} تابع بدون docstring",
            })
        # خطوط بلند
        long_l = sum(1 for l in self.lines
                     if len(l) > 120 and not l.strip().startswith("#"))
        if long_l > 15:
            issues.append({
                "type": "long_lines",
                "msg": f"{long_l} خط بیش از 120 کاراکتر",
            })
        # خطوط خالی متوالی
        max_blank = 0
        cur = 0
        for l in self.lines:
            if not l.strip():
                cur += 1
                max_blank = max(max_blank, cur)
            else:
                cur = 0
        if max_blank > 3:
            issues.append({
                "type": "blank_lines",
                "msg": f"{max_blank} خط خالی متوالی (بهترین: 2)",
            })
        # import تکراری
        import re as _re
        all_imports = _re.findall(r"^(?:import|from)\s+(\S+)", self.code, _re.M)
        dupes = [i for i in set(all_imports) if all_imports.count(i) > 1]
        if dupes:
            issues.append({
                "type": "dup_import",
                "msg": f"import تکراری: {', '.join(dupes[:3])}",
            })
        return issues


# ── پشتیبان و تأیید ──
def backup_target():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:22]
    backup = BACKUP_DIR / f"panel_{ts}.py"
    shutil.copy(TARGET, backup)
    return backup


def verify_syntax():
    try:
        py_compile.compile(str(TARGET), doraise=True)
        return True, None
    except py_compile.PyCompileError as e:
        return False, str(e)


def safe_apply(description, mutate_fn):
    """اعمال امن با پشتیبان و rollback خودکار"""
    code_before = TARGET.read_text(encoding="utf-8")
    backup = backup_target()
    try:
        code_after = mutate_fn(code_before)
    except Exception as e:
        return False, f"خطا در mutation: {e}"
    if code_after == code_before:
        return False, "تغییری ایجاد نشد"
    TARGET.write_text(code_after, encoding="utf-8")
    ok, err = verify_syntax()
    if not ok:
        shutil.copy(backup, TARGET)
        return False, f"خطای نحوی، بازگشت انجام شد: {err[:80]}"
    h = load_history()
    h.append({
        "ts": datetime.now().isoformat(),
        "description": description,
        "backup": backup.name,
        "delta_lines": len(code_after.split("\n")) - len(code_before.split("\n")),
        "version": load_version(),
    })
    save_history(h)
    return True, f"با موفقیت اعمال شد (پشتیبان: {backup.name})"


# ── ارتقاهای موجود ──
def up_header():
    def mutate(code):
        v = load_version()
        lines = code.split("\n")
        lines = [l for l in lines if not l.startswith("# EvoScanner Panel v")]
        marker = f"# EvoScanner Panel v{v}"
        insert_at = 0
        for i, l in enumerate(lines):
            if l.startswith("#!"):
                insert_at = i + 1
                continue
            if l.strip().startswith('"""') or l.strip().startswith("'''"):
                # بعد از docstring بگذار
                end_quote = l.strip()[0:3]
                for j in range(i+1, len(lines)):
                    if end_quote in lines[j]:
                        insert_at = j + 1
                        break
                break
            insert_at = i
            break
        lines.insert(insert_at, marker)
        return "\n".join(lines)
    return safe_apply("به‌روزرسانی هدر نسخه", mutate)


def up_docstrings():
    def mutate(code):
        targets = {
            "def clear():":   '    """Clear terminal screen."""',
            "def hr(w=62):":  '    """Print horizontal separator line."""',
            "def ok(t):":     '    """Print success message."""',
            "def warn(t):":   '    """Print warning message."""',
            "def err(t):":    '    """Print error message."""',
            "def info(t):":   '    """Print info message."""',
            "def pause(msg=": None,  # skip
        }
        lines = code.split("\n")
        out = []
        i = 0
        while i < len(lines):
            line = lines[i]
            out.append(line)
            key = line.strip()
            if key in targets and targets[key]:
                # چک کن خط بعدی docstring نیست
                if i + 1 < len(lines):
                    nxt = lines[i+1].strip()
                    if not (nxt.startswith('"""') or nxt.startswith("'''")):
                        if nxt and not nxt.startswith("def "):
                            out.append(targets[key])
            i += 1
        return "\n".join(out)
    return safe_apply("افزودن docstring به توابع کمکی", mutate)


def up_compress_blanks():
    def mutate(code):
        lines = code.split("\n")
        out, blanks = [], 0
        for line in lines:
            if not line.strip():
                blanks += 1
                if blanks <= 2:
                    out.append(line)
            else:
                blanks = 0
                out.append(line)
        return "\n".join(out)
    return safe_apply("فشرده‌سازی خطوط خالی تکراری", mutate)


def up_dedup_imports():
    def mutate(code):
        lines = code.split("\n")
        seen_imports = set()
        out = []
        for line in lines:
            s = line.strip()
            if (s.startswith("import ") or s.startswith("from ")) and \
               line == line.lstrip():  # فقط top-level
                if s in seen_imports:
                    continue
                seen_imports.add(s)
            out.append(line)
        return "\n".join(out)
    return safe_apply("حذف importهای تکراری", mutate)


def up_strip_trailing_ws():
    def mutate(code):
        return "\n".join(l.rstrip() for l in code.split("\n"))
    return safe_apply("حذف فاصله‌های انتهای خطوط", mutate)


def up_missing_imports():
    def mutate(code):
        needed = []
        if "json." in code and "import json" not in code:
            needed.append("import json")
        if "os." in code and "import os" not in code:
            needed.append("import os")
        if "sys." in code and "import sys" not in code:
            needed.append("import sys")
        if "time." in code and "import time" not in code:
            needed.append("import time")
        if "subprocess." in code and "import subprocess" not in code:
            needed.append("import subprocess")
        if not needed:
            return code
        lines = code.split("\n")
        for i, l in enumerate(lines):
            if l.startswith("import ") or l.startswith("from "):
                for imp in reversed(needed):
                    lines.insert(i, imp)
                break
        return "\n".join(lines)
    return safe_apply("افزودن importهای پایه گم‌شده", mutate)


AVAILABLE = [
    ("1", "hdr", "به‌روزرسانی هدر نسخه", up_header),
    ("2", "doc", "افزودن docstring", up_docstrings),
    ("3", "cmp", "فشرده‌سازی خطوط خالی", up_compress_blanks),
    ("4", "imp", "افزودن importهای گم‌شده", up_missing_imports),
    ("5", "dup", "حذف importهای تکراری", up_dedup_imports),
    ("6", "ws",  "حذف فاصله‌های انتهای خطوط", up_strip_trailing_ws),
]


def rollback_last():
    """بازگشت به آخرین پشتیبان"""
    h = load_history()
    if not h:
        return False, "تاریخچه خالی است"
    last = h[-1]
    backup = BACKUP_DIR / last["backup"]
    if not backup.exists():
        return False, f"پشتیبان پیدا نشد: {backup.name}"
    shutil.copy(backup, TARGET)
    ok, err = verify_syntax()
    if not ok:
        return False, f"خطای نحوی در پشتیبان: {err[:80]}"
    h.pop()
    save_history(h)
    return True, f"بازگشت انجام شد: {last['description']}"


def rollback_by_index(idx):
    """بازگشت به پشتیبان خاص (1-based از آخر)"""
    h = load_history()
    if not h or idx < 1 or idx > len(h):
        return False, "اندیس نامعتبر"
    entry = h[-idx]
    backup = BACKUP_DIR / entry["backup"]
    if not backup.exists():
        return False, f"پشتیبان پیدا نشد: {backup.name}"
    shutil.copy(backup, TARGET)
    ok, err = verify_syntax()
    if not ok:
        return False, f"خطای نحوی: {err[:80]}"
    # حذف رکوردهای بعد از این
    del h[-(idx):]
    save_history(h)
    return True, f"بازگشت: {entry['description']}"


def list_backups():
    files = sorted(BACKUP_DIR.glob("panel_*.py"), reverse=True)
    return files[:30]

