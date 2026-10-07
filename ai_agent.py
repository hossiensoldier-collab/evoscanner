"""AI Agent - LLM patch builder"""
import json, os, re, shutil, urllib.request
from datetime import datetime
from pathlib import Path

BASE = Path.home() / "evoscanner"

# SSL bypass baraye filter-shakan
import ssl as _ssl
SSL_CTX = _ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = _ssl.CERT_NONE
CONFIG = BASE / ".agent.json"
BACKUPS = BASE / "agent_backups"
BACKUPS.mkdir(exist_ok=True)
LOG = BASE / "agent_log.json"

PROVIDERS = {
    "groq": {
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "model": "llama-3.3-70b-versatile",
        "free": True,
        "signup": "https://console.groq.com/keys",
    },
    "openrouter": {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "model": "meta-llama/llama-3.3-70b-instruct:free",
        "free": True,
        "signup": "https://openrouter.ai/keys",
    },
    "deepinfra": {
        "url": "https://api.deepinfra.com/v1/openai/chat/completions",
        "model": "meta-llama/Meta-Llama-3.1-70B-Instruct",
        "free": False,
        "signup": "https://deepinfra.com/dash/api_keys",
    },
    "together": {
        "url": "https://api.together.xyz/v1/chat/completions",
        "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        "free": True,
        "signup": "https://api.together.xyz/settings/api-keys",
    },
}


def load_config():
    if CONFIG.exists():
        try:
            return json.loads(CONFIG.read_text())
        except Exception:
            pass
    return {}


def save_config(cfg):
    CONFIG.write_text(json.dumps(cfg, indent=2))
    try:
        os.chmod(CONFIG, 0o600)
    except Exception:
        pass


def get_key():
    return load_config().get("api_key", "")


def get_provider():
    return load_config().get("provider", "groq")


def configure(provider=None, api_key=None):
    cfg = load_config()
    if provider:
        cfg["provider"] = provider
    if api_key:
        cfg["api_key"] = api_key.strip()
    save_config(cfg)
    return cfg


def verify_key(timeout=15):
    cfg = load_config()
    key = cfg.get("api_key", "")
    prov = cfg.get("provider", "groq")
    if not key:
        return False, "no key"
    p = PROVIDERS.get(prov)
    if not p:
        return False, "provider bad"
    body = json.dumps({
        "model": p["model"],
        "messages": [{"role": "user", "content": "say ok"}],
        "max_tokens": 5,
    }).encode()
    req = urllib.request.Request(
        p["url"], data=body,
        headers={"Authorization": "Bearer " + key,
                 "Content-Type": "application/json",
                 "User-Agent": "EvoScanner-Agent"})
    try:
        with urllib.request.urlopen(req, timeout=timeout,
                                    context=SSL_CTX) as r:
            data = json.loads(r.read())
            return True, prov + "/" + p["model"]
    except urllib.error.HTTPError as e:
        if e.code == 401:
            return False, "key invalid (401)"
        return False, "HTTP " + str(e.code)
    except Exception as e:
        return False, str(e)


def project_context():
    st = {"version": "3.0.0", "files": [], "commands": [],
          "db": 0, "graph_nodes": 0, "graph_edges": 0}
    vf = BASE / "version.txt"
    if vf.exists():
        st["version"] = vf.read_text().strip()
    for f in sorted(BASE.glob("*.py")):
        try:
            st["files"].append({"name": f.name,
                "lines": len(f.read_text().splitlines())})
        except Exception:
            pass
    try:
        import sqlite3
        db = sqlite3.connect(BASE / "knowledge.db")
        st["db"] = db.execute("SELECT COUNT(*) FROM resources").fetchone()[0]
        db.close()
    except Exception:
        pass
    try:
        g = json.loads((BASE / "graph.json").read_text())
        st["graph_nodes"] = sum(1 for v in g["nodes"].values()
                                 if v.get("type") == "entity")
        st["graph_edges"] = len(g.get("edges", {}))
    except Exception:
        pass
    try:
        txt = (BASE / "evoscanner_v2.py").read_text()
        st["commands"] = sorted(set(
            re.findall(r'cmd\s*==\s*"([^"]+)"', txt)))
    except Exception:
        pass
    return st


SYSTEM_PROMPT = """You are a Python developer assistant for the EvoScanner project.
It runs on Termux/Android with only stdlib Python.

RULES:
1. Respond ONLY in code blocks.
2. New file format:
   [FENCE]file:relative/path.py
   (content)
   [FENCE]

3. Patch existing file:
   [FENCE]patch:relative/path.py
   <<<<<<< OLD
   exact old code
   =======
   new code
   >>>>>>> NEW
   [FENCE]

Replace [FENCE] with triple backticks in your actual response.

4. Menu functions in panel.py follow this pattern:
   def menu_xxx():
       while True:
           banner()
           title("Title")
           print(...)
           c = ask("Entekhab")
           if c == "0": return
           elif c == "1": ...

5. Available colors: C['R'], C['G'], C['Y'], C['B'], C['M'],
   C['Cy'], C['W'], C['D'], C['Bold'], C['Dim']

6. Menu item format:
   print(f"  {C['Y']}[N]{C['D']}  Title  {C['Dim']}sub{C['D']}")

7. Give complete runnable code. No "..." placeholders.

8. Keep code in separate files when possible.
"""


def ask_llm(wish, kind="feature", timeout=120):
    cfg = load_config()
    key = cfg.get("api_key", "")
    prov = cfg.get("provider", "groq")
    p = PROVIDERS.get(prov)
    if not key or not p:
        return None, "key or provider missing"

    st = project_context()
    files_txt = "\n".join(
        "  - " + f["name"] + " (" + str(f["lines"]) + " lines)"
        for f in st["files"])

    user_msg = (
        "## User wish:\n\n" + wish + "\n\n"
        + "## Kind: " + kind + "\n\n"
        + "## Project state:\n\n"
        + "- version: v" + st["version"] + "\n"
        + "- resources: " + str(st["db"]) + "\n"
        + "- graph: " + str(st["graph_nodes"]) + " nodes, "
        + str(st["graph_edges"]) + " edges\n"
        + "- commands: " + ", ".join(st["commands"][:30]) + "\n\n"
        + "## Files:\n" + files_txt + "\n\n"
        + "Give me code and patches. No explanation."
    )

    body = json.dumps({
        "model": p["model"],
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        "temperature": 0.2,
        "max_tokens": 4000,
    }).encode()

    req = urllib.request.Request(
        p["url"], data=body,
        headers={"Authorization": "Bearer " + key,
                 "Content-Type": "application/json",
                 "User-Agent": "EvoScanner-Agent"})
    try:
        with urllib.request.urlopen(req, timeout=timeout,
                                    context=SSL_CTX) as r:
            data = json.loads(r.read())
            return data["choices"][0]["message"]["content"], None
    except urllib.error.HTTPError as e:
        return None, "HTTP " + str(e.code)
    except Exception as e:
        return None, str(e)


FILE_BLOCK = re.compile(r"```file:([^\n]+)\n([\s\S]*?)```", re.M)
PATCH_BLOCK = re.compile(r"```patch:([^\n]+)\n([\s\S]*?)```", re.M)


def parse_response(text):
    files = []
    patches = []
    for m in FILE_BLOCK.finditer(text):
        files.append({"path": m.group(1).strip(),
                      "content": m.group(2)})
    for m in PATCH_BLOCK.finditer(text):
        body = m.group(2)
        om = re.search(
            r"<<<<<<< OLD\n([\s\S]*?)\n=======\n"
            r"([\s\S]*?)\n>>>>>>> NEW", body)
        if om:
            patches.append({"path": m.group(1).strip(),
                            "old": om.group(1),
                            "new": om.group(2)})
    return files, patches


def backup_all():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder = BACKUPS / ts
    folder.mkdir(exist_ok=True)
    for f in BASE.glob("*.py"):
        shutil.copy(f, folder / f.name)
    return folder


def verify_syntax(path):
    try:
        import py_compile
        py_compile.compile(str(path), doraise=True)
        return True, None
    except Exception as e:
        return False, str(e)[:120]


def apply_files(files):
    res = []
    for f in files:
        path = (BASE / f["path"]).resolve()
        if not str(path).startswith(str(BASE)):
            res.append((f["path"], False, "path outside"))
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f["content"], encoding="utf-8")
        ok, err = (verify_syntax(path)
                   if path.suffix == ".py" else (True, None))
        res.append((f["path"], ok, err))
    return res


def apply_patches(patches):
    res = []
    for p in patches:
        path = (BASE / p["path"]).resolve()
        if not str(path).startswith(str(BASE)):
            res.append((p["path"], False, "path outside"))
            continue
        if not path.exists():
            res.append((p["path"], False, "file not found"))
            continue
        code = path.read_text(encoding="utf-8")
        if p["old"] not in code:
            res.append((p["path"], False, "old text not found"))
            continue
        if code.count(p["old"]) > 1:
            res.append((p["path"], False,
                        "old text " + str(code.count(p["old"])) + " times"))
            continue
        new_code = code.replace(p["old"], p["new"], 1)
        path.write_text(new_code, encoding="utf-8")
        ok, err = (verify_syntax(path)
                   if path.suffix == ".py" else (True, None))
        if not ok:
            path.write_text(code, encoding="utf-8")
            res.append((p["path"], False, "syntax err: " + str(err)))
        else:
            res.append((p["path"], True, None))
    return res


def log_run(wish, kind, files_res, patches_res, backup):
    log = []
    if LOG.exists():
        try:
            log = json.loads(LOG.read_text())
        except Exception:
            pass
    log.append({
        "ts": datetime.now().isoformat(),
        "wish": wish[:200],
        "kind": kind,
        "files": [{"path": p, "ok": o, "err": e} for p, o, e in files_res],
        "patches": [{"path": p, "ok": o, "err": e} for p, o, e in patches_res],
        "backup": str(backup) if backup else None,
    })
    LOG.write_text(json.dumps(log[-50:], indent=2, ensure_ascii=False))


def list_runs(limit=15):
    if not LOG.exists():
        return []
    try:
        return list(reversed(json.loads(LOG.read_text())[-limit:]))
    except Exception:
        return []


def rollback_last():
    runs = list_runs(1)
    if not runs:
        return False, "no log"
    r = runs[0]
    if not r.get("backup"):
        return False, "no backup"
    folder = Path(r["backup"])
    if not folder.exists():
        return False, "folder missing"
    n = 0
    for f in folder.glob("*.py"):
        shutil.copy(f, BASE / f.name)
        n += 1
    return True, str(n) + " files restored from " + folder.name


def rollback_by_index(idx):
    runs = list_runs(20)
    if idx < 1 or idx > len(runs):
        return False, "index bad"
    r = runs[idx - 1]
    if not r.get("backup"):
        return False, "no backup"
    folder = Path(r["backup"])
    if not folder.exists():
        return False, "folder missing"
    n = 0
    for f in folder.glob("*.py"):
        shutil.copy(f, BASE / f.name)
        n += 1
    return True, str(n) + " files restored from " + folder.name


def run_full(wish, kind="feature"):
    text, err = ask_llm(wish, kind)
    if err:
        return {"ok": False, "error": err}
    if not text:
        return {"ok": False, "error": "empty response"}
    files, patches = parse_response(text)
    if not files and not patches:
        return {"ok": False, "error": "no code in response",
                "text": text}
    backup = backup_all()
    files_res = apply_files(files)
    patches_res = apply_patches(patches)
    log_run(wish, kind, files_res, patches_res, backup)
    return {"ok": True, "files": files_res, "patches": patches_res,
            "backup": str(backup), "text": text}


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "config" and len(sys.argv) > 3:
            configure(sys.argv[2], sys.argv[3])
            print("saved")
        elif sys.argv[1] == "verify":
            ok, msg = verify_key()
            print(("OK: " if ok else "FAIL: ") + msg)
        elif sys.argv[1] == "run":
            print(json.dumps(run_full(" ".join(sys.argv[2:])),
                             indent=2, ensure_ascii=False))
        elif sys.argv[1] == "history":
            for i, r in enumerate(list_runs(), 1):
                print("  " + str(i) + ". " + r["ts"][:16]
                      + "  " + r["wish"][:60])
        elif sys.argv[1] == "rollback":
            ok, msg = rollback_last()
            print(msg)

