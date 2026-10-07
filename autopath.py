"""مسیر یادگیری خودکار ۴ سطحی"""
from pathlib import Path
from pathlib import Path


def path(kb, topic):
    print(f"\n🎯 مسیر یادگیری: {topic}")
    print("─" * 55)

    levels = [
        ("مبتدی",   [topic, f"{topic} tutorial", f"{topic} basics",
                     f"{topic} intro", f"python {topic}"]),
        ("متوسط",   [f"{topic} advanced", f"{topic} patterns",
                     f"{topic} best practices"]),
        ("پیشرفته", [f"{topic} internals", f"{topic} performance",
                     f"{topic} production"]),
        ("پژوهش",   [f"{topic} research", f"{topic} paper",
                     f"{topic} state of the art", f"{topic} benchmark"]),
    ]

    total = 0
    missing = []
    for level, queries in levels:
        found = []
        for q in queries:
            found.extend(kb.search(q, 5))
        seen = set(); uniq = []
        for src_, title, url, score in found:
            if url not in seen:
                seen.add(url); uniq.append((src_, title, url, score))
        print(f"\n  ◆ {level} — {len(uniq)} منبع")
        if not uniq:
            missing.append(level)
            print("    (خالی — نیاز به جمع‌آوری)")
        for src_, title, url, score in uniq[:3]:
            total += 1
            print(f"    • [{src_:14s}] {title[:55]}")
            print(f"      {url}")

    EN = {"مبتدی": "tutorial", "متوسط": "intermediate",
          "پیشرفته": "advanced", "پژوهش": "research"}
    if missing:
        print(f"\n  💡 سطوح خالی: {', '.join(missing)}")
        print(f"  کوئری پیشنهادی برای چرخه بعدی:")
        import json as _json
        sugg = []
        for level in missing:
            q = f"{topic} {EN.get(level, level)}"
            print(f"    • {q}")
            sugg.append(q)
        # ذخیره در evolution
        evo_file = Path.home() / "evoscanner" / "evolution.json"
        if evo_file.exists() and sugg:
            try:
                state = _json.loads(evo_file.read_text())
                state["active"] = list(dict.fromkeys(
                    state["active"] + sugg))[:25]
                evo_file.write_text(_json.dumps(state, indent=2))
                print(f"  ✓ به لیست فعال اضافه شد")
            except Exception:
                pass

    print(f"\n  جمع: {total} منبع مرتبط")
    return total

