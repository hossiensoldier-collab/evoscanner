"""AI Bridge — ساخت پرامپت کامل برای بردن به چت AI"""
import json
import subprocess
from datetime import datetime
from pathlib import Path

BASE = Path.home() / "evoscanner"
OUT = BASE / "ai_prompts"
OUT.mkdir(exist_ok=True)
WISH = BASE / "ai_wishes.json"


def project_state():
    """وضعیت لحظه‌ای پروژه"""
    st = {
        "files": [],
        "db_resources": 0,
        "graph_nodes": 0,
        "graph_edges": 0,
        "categories": 0,
        "techniques": 0,
        "graphics_topics": 0,
        "version": "3.0.0",
    }

    # فایل‌ها
    for f in sorted(BASE.glob("*.py")):
        try:
            lines = len(f.read_text().splitlines())
            st["files"].append({"name": f.name, "lines": lines})
        except Exception:
            pass

    # نسخه
    vf = BASE / "version.txt"
    if vf.exists():
        st["version"] = vf.read_text().strip()

    # پایگاه
    try:
        import sqlite3
        db = sqlite3.connect(BASE / "knowledge.db")
        st["db_resources"] = db.execute(
            "SELECT COUNT(*) FROM resources").fetchone()[0]
        for t in ("techniques", "graphics_topics"):
            try:
                st[t] = db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            except Exception:
                pass
        try:
            st["categories"] = db.execute(
                "SELECT COUNT(DISTINCT category) FROM resources").fetchone()[0]
        except Exception:
            pass
        db.close()
    except Exception:
        pass

    # گراف
    try:
        g = json.loads((BASE / "graph.json").read_text())
        st["graph_nodes"] = sum(1 for v in g["nodes"].values()
                                 if v.get("type") == "entity")
        st["graph_edges"] = len(g.get("edges", {}))
    except Exception:
        pass

    return st


def available_commands():
    """دستورات موجود در evoscanner_v2.py"""
    try:
        txt = (BASE / "evoscanner_v2.py").read_text()
        import re
        return sorted(set(re.findall(r'cmd\s*==\s*"([^"]+)"', txt)))
    except Exception:
        return []


def build_prompt(user_wish, kind="feature"):
    """ساخت پرامپت کامل"""
    st = project_state()
    cmds = available_commands()

    files_txt = "\n".join(
        f"  - {f['name']} ({f['lines']} خط)" for f in st["files"])

    prompt = f"""سلام. من پروژه EvoScanner رو دارم توسعه میدم و این خواسته من:

┌───────────────────────────────────────────────────────────
│ {user_wish}
└───────────────────────────────────────────────────────────

## وضعیت فعلی پروژه

**نسخه:** v{st['version']}
**مسیر:** ~/evoscanner
**منابع:** {st['db_resources']} | **دسته‌ها:** {st['categories']}
**گراف:** {st['graph_nodes']} نود، {st['graph_edges']} یال
**تکنیک‌ها:** {st['techniques']} | **موضوعات گرافیک:** {st['graphics_topics']}

**فایل‌های اصلی:**
{files_txt}

**دستورات موجود در evoscanner_v2.py:**
{', '.join(cmds[:40])}

## درخواست من

لطفاً:

1. **تحلیل کوتاه** — این قابلیت چه می‌کند، چطور کار می‌کند، چه چیزی به پروژه اضافه می‌کند.

2. **کد کامل و آماده** — به شکل یک یا چند فایل پایتون که با `cat > file.py << 'PYEOF' ... PYEOF` قابل ساخت باشد.

3. **پچ اتصال** — اگر به `panel.py` یا `evoscanner_v2.py` باید دست بزند، یک اسکریپت پایتون بده که این patch را امن اعمال کند (با پشتیبان و بررسی syntax).

4. **دستور تست** — چند دستور کوتاه که بعد از اعمال، صحت را چک کند.

5. **بدون توضیح اضافی** — فقط چیزهایی که باید paste کنم و اجرا کنم.

## قیدها

- فقط کتابخانه استاندارد پایتون (Termux)
- کد در Termux/android اجرا می‌شود
- اگر می‌توانی، قابلیت به شکل ماژول جدا باشد (`feature_xxx.py`) و از پنل صدا زده شود
- در پنل، رنگ‌های موجود: C['R'], C['G'], C['Y'], C['B'], C['M'], C['Cy'], C['W'], C['D'], C['Bold'], C['Dim']
- فرمت منو: `print(f"  {{C['Y']}}[N]{{C['D']}}  Title  {{C['Dim']}}subtitle{{C['D']}}")`
- توابع dispatch: `menu_xxx()` که خودش loop دارد و با 0 برمی‌گردد

## نوع درخواست

{kind}

ممنون. آماده patch هستم.
"""

    return prompt


def save_prompt(prompt, tag="wish"):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    f = OUT / f"{tag}_{ts}.md"
    f.write_text(prompt, encoding="utf-8")
    return f


def load_wishes():
    if WISH.exists():
        try:
            return json.loads(WISH.read_text())
        except Exception:
            pass
    return []


def save_wishes(w):
    WISH.write_text(json.dumps(w, indent=2, ensure_ascii=False))


def add_wish(text, kind="feature"):
    w = load_wishes()
    w.append({
        "text": text,
        "kind": kind,
        "ts": datetime.now().isoformat(),
        "done": False,
    })
    save_wishes(w)


def mark_done(idx):
    w = load_wishes()
    if 0 <= idx < len(w):
        w[idx]["done"] = True
        save_wishes(w)
        return True
    return False


def latest_prompt_path():
    files = sorted(OUT.glob("*.md"), reverse=True)
    return files[0] if files else None


def copy_to_clipboard(text):
    """سعی می‌کند در کلیپ‌بورد کپی کند (termux-api)"""
    try:
        p = subprocess.run(["termux-clipboard-set"],
                           input=text.encode("utf-8"),
                           timeout=5)
        return p.returncode == 0
    except Exception:
        return False


def show_wishes():
    w = load_wishes()
    if not w:
        print("  (هیچ خواسته‌ای ثبت نشده)")
        return
    for i, x in enumerate(w, 1):
        mark = "[x]" if x["done"] else "[ ]"
        ts = x["ts"][:16].replace("T", " ")
        print(f"  {mark} {i:2d}. {x['text'][:60]}  ({ts})")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "state":
            print(json.dumps(project_state(), indent=2, ensure_ascii=False))
        elif sys.argv[1] == "wishes":
            show_wishes()
        elif sys.argv[1] == "make":
            wish = " ".join(sys.argv[2:])
            if wish:
                p = build_prompt(wish)
                f = save_prompt(p)
                print(f"Saved: {f}")
                print()
                print(p)

