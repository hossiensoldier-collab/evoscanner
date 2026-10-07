"""SSH Tunnel — SOCKS5 proxy on localhost:1080"""
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(__file__).parent
CFG = BASE / "tunnel.json"
PID = BASE / "tunnel.pid"
LOG = BASE / "tunnel.log"


def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")


def load_cfg():
    if CFG.exists():
        try:
            return json.loads(CFG.read_text())
        except Exception:
            pass
    return {
        "host": "",
        "user": "root",
        "port": 22,
        "local_port": 1080,
        "retries": 5,
    }


def save_cfg(cfg):
    CFG.write_text(json.dumps(cfg, indent=2))
    try:
        os.chmod(CFG, 0o600)
    except Exception:
        pass


def config():
    c = load_cfg()
    print()
    c["host"] = input(f"SSH host [{c['host']}]: ").strip() or c["host"]
    c["user"] = input(f"user [{c['user']}]: ").strip() or c["user"]
    p = input(f"SSH port [{c['port']}]: ").strip()
    if p:
        c["port"] = int(p)
    lp = input(f"local SOCKS port [{c['local_port']}]: ").strip()
    if lp:
        c["local_port"] = int(lp)
    save_cfg(c)
    print("saved")


def build_cmd(c):
    return [
        "ssh", "-N",
        "-o", "ExitOnForwardFailure=yes",
        "-o", "ServerAliveInterval=30",
        "-o", "ServerAliveCountMax=3",
        "-o", "StrictHostKeyChecking=accept-new",
        "-o", "ConnectTimeout=15",
        "-p", str(c["port"]),
        "-D", f"0.0.0.0:{c['local_port']}",
        f"{c['user']}@{c['host']}",
    ]


def is_running():
    if not PID.exists():
        return False
    try:
        pid = int(PID.read_text())
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def start():
    c = load_cfg()
    if not c["host"]:
        print("config first: python tunnel.py config")
        return

    if is_running():
        print("already running")
        return

    cmd = build_cmd(c)
    log(f"start: {' '.join(cmd[:6])}...")

    proc = subprocess.Popen(
        cmd,
        stdout=open(LOG, "a"),
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    PID.write_text(str(proc.pid))
    time.sleep(2)

    if proc.poll() is not None:
        print("failed — see tunnel.log")
        if PID.exists():
            PID.unlink()
        return

    print(f"running (PID {proc.pid})")
    print(f"socks5://127.0.0.1:{c['local_port']}")


def stop():
    if not PID.exists():
        print("not running")
        return
    try:
        pid = int(PID.read_text())
        os.kill(pid, signal.SIGTERM)
        time.sleep(1)
        PID.unlink()
        print("stopped")
    except Exception as e:
        print(f"error: {e}")
        if PID.exists():
            PID.unlink()


def status():
    if is_running():
        c = load_cfg()
        print(f"running (PID {PID.read_text().strip()})")
        print(f"socks5://127.0.0.1:{c['local_port']}")
    else:
        print("stopped")


def test():
    c = load_cfg()
    if not is_running():
        print("not running — start first")
        return
    proxy = f"socks5h://127.0.0.1:{c['local_port']}"
    try:
        r = subprocess.run(
            ["curl", "-s", "--max-time", "15", "--proxy", proxy,
             "https://api.github.com/zen"],
            capture_output=True, text=True, timeout=20)
        if r.returncode == 0 and r.stdout.strip():
            print("OK:", r.stdout.strip()[:80])
        else:
            print("FAIL:", r.stderr.strip()[:120] or "no data")
    except Exception as e:
        print(f"error: {e}")


def watch_restart():
    """ری‌استارت خودکار در پس‌زمینه"""
    c = load_cfg()
    for i in range(c.get("retries", 5)):
        if is_running():
            time.sleep(30)
            continue
        log(f"restart {i + 1}")
        start()
        time.sleep(5)
    stop()


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "config":
        config()
    elif cmd == "start":
        start()
    elif cmd == "stop":
        stop()
    elif cmd == "test":
        test()
    elif cmd == "watch":
        watch_restart()
    else:
        status()
