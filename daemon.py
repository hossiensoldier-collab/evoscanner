"""Daemon — چرخه خودکار"""
import sys, time, json, subprocess
from datetime import datetime
from pathlib import Path

BASE = Path.home() / "evoscanner"
LOG = BASE / "daemon.log"
STATE = BASE / "daemon.json"


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def run_step(name, cmd, timeout=600):
    log(f"▶ {name}")
    try:
        r = subprocess.run(
            [sys.executable, "evoscanner_v2.py"] + cmd,
            cwd=BASE, capture_output=True, text=True, timeout=timeout
        )
        if r.returncode == 0:
            log(f"✓ {name}")
            return True
        log(f"✗ {name} — exit {r.returncode}")
        return False
    except subprocess.TimeoutExpired:
        log(f"✗ {name} — timeout")
        return False
    except Exception as e:
        log(f"✗ {name} — {e}")
        return False


def one_pass():
    log("═" * 50)
    log("شروع چرخه daemon")
    run_step("reset-health",  ["reset-health"], 60)
    run_step("run-cycles",    ["run", "2"], 300)
    run_step("enrich",        ["enrich", "30"], 300)
    run_step("rebuild-graph", ["rebuild"], 120)
    run_step("learn",         ["learn"], 60)
    run_step("agents",        ["agents"], 300)
    run_step("export",        ["export"], 120)
    # هر پاس: فشرده‌سازی سبک
    run_step("compress",      ["compress"], 120)
    log("پایان چرخه")
    log("═" * 50)


def main():
    hours = 6
    once = "--once" in sys.argv
    if "--interval" in sys.argv:
        i = sys.argv.index("--interval")
        hours = int(sys.argv[i + 1])

    log(f"🚀 Daemon شروع — فاصله: {hours}h")
    try:
        one_pass()
        if once:
            log("حالت --once — خروج")
            return
        while True:
            log(f"💤 خواب {hours} ساعت...")
            time.sleep(hours * 3600)
            one_pass()
    except KeyboardInterrupt:
        log("⏸  Daemon متوقف شد")


if __name__ == "__main__":
    main()

