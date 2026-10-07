#!/usr/bin/env python3
import shutil
from pathlib import Path
from datetime import datetime

EVO = Path.home() / "evoscanner"
BACKUPS = EVO / "BACKUPS"
BACKUPS.mkdir(exist_ok=True)
PANEL = EVO / "panel.py"

def check():
    try:
        compile(PANEL.read_text(encoding="utf-8"), str(PANEL), "exec")
        return True, None
    except SyntaxError as e:
        return False, e

def run():
    if not PANEL.exists():
        print("panel.py نیست"); return
    ok, err = check()
    if ok:
        print("  ✓ پنل سالمه")
        return
    print(f"  ⚠ خطا: {err.msg} (خط {err.lineno})")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = BACKUPS / f"panel.py.{ts}.prerun"
    shutil.copy2(PANEL, bak)
    print(f"  ✓ بکاپ: {bak.name}")

if __name__ == "__main__":
    run()
