"""Project Cleanup & Health — آرشیو فایل‌های مرده"""
import hashlib
import re
import shutil
from datetime import datetime
from pathlib import Path

BASE = Path.home() / "evoscanner"
ARCHIVE = BASE / "archive"

ONESHOT_PATTERNS = [
    r"^fix_.*\.py$",
    r"^migrate_.*\.py$",
    r"^apply_patch_.*\.sh$",
    r".*\.bak$",
    r".*\.py\.bak.*$",
    r".*\.py\.old$",
    r"_good\.py$",
    r"_works\.py$",
    r"_backup\.py$",
    r"panel_\d+\.py$",
]


def _hash(path):
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()[:12]
    except Exception:
        return None


def scan():
    info = {
        "main": [],
        "features": [],
        "duplicates": {},
        "obsolete": [],
        "total_kb": 0,
    }

    for f in BASE.glob("*.py"):
        try:
            data = f.read_bytes()
            info["main"].append({
                "name": f.name,
                "size": len(data),
                "lines": data.decode("utf-8", errors="ignore").count("\n"),
            })
            info["total_kb"] += len(data) // 1024
            h = _hash(f)
            if h:
                info["duplicates"].setdefault(h, []).append(f.name)
        except Exception:
            pass

    feat = BASE / "features"
    if feat.exists():
        for f in feat.glob("*.py"):
            try:
                data = f.read_bytes()
                info["features"].append({
                    "name": f"features/{f.name}",
                    "size": len(data),
                    "lines": data.decode("utf-8", errors="ignore").count("\n"),
                })
            except Exception:
                pass

    info["duplicates"] = {
        h: n for h, n in info["duplicates"].items() if len(n) > 1
    }

    for f in BASE.glob("*.py"):
        for pat in ONESHOT_PATTERNS:
            if re.match(pat, f.name):
                info["obsolete"].append(f.name)
                break

    return info


def health_report():
    info = scan()
    print()
    print("=" * 65)
    print("  گزارش سلامت پروژه EvoScanner")
    print("=" * 65)
    print()

    total_main = sum(f["size"] for f in info["main"])
    total_feat = sum(f["size"] for f in info["features"])
    print(f"  فایل‌های اصلی:  {len(info['main']):3d}   {total_main // 1024} KB")
    print(f"  features/:      {len(info['features']):3d}   {total_feat // 1024} KB")
    print(f"  جمع:            {len(info['main']) + len(info['features']):3d}   "
          f"{(total_main + total_feat) // 1024} KB")
    print()

    if info["obsolete"]:
        ob_kb = sum((BASE / n).stat().st_size
                    for n in info["obsolete"]
                    if (BASE / n).exists()) // 1024
        print(f"  {len(info['obsolete'])} فایل یک‌بارمصرف ({ob_kb} KB):")
        for n in info["obsolete"][:25]:
            print(f"      - {n}")
        if len(info["obsolete"]) > 25:
            print(f"      ... +{len(info['obsolete']) - 25}")
        print()

    if info["duplicates"]:
        print(f"  {len(info['duplicates'])} گروه فایل تکراری:")
        for h, names in list(info["duplicates"].items())[:8]:
            print(f"      {h}: {', '.join(names)}")
        print()
    else:
        print("  ✓ فایل تکراری نیست")
        print()

    big = sorted(info["main"] + info["features"],
                 key=lambda x: -x["size"])[:8]
    print("  بزرگ‌ترین فایل‌ها:")
    for f in big:
        print(f"      {f['name']:<32s} "
              f"{f['lines']:>5d} خط  "
              f"{f['size'] // 1024:>4d} KB")
    print()

    return info


def archive_obsolete(dry_run=True):
    info = scan()
    if not info["obsolete"]:
        print("\n  چیزی برای آرشیو نیست\n")
        return []

    ARCHIVE.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = ARCHIVE / f"cleanup_{ts}"
    if not dry_run:
        dest.mkdir(exist_ok=True)

    moved = []
    for name in info["obsolete"]:
        src = BASE / name
        if not src.exists():
            continue
        if dry_run:
            print(f"  [dry] {name}")
            moved.append(name)
        else:
            try:
                shutil.move(str(src), str(dest / name))
                moved.append(name)
                print(f"  OK  {name}")
            except Exception as e:
                print(f"  ERR {name}: {e}")

    if not dry_run and moved:
        (dest / "README.txt").write_text(
            f"Archive: {ts}\nCount: {len(moved)}\n"
            f"Restore: python feature_cleanup.py restore {dest.name}\n"
        )

    print()
    if dry_run:
        print(f"  ({len(moved)} فایل — dry-run)")
    else:
        print(f"  {len(moved)} فایل به {dest.name} منتقل شد")
    print()
    return moved


def restore(archive_name):
    src = ARCHIVE / archive_name
    if not src.exists():
        print(f"  پیدا نشد: {src}")
        return 0
    n = 0
    for f in src.glob("*.py"):
        try:
            target = BASE / f.name
            if target.exists():
                print(f"  skip {f.name} (موجود است)")
                continue
            shutil.move(str(f), str(target))
            n += 1
        except Exception as e:
            print(f"  ERR {f.name}: {e}")
    print(f"  {n} فایل بازگردانی شد")
    return n


def list_archives():
    if not ARCHIVE.exists():
        print("\n  (آرشیو خالی)\n")
        return
    print()
    print("  آرشیوها:")
    for d in sorted(ARCHIVE.iterdir(), reverse=True):
        if d.is_dir():
            n = len(list(d.glob("*.py")))
            print(f"      {d.name}  ({n} فایل)")
    print()


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"
    if cmd == "report":
        health_report()
    elif cmd == "dry":
        archive_obsolete(dry_run=True)
    elif cmd == "archive":
        archive_obsolete(dry_run=False)
    elif cmd == "restore" and len(sys.argv) > 2:
        restore(sys.argv[2])
    elif cmd == "list":
        list_archives()

