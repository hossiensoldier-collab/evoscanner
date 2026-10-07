#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""plugin_system.py — کشف و مدیریت plugin ها
هر plugin یه فایل با PLUGIN = {...} هست.
"""
import importlib.util, json, sys
from pathlib import Path

EVO = Path.home() / "evoscanner"
PLUGIN_DIRS = [EVO, EVO / "features", EVO / "plugins"]

def discover():
    """همه‌ی plugin های موجود رو پیدا کن"""
    plugins = []
    seen = set()
    for d in PLUGIN_DIRS:
        if not d.exists():
            continue
        for f in d.glob("*.py"):
            if f.name.startswith("_"):
                continue
            if f.stem in seen:
                continue
            try:
                spec = importlib.util.spec_from_file_location(f.stem, f)
                mod = importlib.util.module_from_spec(spec)
                # فقط متادیتا رو بخون، اجرا نکن
                src = f.read_text(encoding="utf-8")
                if "PLUGIN" not in src:
                    continue
                spec.loader.exec_module(mod)
                meta = getattr(mod, "PLUGIN", None)
                if meta and isinstance(meta, dict):
                    meta["path"] = str(f)
                    meta["module_name"] = f.stem
                    plugins.append(meta)
                    seen.add(f.stem)
            except Exception as e:
                # plugin خرابه، رد کن
                pass
    return plugins

def list_plugins():
    """چاپ لیست plugin ها"""
    plugins = discover()
    if not plugins:
        print("  هیچ plugin ای پیدا نشد")
        return
    print(f"\n  {len(plugins)} plugin پیدا شد:\n")
    for p in plugins:
        num = p.get("menu", "?")
        name = p.get("name", p["module_name"])
        desc = p.get("description", "")
        print(f"  [{num:>2}] {name:15} {desc}")
    print()

def make_template(name, menu_num, description, handler="main"):
    """یه قالب plugin جدید بساز"""
    tmpl = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""{name} — {description}"""

PLUGIN = {{
    "name": "{name}",
    "menu": {menu_num},
    "description": "{description}",
    "handler": "{handler}",
    "version": "1.0",
}}

def {handler}():
    print("\\n  {name} در حال اجراست...\\n")
    # کد اینجا
    input("  ادامه...")

if __name__ == "__main__":
    {handler}()
'''
    out = EVO / "plugins"
    out.mkdir(exist_ok=True)
    path = out / f"{name.lower()}.py"
    path.write_text(tmpl, encoding="utf-8")
    return path

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["list", "new", "check"])
    ap.add_argument("--name", "-n", default="myplugin")
    ap.add_argument("--menu", "-m", type=int, default=99)
    ap.add_argument("--desc", "-d", default="توضیح کوتاه")
    args = ap.parse_args()

    if args.cmd == "list":
        list_plugins()
    elif args.cmd == "new":
        p = make_template(args.name, args.menu, args.desc)
        print(f"✓ ساخته شد: {p}")
    elif args.cmd == "check":
        plugins = discover()
        print(f"✓ {len(plugins)} plugin سالم")
