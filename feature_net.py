"""Network manager — test providers, proxy, SSH tunnel, WARP"""
import json
import os
import socket
import subprocess
import ssl
import time
import urllib.request
from pathlib import Path

BASE = Path.home() / "evoscanner"
CFG = BASE / ".agent.json"
NET_CFG = BASE / ".net.json"

# پرووایدرها
PROVIDERS = {
    "groq":       {"host": "api.groq.com",       "url": "https://api.groq.com/openai/v1/models"},
    "openrouter": {"host": "openrouter.ai",      "url": "https://openrouter.ai/api/v1/models"},
    "together":   {"host": "api.together.xyz",   "url": "https://api.together.xyz/v1/models"},
    "deepinfra":  {"host": "api.deepinfra.com",  "url": "https://api.deepinfra.com/v1/models"},
    "mistral":    {"host": "api.mistral.ai",     "url": "https://api.mistral.ai/v1/models"},
    "openai":     {"host": "api.openai.com",     "url": "https://api.openai.com/v1/models"},
}

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE


def load_net():
    if NET_CFG.exists():
        try:
            return json.loads(NET_CFG.read_text())
        except Exception:
            pass
    return {"proxy": "", "ssh": {}}


def save_net(cfg):
    NET_CFG.write_text(json.dumps(cfg, indent=2))
    try:
        os.chmod(NET_CFG, 0o600)
    except Exception:
        pass


# ─── تست اتصال ───

def test_provider(name, timeout=8):
    """تست یک provider"""
    p = PROVIDERS.get(name)
    if not p:
        return {"ok": False, "err": "provider unknown"}

    # ۱. تست DNS
    try:
        ip = socket.gethostbyname(p["host"])
    except Exception as e:
        return {"ok": False, "err": f"DNS fail: {e}"}

    # ۲. تست HTTPS
    try:
        req = urllib.request.Request(p["url"], headers={
            "User-Agent": "EvoScanner/3.0",
        })
        # اگر پروکسی ست است
        net = load_net()
        if net.get("proxy"):
            handler = urllib.request.ProxyHandler({
                "https": net["proxy"],
                "http": net["proxy"],
            })
            opener = urllib.request.build_opener(handler)
            urllib.request.install_opener(opener)

        t0 = time.time()
        with urllib.request.urlopen(req, timeout=timeout,
                                    context=SSL_CTX) as r:
            elapsed = time.time() - t0
            return {
                "ok": True,
                "ip": ip,
                "status": r.status,
                "ms": int(elapsed * 1000),
            }
    except urllib.error.HTTPError as e:
        # 401/403 یعنی اتصال کار می‌کند ولی نیاز به auth
        return {
            "ok": True,
            "ip": ip,
            "status": e.code,
            "note": "auth needed but reachable",
        }
    except Exception as e:
        return {"ok": False, "ip": ip, "err": str(e)[:80]}


def test_all(timeout=6):
    """تست همه providerها"""
    results = {}
    for name in PROVIDERS:
        results[name] = test_provider(name, timeout=timeout)
    return results


def best_provider(timeout=6):
    """بهترین provider در دسترس"""
    results = test_all(timeout=timeout)
    ok = [(n, r) for n, r in results.items() if r.get("ok")]
    if not ok:
        return None, results
    # مرتب بر اساس زمان پاسخ
    ok.sort(key=lambda x: x[1].get("ms", 9999))
    return ok[0][0], results


# ─── مدیر پروکسی ───

def set_proxy(url):
    """ذخیره پروکسی در .net.json + env"""
    cfg = load_net()
    cfg["proxy"] = url
    save_net(cfg)
    if url:
        os.environ["HTTPS_PROXY"] = url
        os.environ["HTTP_PROXY"] = url
    else:
        os.environ.pop("HTTPS_PROXY", None)
        os.environ.pop("HTTP_PROXY", None)
    return True


def get_proxy():
    return load_net().get("proxy", "")


# ─── SSH Tunnel ───

def ssh_tunnel_add(name, host, user, local_port, remote_port,
                   ssh_port=22):
    """ثبت تونل SSH"""
    cfg = load_net()
    cfg.setdefault("ssh", {})
    cfg["ssh"][name] = {
        "host": host, "user": user,
        "local_port": local_port,
        "remote_port": remote_port,
        "ssh_port": ssh_port,
    }
    save_net(cfg)
    return True


def ssh_tunnel_start(name):
    """شروع تونل SSH در پس‌زمینه"""
    cfg = load_net()
    t = cfg.get("ssh", {}).get(name)
    if not t:
        return False, "tunnel not found"

    cmd = [
        "ssh", "-N",
        "-o", "ExitOnForwardFailure=yes",
        "-o", "ServerAliveInterval=30",
        "-o", "StrictHostKeyChecking=no",
        "-p", str(t["ssh_port"]),
        "-L", f"{t['local_port']}:127.0.0.1:{t['remote_port']}",
        f"{t['user']}@{t['host']}",
    ]
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        cfg["ssh"][name]["pid"] = proc.pid
        save_net(cfg)
        return True, f"PID {proc.pid} on :{t['local_port']}"
    except Exception as e:
        return False, str(e)


def ssh_tunnel_stop(name):
    cfg = load_net()
    t = cfg.get("ssh", {}).get(name)
    if not t or "pid" not in t:
        return False, "no pid"
    try:
        os.kill(t["pid"], 15)
        del t["pid"]
        save_net(cfg)
        return True, "stopped"
    except Exception as e:
        return False, str(e)


# ─── WARP helper ───

def warp_status():
    """وضعیت WARP"""
    try:
        r = subprocess.run(
            ["warp-cli", "status"],
            capture_output=True, text=True, timeout=5)
        return r.stdout.strip() or r.stderr.strip()
    except FileNotFoundError:
        return "not installed"
    except Exception as e:
        return str(e)


def warp_install_hint():
    return (
        "pkg install cloudflare-warp\n"
        "warp-cli register\n"
        "warp-cli connect\n"
        "warp-cli status"
    )


# ─── UI ───

def report():
    """گزارش کامل وضعیت شبکه"""
    print()
    print("=" * 60)
    print("  گزارش شبکه EvoScanner")
    print("=" * 60)
    print()

    # پروکسی
    proxy = get_proxy()
    if proxy:
        print(f"  پروکسی فعلی: {proxy}")
    else:
        print(f"  پروکسی: (تنظیم نشده)")
    print()

    # تست providerها
    print("  تست providerها:")
    results = test_all(timeout=6)
    for name, r in results.items():
        if r.get("ok"):
            ms = r.get("ms", "?")
            print(f"    [OK] {name:12s}  {ms}ms")
        else:
            err = r.get("err", "?")[:40]
            print(f"    [XX] {name:12s}  {err}")
    print()

    # بهترین
    best, _ = best_provider(timeout=6)
    if best:
        print(f"  بهترین provider: {best}")
    else:
        print("  هیچ provider در دسترس نیست")
        print("  راه‌حل: پروکسی یا WARP")
    print()

    # SSH
    cfg = load_net()
    tunnels = cfg.get("ssh", {})
    if tunnels:
        print("  تونل‌های SSH:")
        for name, t in tunnels.items():
            status = "فعال" if "pid" in t else "غیرفعال"
            print(f"    {name}: {t['user']}@{t['host']} "
                  f"→ :{t['local_port']}  [{status}]")
        print()


def auto_configure():
    """تنظیم خودکار بهترین provider در .agent.json"""
    best, results = best_provider(timeout=6)
    if not best:
        print()
        print("  ✗ هیچ provider در دسترس نیست")
        print("  راه‌حل: proxy یا WARP")
        print()
        return False

    if CFG.exists():
        try:
            cfg = json.loads(CFG.read_text())
        except Exception:
            cfg = {}
    else:
        cfg = {}

    old = cfg.get("provider", "?")
    cfg["provider"] = best
    CFG.write_text(json.dumps(cfg, indent=2))
    try:
        os.chmod(CFG, 0o600)
    except Exception:
        pass

    print()
    print(f"  ✓ provider تغییر یافت: {old} → {best}")
    print()
    return True


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"
    if cmd == "report":
        report()
    elif cmd == "test":
        for name, r in test_all().items():
            status = "OK" if r.get("ok") else "FAIL"
            print(f"{status:6s} {name:12s} {r.get('err', '')[:60]}")
    elif cmd == "auto":
        auto_configure()
    elif cmd == "best":
        b, _ = best_provider()
        print(b or "none")
    elif cmd == "proxy":
        url = sys.argv[2] if len(sys.argv) > 2 else ""
        set_proxy(url)
        print(f"proxy = {url or '(cleared)'}")

