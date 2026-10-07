"""Server Hub — 4-in-1: cloud guide, ssh keys, hosts, worker"""
import json
import os
import shutil
import ssl
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = Path.home() / "evoscanner"
SSH_DIR = Path.home() / ".ssh"
KEYS_DIR = BASE / "ssh_keys"
HOSTS_FILE = BASE / ".ssh_hosts.json"
WORKER_FILE = BASE / ".worker.json"

KEYS_DIR.mkdir(exist_ok=True)

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE


# ═══════════════════════════════════════════════════
# 1. CLOUD PROVIDERS — راهنمای ثبت‌نام
# ═══════════════════════════════════════════════════

PROVIDERS = {
    "oracle": {
        "name": "Oracle Cloud Free",
        "url": "https://www.oracle.com/cloud/free/",
        "signup_url": "https://signup.cloud.oracle.com/",
        "spec": "4 ARM cores + 24GB RAM + 200GB disk — forever free",
        "steps": [
            "Sign up with real email (Gmail/iCloud works)",
            "Verify email",
            "Add payment method (credit/debit — $1 hold, refunded)",
            "Wait 5-15 min for account activation",
            "Login to cloud.oracle.com",
            "Menu → Compute → Instances → Create Instance",
            "Image: Ubuntu 22.04, Shape: VM.Standard.A1.Flex",
            "Set 4 OCPU + 24GB RAM (max free)",
            "Download SSH private key (keep it safe)",
            "Get public IP from instance details",
        ],
        "after": "ssh -i key.pem ubuntu@<IP>",
    },
    "codespaces": {
        "name": "GitHub Codespaces",
        "url": "https://github.com/codespaces",
        "signup_url": "https://github.com/signup",
        "spec": "2 cores + 8GB RAM — 60 hours/month free",
        "steps": [
            "Sign up to GitHub (any email)",
            "Verify email",
            "Go to github.com/codespaces",
            "Click 'New codespace'",
            "Choose a blank repo or create one",
            "Wait 30-60 seconds",
            "Open terminal inside Codespace",
            "Your SSH: ssh codespace@<name>.github.dev",
        ],
        "after": "gh codespace ssh  # or use gh CLI",
    },
    "gcloud": {
        "name": "Google Cloud Shell",
        "url": "https://shell.cloud.google.com",
        "signup_url": "https://accounts.google.com/signup",
        "spec": "1 core + 1.7GB — 50 hours/week free",
        "steps": [
            "Sign up with Google account",
            "Go to shell.cloud.google.com",
            "Accept terms",
            "Terminal opens — no card needed",
            "Persistent 5GB home directory",
        ],
        "after": "In browser: shell.cloud.google.com",
    },
    "flyio": {
        "name": "Fly.io",
        "url": "https://fly.io",
        "signup_url": "https://fly.io/app/sign-up",
        "spec": "3 small VMs free (shared CPU, 256MB each)",
        "steps": [
            "Sign up with GitHub or email",
            "Verify email",
            "Add card (mandatory, no charge under free tier)",
            "Install flyctl",
            "fly launch",
        ],
        "after": "fly ssh console",
    },
    "railway": {
        "name": "Railway",
        "url": "https://railway.app",
        "signup_url": "https://railway.app/login",
        "spec": "$5 free credit/month",
        "steps": [
            "Login with GitHub",
            "Approve authorization",
            "New project → deploy from repo",
            "Add SSH via service",
        ],
        "after": "railway connect",
    },
}


def provider_info(key):
    p = PROVIDERS.get(key)
    if not p:
        return None
    print()
    print("=" * 60)
    print(f"  {p['name']}")
    print("=" * 60)
    print()
    print(f"  URL:    {p['url']}")
    print(f"  Signup: {p['signup_url']}")
    print(f"  Spec:   {p['spec']}")
    print()
    print("  مراحل:")
    for i, step in enumerate(p["steps"], 1):
        print(f"    {i:2d}. {step}")
    print()
    print(f"  بعد از راه‌اندازی:")
    print(f"    {p['after']}")
    print()


def list_providers():
    print()
    print("  سرویس‌های رایگان:")
    print()
    for k, p in PROVIDERS.items():
        print(f"    [{k:12s}] {p['name']:25s} {p['spec'][:35]}")
    print()


# ═══════════════════════════════════════════════════
# 2. SSH KEY MANAGER
# ═══════════════════════════════════════════════════

def gen_key(name="evoscanner", key_type="ed25519"):
    if not name:
        return None, "name required"
    priv = KEYS_DIR / name
    pub = KEYS_DIR / f"{name}.pub"
    if priv.exists():
        return None, "key already exists"
    try:
        r = subprocess.run(
            ["ssh-keygen", "-t", key_type, "-f", str(priv),
             "-N", "", "-C", f"evoscanner-{name}"],
            capture_output=True, text=True, timeout=15)
        if r.returncode != 0:
            return None, r.stderr[:100]
        os.chmod(priv, 0o600)
        return {"name": name, "priv": str(priv), "pub": str(pub)}, None
    except Exception as e:
        return None, str(e)


def list_keys():
    out = []
    for f in sorted(KEYS_DIR.iterdir()):
        if f.suffix == ".pub":
            continue
        pub = f.with_suffix(".pub")
        out.append({
            "name": f.name,
            "has_pub": pub.exists(),
            "size": f.stat().st_size,
        })
    return out


def show_pub(name):
    pub = KEYS_DIR / f"{name}.pub"
    if not pub.exists():
        return None
    return pub.read_text().strip()


def delete_key(name):
    priv = KEYS_DIR / name
    pub = KEYS_DIR / f"{name}.pub"
    n = 0
    for f in (priv, pub):
        if f.exists():
            f.unlink()
            n += 1
    return n


# ═══════════════════════════════════════════════════
# 3. SSH HOSTS MANAGER
# ═══════════════════════════════════════════════════

def load_hosts():
    if HOSTS_FILE.exists():
        try:
            return json.loads(HOSTS_FILE.read_text())
        except Exception:
            pass
    return {}


def save_hosts(d):
    HOSTS_FILE.write_text(json.dumps(d, indent=2))
    try:
        os.chmod(HOSTS_FILE, 0o600)
    except Exception:
        pass


def add_host(alias, host, user, port=22, key_name=None):
    hosts = load_hosts()
    hosts[alias] = {
        "host": host, "user": user, "port": int(port),
        "key": key_name or "",
    }
    save_hosts(hosts)
    return True


def remove_host(alias):
    hosts = load_hosts()
    if alias in hosts:
        del hosts[alias]
        save_hosts(hosts)
        return True
    return False


def test_host(alias, timeout=15):
    hosts = load_hosts()
    h = hosts.get(alias)
    if not h:
        return {"ok": False, "err": "not found"}

    cmd = ["ssh",
           "-o", "BatchMode=yes",
           "-o", "ConnectTimeout=8",
           "-o", "StrictHostKeyChecking=accept-new",
           "-p", str(h["port"])]
    if h.get("key"):
        key_path = KEYS_DIR / h["key"]
        if key_path.exists():
            cmd += ["-i", str(key_path)]
    cmd += [f"{h['user']}@{h['host']}", "echo OK"]

    t0 = time.time()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=timeout)
        elapsed = int((time.time() - t0) * 1000)
        if r.returncode == 0 and "OK" in r.stdout:
            return {"ok": True, "ms": elapsed}
        return {"ok": False, "err": (r.stderr or "no OK")[:80]}
    except subprocess.TimeoutExpired:
        return {"ok": False, "err": "timeout"}
    except Exception as e:
        return {"ok": False, "err": str(e)[:80]}


def test_all_hosts():
    out = {}
    for alias in load_hosts():
        out[alias] = test_host(alias)
    return out


def best_host():
    results = test_all_hosts()
    ok = [(a, r) for a, r in results.items() if r.get("ok")]
    if not ok:
        return None, results
    ok.sort(key=lambda x: x[1].get("ms", 9999))
    return ok[0][0], results


# ═══════════════════════════════════════════════════
# 4. CLOUDFLARE WORKER HELPER
# ═══════════════════════════════════════════════════

WORKER_CODE = '''export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const upstream = "https://openrouter.ai" + url.pathname + url.search;
    const headers = new Headers(request.headers);
    headers.set("Host", "openrouter.ai");
    headers.set("Origin", "https://openrouter.ai");
    headers.set("Referer", "https://openrouter.ai/");

    let body = null;
    if (request.method !== "GET" && request.method !== "HEAD") {
      body = await request.arrayBuffer();
    }

    const req = new Request(upstream, {
      method: request.method,
      headers: headers,
      body: body,
    });

    const resp = await fetch(req);
    const newHeaders = new Headers(resp.headers);
    newHeaders.set("Access-Control-Allow-Origin", "*");
    newHeaders.set("Access-Control-Allow-Methods",
                   "GET,POST,PUT,DELETE,OPTIONS");
    newHeaders.set("Access-Control-Allow-Headers", "*");

    return new Response(resp.body, {
      status: resp.status,
      headers: newHeaders,
    });
  }
};
'''


def save_worker(url):
    WORKER_FILE.write_text(json.dumps({
        "url": url.strip().rstrip("/"),
        "ts": time.time(),
    }, indent=2))
    try:
        os.chmod(WORKER_FILE, 0o600)
    except Exception:
        pass


def get_worker():
    if WORKER_FILE.exists():
        try:
            return json.loads(WORKER_FILE.read_text()).get("url", "")
        except Exception:
            pass
    return ""


def test_worker(timeout=15):
    url = get_worker()
    if not url:
        return {"ok": False, "err": "no worker url"}
    try:
        req = urllib.request.Request(url + "/api/v1/models")
        t0 = time.time()
        with urllib.request.urlopen(
                req, timeout=timeout, context=SSL_CTX) as r:
            return {
                "ok": True,
                "status": r.status,
                "ms": int((time.time() - t0) * 1000),
            }
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            return {"ok": True, "status": e.code,
                    "note": "reachable"}
        return {"ok": False, "err": f"HTTP {e.code}"}
    except Exception as e:
        return {"ok": False, "err": str(e)[:80]}


# ═══════════════════════════════════════════════════
# 5. DASHBOARD
# ═══════════════════════════════════════════════════

def dashboard():
    print()
    print("=" * 60)
    print("  Server Hub — داشبورد")
    print("=" * 60)
    print()

    # SSH keys
    keys = list_keys()
    print(f"  SSH keys:    {len(keys)}")
    for k in keys:
        print(f"      {k['name']}  {'[pub]' if k['has_pub'] else '[no pub]'}")

    # Hosts
    hosts = load_hosts()
    print(f"  SSH hosts:   {len(hosts)}")
    for a, h in hosts.items():
        print(f"      {a}: {h['user']}@{h['host']}:{h['port']}")

    # Worker
    w = get_worker()
    print(f"  Worker:      {w or '(not set)'}")

    print()


# ═══════════════════════════════════════════════════
# 6. MENU (standalone)
# ═══════════════════════════════════════════════════

def _menu_standalone():
    C = {"G": "\033[0;32m", "R": "\033[0;31m", "Y": "\033[1;33m",
         "Cy": "\033[0;36m", "W": "\033[1;37m", "D": "\033[0m",
         "Bold": "\033[1m", "Dim": "\033[2m"}

    def ask(p, d=""):
        try:
            s = input(f"{C['Bold']}> {C['D']}{p}"
                      + (f" [{d}]" if d else "") + ": ").strip()
            return s or d
        except (EOFError, KeyboardInterrupt):
            return ""

    def pause():
        try:
            input(f"\n{C['Dim']}Enter...{C['D']}")
        except (EOFError, KeyboardInterrupt):
            pass

    while True:
        os.system("clear")
        print()
        print(C["Cy"] + "  ======================================" + C["D"])
        print(C["Cy"] + "  |      Server Hub  v1.0              |" + C["D"])
        print(C["Cy"] + "  ======================================" + C["D"])
        print()
        print(f"  {C['Y']}[1]{C['D']}  Cloud Providers (راهنما)")
        print(f"  {C['Y']}[2]{C['D']}  SSH Keys")
        print(f"  {C['Y']}[3]{C['D']}  SSH Hosts")
        print(f"  {C['Y']}[4]{C['D']}  Cloudflare Worker")
        print(f"  {C['Y']}[5]{C['D']}  Dashboard")
        print(f"  {C['Y']}[0]{C['D']}  Exit")
        print()
        c = ask("Choice")

        if c == "0":
            os.system("clear"); return
        elif c == "1":
            list_providers()
            k = ask("نام provider")
            if k:
                provider_info(k)
            pause()
        elif c == "2":
            print()
            print("  [1] Generate new key")
            print("  [2] List keys")
            print("  [3] Show public key")
            print("  [4] Delete key")
            s = ask("Choice")
            if s == "1":
                n = ask("Key name", "evoscanner")
                r, e = gen_key(n)
                if e:
                    print(f"  ✗ {e}")
                else:
                    print(f"  ✓ {r['priv']}")
                    print(f"  ✓ {r['pub']}")
            elif s == "2":
                for k2 in list_keys():
                    print(f"    {k2['name']}")
            elif s == "3":
                n = ask("Key name")
                p = show_pub(n)
                print(p or "not found")
            elif s == "4":
                n = ask("Key name")
                if n:
                    print(f"  deleted: {delete_key(n)} files")
            pause()
        elif c == "3":
            hosts = load_hosts()
            print()
            print("  [1] Add host")
            print("  [2] List hosts")
            print("  [3] Test host")
            print("  [4] Best host")
            print("  [5] Remove host")
            s = ask("Choice")
            if s == "1":
                a = ask("Alias")
                h = ask("Host (IP/domain)")
                u = ask("User", "root")
                p = ask("Port", "22")
                k = ask("Key name (optional)")
                if a and h:
                    add_host(a, h, u, p, k)
                    print("  ✓ added")
            elif s == "2":
                for a, h in hosts.items():
                    print(f"    {a}: {h['user']}@{h['host']}:{h['port']}")
            elif s == "3":
                a = ask("Alias")
                r = test_host(a)
                if r.get("ok"):
                    print(f"  ✓ {r['ms']}ms")
                else:
                    print(f"  ✗ {r.get('err')}")
            elif s == "4":
                b, all_r = best_host()
                if b:
                    print(f"  best: {b} ({all_r[b]['ms']}ms)")
                else:
                    print("  none working")
            elif s == "5":
                a = ask("Alias")
                if remove_host(a):
                    print("  ✓ removed")
            pause()
        elif c == "4":
            print()
            print("  [1] Show worker code (paste in CF dashboard)")
            print("  [2] Save worker URL")
            print("  [3] Test worker")
            s = ask("Choice")
            if s == "1":
                print()
                print(WORKER_CODE)
            elif s == "2":
                u = ask("Worker URL")
                if u:
                    save_worker(u)
                    print("  ✓ saved")
            elif s == "3":
                r = test_worker()
                if r.get("ok"):
                    print(f"  ✓ {r.get('ms','?')}ms HTTP {r.get('status')}")
                else:
                    print(f"  ✗ {r.get('err')}")
            pause()
        elif c == "5":
            dashboard(); pause()


if __name__ == "__main__":
    _menu_standalone()

