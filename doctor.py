#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""doctor.py — چک سلامت کامل پروژه"""
import os, sys, json, sqlite3, socket
from pathlib import Path
from datetime import datetime

EVO = Path.home() / "evoscanner"
HOME = Path.home()
MANIFEST = EVO / "manifest.json"

C = {
    "R":"\033[0m", "B":"\033[1m", "D":"\033[2m",
    "CY":"\033[38;2;100;220;230m", "GR":"\033[38;2;120;230;150m",
    "RD":"\033[38;2;255;110;110m", "YL":"\033[38;2;255;215;80m",
    "PU":"\033[38;2;180;140;255m", "GY":"\033[38;2;130;135;150m",
}

def ok(m):    print(f"  {C['GR']}✓{C['R']} {m}")
def err(m):   print(f"  {C['RD']}✗{C['R']} {m}")
def warn(m):  print(f"  {C['YL']}⚠{C['R']} {m}")
def info(m):  print(f"  {C['GY']}·{C['R']} {m}")

def port_free(port):
    try:
        s = socket.socket()
        s.settimeout(0.3)
        s.connect(("127.0.0.1", port))
        s.close()
        return False  # اشغال
    except:
        return True  # آزاد

def check_manifest():
    if not MANIFEST.exists():
        err("manifest.json نیست")
        return None
    try:
        m = json.loads(MANIFEST.read_text(encoding="utf-8"))
        ok(f"manifest.json — {m['name']} v{m['version']}")
        ok(f"  {len(m.get('modules',{}))} ماژول + {len(m.get('engines',{}))} موتور + {len(m.get('menu',{}))} منو")
        return m
    except Exception as e:
        err(f"manifest خرابه: {e}")
        return None

def check_modules(m):
    if not m: return
    print(f"\n  {C['PU']}ماژول‌ها:{C['R']}")
    missing = 0
    for name, info_ in m.get("modules",{}).items():
        p = EVO / info_["path"]
        if info_.get("external"):
            p = Path(info_["path"].replace("~", str(HOME)))
        if p.exists():
            size = p.stat().st_size
            ok(f"  {name:18} {size:>8,}B  {info_['path']}")
        else:
            err(f"  {name:18} گم  {info_['path']}")
            missing += 1
    return missing

def check_engines(m):
    if not m: return
    print(f"\n  {C['PU']}موتورهای مستقل:{C['R']}")
    for name, info_ in m.get("engines",{}).items():
        p = Path(info_["path"].replace("~", str(HOME)))
        if p.exists():
            ok(f"  {name:18} {p.stat().st_size:>8,}B")
        else:
            warn(f"  {name:18} گم (اختیاری)")

def check_db():
    print(f"\n  {C['PU']}دیتابیس:{C['R']}")
    for name, p in [("evoscanner", EVO/"knowledge.db"),
                    ("forge", HOME/"knowledgeforge"/"knowledge.db")]:
        if p.exists():
            try:
                c = sqlite3.connect(p)
                tables = c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
                ok(f"  {name:12} {len(tables)} جدول · {p.stat().st_size:,}B")
            except Exception as e:
                err(f"  {name:12} خراب: {e}")
        else:
            warn(f"  {name:12} نیست")

def check_ports():
    print(f"\n  {C['PU']}پورت‌ها:{C['R']}")
    for name, port in [("webui",8080),("api",8081),("graph",8082),("webapp",8090),("pqasd",8787)]:
        if port_free(port):
            ok(f"  {name:12} :{port}  آزاد")
        else:
            warn(f"  {name:12} :{port}  مشغول")

def check_backups():
    print(f"\n  {C['PU']}بکاپ‌ها:{C['R']}")
    b = EVO / "BACKUPS"
    if b.exists():
        files = list(b.glob("*.py"))
        ok(f"  {len(files)} فایل")
        latest = sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)[:3]
        for p in latest:
            t = datetime.fromtimestamp(p.stat().st_mtime)
            info(f"  {t:%m-%d %H:%M}  {p.name}")
    else:
        warn("  پوشه BACKUPS نیست")

def check_syntax():
    print(f"\n  {C['PU']}سینتکس پایتون:{C['R']}")
    errs = 0
    for p in list(EVO.glob("*.py")):
        try:
            compile(p.read_text(encoding="utf-8"), str(p), "exec")
        except SyntaxError as e:
            err(f"  {p.name}:{e.lineno} — {e.msg}")
            errs += 1
    if errs == 0:
        ok(f"  {len(list(EVO.glob('*.py')))} فایل همه سالم")
    return errs

def check_cortex():
    print(f"\n  {C['PU']}CORTEX:{C['R']}")
    mem = EVO / "cortex_memory.json"
    if mem.exists():
        try:
            d = json.loads(mem.read_text(encoding="utf-8"))
            ok(f"  {len(d.get('sessions',[]))} session · {len(d.get('skills',{}))} skill · {len(d.get('insights',[]))} insight")
        except: warn("  حافظه خراب")
    else:
        warn("  cortex_memory.json نیست")

def main():
    os.system("clear")
    print(f"\n  {C['CY']}{C['B']}╔══════════════════════════════════════════════╗")
    print(f"  ║   🏥 EvoScanner — DOCTOR                     ║")
    print(f"  ╚══════════════════════════════════════════════╝{C['R']}\n")
    print(f"  {C['GY']}{datetime.now():%Y-%m-%d %H:%M}{C['R']}\n")

    m = check_manifest()
    missing = check_modules(m)
    check_engines(m)
    check_db()
    check_ports()
    check_backups()
    errs = check_syntax()
    check_cortex()

    # خلاصه
    print()
    print(f"  {C['CY']}{C['B']}═══ خلاصه ═══{C['R']}")
    total = (missing or 0) + errs
    if total == 0:
        print(f"  {C['GR']}{C['B']}✅ همه‌چیز عالی{C['R']}")
    else:
        print(f"  {C['YL']}⚠ {total} مورد نیاز به بررسی{C['R']}")

    print()
    input("  ادامه...")

if __name__ == "__main__":
    main()
