#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""اسکن کامل پروژه‌های Termux + ساخت PROJECTS.md"""
import os, sys, json, time
from pathlib import Path
from datetime import datetime

HOME = Path.home()
SKIP = {".cache",".npm",".gradle",".cargo",".rustup",".local","node_modules",
        "__pycache__",".git","venv",".venv","env","site-packages",".termux",
        ".dart-tool",".pub-cache",".m2",".stack",".ghc",".cabal","tmp",".tmp",
        "downloads","storage","usr"}

MARKERS = {".git","requirements.txt","package.json","pyproject.toml","setup.py",
           "Cargo.toml","go.mod","pom.xml","build.gradle","Gemfile","Makefile",
           "Dockerfile","Pipfile","poetry.lock",".project"}

def human(n):
    for u in ["B","KB","MB","GB"]:
        if n<1024: return f"{n:.1f}{u}"
        n/=1024
    return f"{n:.1f}TB"

def ago(ts):
    d=time.time()-ts
    if d<60: return f"{int(d)}s"
    if d<3600: return f"{int(d/60)}m"
    if d<86400: return f"{int(d/3600)}h"
    if d<2592000: return f"{int(d/86400)}d"
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")

def main():
    projects = []
    for root, dirs, files in os.walk(HOME, topdown=True):
        rp = Path(root)
        try:
            rel = rp.relative_to(HOME)
        except ValueError:
            continue
        parts = set(rel.parts)
        if parts & SKIP or any(p.startswith(".") and p not in (".", "") for p in [rp.name] if rp.name not in (".git",)):
            dirs[:] = [d for d in dirs if d not in SKIP]
            continue
        dirs[:] = [d for d in dirs if d not in SKIP]
        try:
            entries = set(os.listdir(root))
        except Exception:
            continue
        if entries & MARKERS:
            py=c=js=0; size=0; latest=0; nfiles=0
            for f in files:
                fp = rp/f
                try: st = fp.stat()
                except Exception: continue
                size += st.st_size; nfiles += 1
                latest = max(latest, st.st_mtime)
                ext = fp.suffix.lower()
                if ext==".py": py+=1
                elif ext in (".c",".cpp",".h",".rs",".go"): c+=1
                elif ext in (".js",".ts"): js+=1
            projects.append({
                "name": rp.name, "path": str(rp),
                "rel": str(rel) if str(rel)!="." else "~",
                "py": py, "c": c, "js": js, "files": nfiles,
                "size": size, "mtime": latest,
                "markers": sorted(entries & MARKERS),
            })
    projects.sort(key=lambda p: p["mtime"], reverse=True)
    return projects

if __name__ == "__main__":
    print("\n🔍 در حال اسکن...\n")
    t0=time.time()
    ps = main()
    print(f"\n📦 {len(ps)} پروژه پیدا شد (زمان: {time.time()-t0:.1f}s)\n")
    for p in ps:
        print(f"▸ {p['name']:25} {p['rel']:45} py={p['py']:<4} files={p['files']:<5} {human(p['size']):<8} {ago(p['mtime'])}")

    # ساخت PROJECTS.md
    out = HOME/"PROJECTS.md"
    with open(out,"w",encoding="utf-8") as f:
        f.write(f"# پروژه‌های Termux\n\n")
        f.write(f"*آخرین اسکن: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n")
        f.write(f"تعداد پروژه‌ها: **{len(ps)}**\n\n")
        f.write("| پروژه | مسیر | py | files | حجم | آخرین تغییر | نشانه‌ها |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        for p in ps:
            f.write(f"| {p['name']} | `{p['rel']}` | {p['py']} | {p['files']} | {human(p['size'])} | {ago(p['mtime'])} | {', '.join(p['markers'])} |\n")
    print(f"\n✓ گزارش ذخیره شد: {out}")
