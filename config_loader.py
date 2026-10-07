#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""config_loader.py — خواندن config.yaml بدون نیاز به کتابخانه"""
import re
from pathlib import Path

CONFIG_FILE = Path(__file__).parent / "config.yaml"

def _parse_simple_yaml(text):
    """پارسر ساده YAML برای ساختار flat"""
    result = {}
    section = None
    for line in text.splitlines():
        # حذف کامنت
        if "#" in line:
            line = line[:line.index("#")]
        line = line.rstrip()
        if not line.strip():
            continue
        # section (بدون indent)
        if not line.startswith(" ") and line.endswith(":"):
            section = line[:-1].strip()
            result[section] = {}
            continue
        # key: value (با indent)
        m = re.match(r'^\s+(\w+):\s*(.*)$', line)
        if m and section:
            k, v = m.group(1), m.group(2).strip()
            # نوع
            if v.lower() in ("true","false"):
                v = v.lower() == "true"
            elif v.startswith('"') and v.endswith('"'):
                v = v[1:-1]
            elif v.startswith("'") and v.endswith("'"):
                v = v[1:-1]
            else:
                try: v = int(v)
                except ValueError:
                    try: v = float(v)
                    except ValueError: pass
            # جایگزینی ~
            if isinstance(v, str) and v.startswith("~"):
                v = str(Path.home()) + v[1:]
            result[section][k] = v
    return result

def load():
    if not CONFIG_FILE.exists():
        return {}
    try:
        return _parse_simple_yaml(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"⚠ config load error: {e}")
        return {}

def get(section, key, default=None):
    cfg = load()
    return cfg.get(section, {}).get(key, default)

if __name__ == "__main__":
    import json
    print(json.dumps(load(), indent=2, ensure_ascii=False))
