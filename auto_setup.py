"""Auto Setup — یک دستور، همه چیز خودکار"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = Path.home() / "evoscanner"
KEYS_DIR = BASE / "ssh_keys"
HOSTS_FILE = BASE / ".ssh_hosts.json"
WORKER_FILE = BASE / ".worker.json"
AGENT_CFG = BASE / ".agent.json"

KEYS_DIR.mkdir(exist_ok=True)

C = {
    "R": "\033[0;31m", "G": "\033[0;32m", "Y": "\033[1;33m",
    "B": "\033[0;34m", "M": "\033[0;35m", "Cy": "\033[0;36m",
    "W": "\033[1;37m", "D": "\033[0m",
    "Bold": "\033[1m", "Dim": "\033[2m",
}


def clear():
    os.system("clear")


def title(t):
    print()
    print(C["Cy"] + "=" * 60 + C["D"])
    print(C["Bold"] + C["W"] + f"  {t}" + C["D"])
    print(C["Cy"] + "=" * 60 + C["D"])
    print()


def step(n, total, t):
    print()
    print(f"{C["M"]}[{n}/{total}]{C["D"]} {C["Bold"]}{t}{C["D"]}")
    print(C["Dim"] + "-" * 55 + C["D"])


def ok(t):   print(f"  {C['G']}✓{C['D']} {t}")
def warn(t): print(f"  {C['Y']}!{C['D']} {t}")
def err(t):  print(f"  {C['R']}✗{C['D']} {t}")
def info(t): print(f"  {C['B']}i{C['D']} {t}")


def ask(p, default=""):
    try:
        s = input(f"{C['Bold']}  > {C['D']}{p}"
                  + (f" [{default}]" if default else "") + ": ").strip()
        return s or default
    except (EOFError, KeyboardInterrupt):
        return ""


def wait(prompt="Enter..."):
    try:
        input(f"\n{C['Dim']}  {prompt}{C['D']}")
    except (EOFError, KeyboardInterrupt):
        pass


# ═══════════════════════════════════════════════════
#  فاز ۱: تشخیص محیط
# ═══════════════════════════════════════════════════

def phase_detect():
    step(1, 7, "تشخیص محیط")

    checks = {
        "python": shutil.which("python"),
        "ssh": shutil.which("ssh"),
        "ssh-keygen": shutil.which("ssh-keygen"),
        "curl": shutil.which("curl"),
        "termux-open-url": shutil.which("termux-open-url"),
    }

    for name, path in checks.items():
        if path:
            ok(f"{name}: {path}")
        else:
            warn(f"{name}: نیست")

    if not checks["ssh-keygen"]:
        err("ssh-keygen لازم است. نصب: pkg install openssh")
        return False
    return True


# ═══════════════════════════════════════════════════
#  فاز ۲: تولید کلید SSH (خودکار)
# ═══════════════════════════════════════════════════

def phase_gen_key():
    step(2, 7, "تولید کلید SSH (خودکار)")

    key_name = "evoscanner"
    priv = KEYS_DIR / key_name
    pub = KEYS_DIR / f"{key_name}.pub"

    if priv.exists():
        ok(f"کلید از قبل هست: {priv}")
        return key_name

    try:
        r = subprocess.run(
            ["ssh-keygen", "-t", "ed25519",
             "-f", str(priv), "-N", "", "-C", "evoscanner-auto"],
            capture_output=True, text=True, timeout=15)
        if r.returncode != 0:
            err(f"خطا: {r.stderr[:80]}")
            return None
        os.chmod(priv, 0o600)
        ok(f"private: {priv}")
        ok(f"public:  {pub}")
        print()
        print(f"  {C['Dim']}کلید عمومی (برای کپی به سرور):{C['D']}")
        print()
        print(C["Y"] + pub.read_text().strip() + C["D"])
        print()
        return key_name
    except Exception as e:
        err(str(e))
        return None


# ═══════════════════════════════════════════════════
#  فاز ۳: انتخاب سرویس ابری
# ═══════════════════════════════════════════════════

PROVIDERS = {
    "1": {
        "key": "oracle",
        "name": "Oracle Cloud Free",
        "url": "https://www.oracle.com/cloud/free/",
        "signup": "https://signup.cloud.oracle.com/",
        "spec": "4 ARM + 24GB RAM + 200GB — مادام‌العمر رایگان",
        "email_ok": True,
        "needs_ip": True,
    },
    "2": {
        "key": "codespaces",
        "name": "GitHub Codespaces",
        "url": "https://github.com/codespaces",
        "signup": "https://github.com/signup",
        "spec": "2 هسته + 8GB — ۶۰ ساعت/ماه",
        "email_ok": True,
        "needs_ip": False,
        "ssh_format": "codespace@<name>.github.dev",
    },
    "3": {
        "key": "gcloud",
        "name": "Google Cloud Shell",
        "url": "https://shell.cloud.google.com",
        "signup": "https://accounts.google.com/signup",
        "spec": "1 هسته + 1.7GB — ۵۰ ساعت/هفته",
        "email_ok": True,
        "needs_ip": False,
        "browser_only": True,
    },
    "4": {
        "key": "flyio",
        "name": "Fly.io",
        "url": "https://fly.io",
        "signup": "https://fly.io/app/sign-up",
        "spec": "۳ ماشین کوچک — رایگان",
        "email_ok": True,
        "needs_ip": True,
    },
    "5": {
        "key": "railway",
        "name": "Railway",
        "url": "https://railway.app",
        "signup": "https://railway.app/login",
        "spec": "۵ دلار اعتبار/ماه",
        "email_ok": True,
        "needs_ip": True,
    },
}


def open_url(url):
    """باز کردن URL در مرورگر گوشی"""
    try:
        if shutil.which("termux-open-url"):
            subprocess.run(["termux-open-url", url], timeout=5)
            return True
    except Exception:
        pass
    return False


def phase_choose_provider():
    step(3, 7, "انتخاب سرویس ابری")
    print()
    print(f"  {C['Dim']}یک سرویس انتخاب کن. پیشنهاد: [1] Oracle{C['D']}")
    print()

    for k, p in PROVIDERS.items():
        print(f"  {C['Y']}[{k}]{C['D']} {C['W']}{p['name']:25s}{C['D']} "
              f"{C['Dim']}{p['spec']}{C['D']}")
    print()

    choice = ask("انتخاب", "1")
    if choice not in PROVIDERS:
        err("نامعتبر")
        return None
    return PROVIDERS[choice]


# ═══════════════════════════════════════════════════
#  فاز ۴: راهنمای ثبت‌نام + باز کردن مرورگر
# ═══════════════════════════════════════════════════

def phase_signup(provider):
    step(4, 7, f"ثبت‌نام در {provider['name']}")

    print()
    print(f"  {C['Bold']}مراحل:{C['D']}")
    print()
    print(f"  1. مرورگر باز می‌شود → با ایمیل واقعی ثبت‌نام کن")
    print(f"  2. ایمیل تأیید را چک کن")
    print(f"  3. اگر کارت خواست، اضافه کن (شارژ نمی‌شود)")
    print(f"  4. یک VM / Instance بساز")
    print(f"  5. وقتی آماده شد، برگرد اینجا")
    print()

    if provider.get("browser_only"):
        print(f"  {C['Y']}این سرویس فقط از مرورگر کار می‌کند{C['D']}")
        print(f"  {C['Y']}در همان صفحه ترمینال می‌گیری{C['D']}")
        print()

    if ask("مرورگر باز شود؟ (b/n)", "b").lower() in ("b", "y", "بله"):
        if open_url(provider["signup"]):
            ok(f"مرورگر باز شد: {provider['signup']}")
        else:
            info(f"مرورگر باز نشد. دستی برو: {provider['signup']}")

    print()
    print(f"  {C['Dim']}وقتی ثبت‌نام تمام شد، Enter بزن{C['D']}")
    wait("Enter برای ادامه...")

    return True


# ═══════════════════════════════════════════════════
#  فاز ۵: دریافت اطلاعات سرور (خودکار)
# ═══════════════════════════════════════════════════

def phase_get_server(provider, key_name):
    step(5, 7, "دریافت اطلاعات سرور")

    print()
    print(f"  {C['Dim']}از کنسول سرویس، این‌ها را بگیر:{C['D']}")
    print()

    if provider.get("needs_ip"):
        print(f"  1. IP عمومی سرور")
        print(f"  2. نام کاربری (معمولاً root یا ubuntu)")
    else:
        print(f"  1. آدرس SSH (فرمت: {provider.get('ssh_format', '?')})")
        print(f"  2. نام کاربری")

    print()
    print(f"  {C['Dim']}اگر نداری، Enter خالی بزن تا بپرم{C['D']}")
    print()

    host = ask("Host (IP یا دامنه)")
    if not host:
        warn("رد شد — بعداً می‌توانی اضافه کنی")
        return None

    user = ask("User", "root")
    port = ask("Port", "22")

    # ذخیره
    hosts = {}
    if HOSTS_FILE.exists():
        try:
            hosts = json.loads(HOSTS_FILE.read_text())
        except Exception:
            pass

    alias = provider["key"]
    hosts[alias] = {
        "host": host,
        "user": user,
        "port": int(port) if port else 22,
        "key": key_name,
    }
    HOSTS_FILE.write_text(json.dumps(hosts, indent=2))
    try:
        os.chmod(HOSTS_FILE, 0o600)
    except Exception:
        pass

    ok(f"ذخیره شد: {alias} → {user}@{host}:{port}")
    return alias


# ═══════════════════════════════════════════════════
#  فاز ۶: تست اتصال
# ═══════════════════════════════════════════════════

def test_host(alias):
    if not HOSTS_FILE.exists():
        return {"ok": False, "err": "no hosts"}
    try:
        hosts = json.loads(HOSTS_FILE.read_text())
    except Exception:
        return {"ok": False, "err": "load fail"}

    h = hosts.get(alias)
    if not h:
        return {"ok": False, "err": "not found"}

    cmd = ["ssh",
           "-o", "BatchMode=yes",
           "-o", "ConnectTimeout=10",
           "-o", "StrictHostKeyChecking=accept-new",
           "-p", str(h["port"])]

    key_file = KEYS_DIR / h["key"] if h.get("key") else None
    if key_file and key_file.exists():
        cmd += ["-i", str(key_file)]

    cmd += [f"{h['user']}@{h['host']}", "echo OK"]

    try:
        t0 = time.time()
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=20)
        ms = int((time.time() - t0) * 1000)
        if r.returncode == 0 and "OK" in r.stdout:
            return {"ok": True, "ms": ms}
        return {"ok": False, "err": (r.stderr or "no OK")[:120]}
    except subprocess.TimeoutExpired:
        return {"ok": False, "err": "timeout"}
    except Exception as e:
        return {"ok": False, "err": str(e)[:120]}


def phase_test(alias):
    step(6, 7, "تست اتصال")

    if not alias:
        warn("سروری برای تست نیست")
        return False

    print()
    print(f"  {C['Dim']}اتصال به {alias}...{C['D']}")
    print()

    r = test_host(alias)
    if r.get("ok"):
        ok(f"اتصال موفق — {r['ms']}ms")
        return True
    else:
        err(f"اتصال ناموفق: {r.get('err', '?')}")
        print()
        print(f"  {C['Dim']}راه‌حل‌ها:{C['D']}")
        print(f"    • اگر پیام permission denied: کلید عمومی را به سرور اضافه کن")
        print(f"    • اگر timeout: IP یا پورت را چک کن")
        print(f"    • اگر host key error: ssh-keygen -R {alias}")
        return False


# ═══════════════════════════════════════════════════
#  فاز ۷: راه‌اندازی تونل + اتصال به AI
# ═══════════════════════════════════════════════════

def phase_tunnel(alias, working):
    step(7, 7, "راه‌اندازی تونل + اتصال به AI")

    if not working:
        warn("تونل راه نیفتاد — بعداً از [21] استفاده کن")
        return False

    print()
    print(f"  {C['Dim']}راه‌اندازی SOCKS5 proxy روی 127.0.0.1:1080{C['D']}")
    print()

    try:
        hosts = json.loads(HOSTS_FILE.read_text())
    except Exception:
        hosts = {}
    h = hosts.get(alias, {})

    # ساخت tunnel.json برای tunnel.py
    tunnel_cfg = {
        "host": h.get("host", ""),
        "user": h.get("user", "root"),
        "port": int(h.get("port", 22)),
        "local_port": 1080,
        "retries": 5,
    }
    tf = BASE / "server" / "tunnel.json"
    tf.parent.mkdir(exist_ok=True)
    tf.write_text(json.dumps(tunnel_cfg, indent=2))
    ok(f"tunnel.json ذخیره شد")

    # راه‌اندازی تونل
    info("راه‌اندازی تونل...")
    try:
        r = subprocess.run(
            [sys.executable, "tunnel.py", "start"],
            cwd=str(BASE / "server"),
            capture_output=True, text=True, timeout=15)
        if "running" in r.stdout or "PID" in r.stdout:
            ok("تونل فعال شد")
            print()
            print(f"  {C['Dim']}تست اتصال از طریق تونل...{C['D']}")
            time.sleep(3)
            r2 = subprocess.run(
                ["curl", "-s", "--max-time", "15",
                 "--proxy", "socks5h://127.0.0.1:1080",
                 "https://api.github.com/zen"],
                capture_output=True, text=True, timeout=20)
            if r2.returncode == 0 and r2.stdout.strip():
                ok(f"تست موفق: {r2.stdout.strip()[:50]}")
                # تنظیم ai_agent برای استفاده از تونل
                if AGENT_CFG.exists():
                    try:
                        cfg = json.loads(AGENT_CFG.read_text())
                        cfg["ssh_tunnel"] = True
                        cfg["socks_proxy"] = "socks5://127.0.0.1:1080"
                        AGENT_CFG.write_text(json.dumps(cfg, indent=2))
                        ok("ai_agent به تونل وصل شد")
                    except Exception:
                        pass
            else:
                warn(f"تست ناموفق: {(r2.stderr or 'no data')[:60]}")
        else:
            err(f"تونل راه نیفتاد: {r.stdout[-100:]}")
    except Exception as e:
        err(str(e)[:80])

    return True


# ═══════════════════════════════════════════════════
#  اجرای اصلی
# ═══════════════════════════════════════════════════

def main():
    clear()
    print()
    print(C["Cy"] + "  ╔" + "═" * 56 + "╗" + C["D"])
    print(C["Cy"] + "  ║" + C["D"] + C["Bold"] + C["W"]
          + "  EvoScanner — Auto Server Setup  ".center(56) + C["D"]
          + C["Cy"] + "║" + C["D"])
    print(C["Cy"] + "  ╚" + "═" * 56 + "╝" + C["D"])
    print()
    print(f"  {C['Dim']}این اسکریپت همه مراحل را خودکار می‌کند.{C['D']}")
    print(f"  {C['Dim']}فقط ثبت‌نام را خودت انجام می‌دهی (امن).{C['D']}")
    print()
    wait("Enter برای شروع...")

    if not phase_detect():
        return

    key_name = phase_gen_key()
    if not key_name:
        return

    print()
    wait("Enter برای انتخاب سرویس...")

    provider = phase_choose_provider()
    if not provider:
        return

    phase_signup(provider)

    alias = phase_get_server(provider, key_name)
    if not alias:
        warn("بدون سرور. بعداً می‌توانی از [22] اضافه کنی")
        print()
        print(f"  {C['Dim']}کلید عمومی برای افزودن دستی به سرور:{C['D']}")
        p = KEYS_DIR / f"{key_name}.pub"
        if p.exists():
            print()
            print(C["Y"] + p.read_text().strip() + C["D"])
        return

    working = phase_test(alias)

    if working:
        phase_tunnel(alias, working)

    # خلاصه
    clear()
    title("✓ پایان راه‌اندازی")
    print(f"  {C['G']}همه مراحل انجام شد{C['D']}")
    print()
    print(f"  {C['Dim']}استفاده از این به بعد:{C['D']}")
    print()
    print(f"    {C['Cy']}python panel.py{C['D']}")
    print(f"    {C['Dim']}→ [22] Server Hub → مدیریت سرورها{C['D']}")
    print(f"    {C['Dim']}→ [21] Server & Tunnel → تونل SOCKS{C['D']}")
    print(f"    {C['Dim']}→ [14] AI Agent → چت با LLM{C['D']}")
    print()
    print(f"  {C['Dim']}کلید SSH:{C['D']}  {KEYS_DIR / key_name}")
    print(f"  {C['Dim']}سرورها:{C['D']}   {HOSTS_FILE}")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n  {C['Y']}لغو شد{C['D']}\n")
        sys.exit(1)

