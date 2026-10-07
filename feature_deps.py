"""Dependency Extractor — از GitHub pyproject/requirements"""
import json
import re
import ssl
import time
import urllib.request
from datetime import datetime
from pathlib import Path

BASE = Path.home() / "evoscanner"
OUT = BASE / "deps_graph.json"

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

# لود توکن
def get_token():
    try:
        from auth import get_token
        return get_token()
    except Exception:
        return ""


def _http_get(url, timeout=5):
    token = get_token()
    headers = {"User-Agent": "EvoScanner-Deps"}
    if token:
        headers["Authorization"] = "token " + token
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout,
                                    context=SSL_CTX) as r:
            return r.read().decode("utf-8", errors="ignore")
    except Exception:
        return None


def _http_get(url, timeout=5):
    token = get_token()
    headers = {"User-Agent": "EvoScanner-Deps"}
    if token:
        headers["Authorization"] = "token " + token
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout,
                                    context=SSL_CTX) as r:
            return r.read().decode("utf-8", errors="ignore")
    except Exception:
        return None


def _http_get(url, timeout=5):
    token = get_token()
    headers = {"User-Agent": "EvoScanner-Deps"}
    if token:
        headers["Authorization"] = "token " + token
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout,
                                    context=SSL_CTX) as r:
            return r.read().decode("utf-8", errors="ignore")
    except Exception:
        return None


def fetch_file(repo, path):
    """دریافت فایل — فقط main و master (سریع‌تر)"""
    for branch in ("main", "master"):
        url = f"https://raw.githubusercontent.com/{repo}/{branch}/{path}"
        text = _http_get(url, timeout=5)   # timeout کوتاه
        if text:
            return text
    return None



def parse_pyproject(text):
    """پارس dependencies از pyproject.toml (بدون toml lib)"""
    deps = []

    # [project] dependencies = [...]
    m = re.search(r'dependencies\s*=\s*\[([\s\S]*?)\]', text)
    if m:
        for line in m.group(1).split("\n"):
            line = line.strip().strip(',').strip('"').strip("'")
            # fastapi>=0.100.0 → fastapi
            pkg = re.split(r'[<>=!~\[;]', line)[0].strip()
            if pkg and len(pkg) > 1:
                deps.append(pkg.lower())

    # [tool.poetry.dependencies]
    in_poetry = False
    for line in text.split("\n"):
        if "[tool.poetry.dependencies]" in line:
            in_poetry = True
            continue
        if in_poetry:
            if line.startswith("[") and "dependencies" not in line:
                in_poetry = False
                continue
            m2 = re.match(r'^([a-zA-Z][a-zA-Z0-9_\-]+)\s*=', line)
            if m2:
                pkg = m2.group(1).lower()
                if pkg not in ("python",):
                    deps.append(pkg)

    return list(set(deps))


def parse_requirements(text):
    """پارس requirements.txt — بدون comment و بدون نویز"""
    deps = []
    SKIP = {
        "python", "pip", "setuptools", "wheel",
        "requirements", "requirements.txt", "deps",
    }
    for line in text.split("\n"):
        line = line.strip()

        # حذف comment
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        if line.startswith("//"):
            continue

        # حذف inline comment
        if "  #" in line:
            line = line.split("  #")[0].strip()
        if " #" in line:
            line = line.split(" #")[0].strip()

        # حذف -r دیگران
        if line.startswith("-r"):
            continue

        # پکیج
        pkg = re.split(r'[<>=!~\[;\s]', line)[0].strip().lower()

        if not pkg:
            continue
        if len(pkg) < 2 or len(pkg) > 40:
            continue
        if pkg in SKIP:
            continue
        if not re.match(r'^[a-z][a-z0-9_\-\.]*$', pkg):
            continue
        # فقط خطوط ASCII
        try:
            pkg.encode("ascii")
        except Exception:
            continue

        deps.append(pkg)

    return list(set(deps))



KNOWN_DEPS_FALLBACK = {
    # repo → لیست وابستگی‌های اصلی (اگر فایل‌ها خوانده نشدند)
    "pandas-dev/pandas": ["numpy", "python-dateutil", "pytz", "tzdata"],
    "pandas-dev/pandas-main": ["numpy", "python-dateutil", "pytz", "tzdata"],
    "numpy/numpy": ["cython", "pybind11", "setuptools"],
    "huggingface/transformers": [
        "numpy", "tokenizers", "huggingface-hub",
        "safetensors", "packaging", "pyyaml", "regex",
        "requests", "tqdm", "filelock",
    ],
    "pytorch/pytorch": ["numpy", "typing-extensions", "sympy", "networkx",
                         "jinja2", "fsspec", "filelock"],
    "tensorflow/tensorflow": ["numpy", "wheel", "six", "protobuf",
                                "absl-py", "astunparse"],
    "scikit-learn/scikit-learn": ["numpy", "scipy", "joblib", "threadpoolctl"],
    "pallets/flask": ["werkzeug", "jinja2", "click", "itsdangerous",
                       "markupsafe", "blinker"],
    "django/django": ["asgiref", "sqlparse", "tzdata"],
    "fastapi/fastapi": ["starlette", "pydantic", "typing-extensions",
                         "opentelemetry-api"],
}


def extract_for_repo(repo):
    """برای یک repo — همه فایل‌ها را امتحان کن"""
    all_deps = set()

    for fname in (
        "pyproject.toml",
        "requirements.txt",
        "setup.py",
        "setup.cfg",
    ):
        text = fetch_file(repo, fname)
        if not text:
            continue
        if fname == "pyproject.toml":
            all_deps.update(parse_pyproject(text))
        elif "requirements" in fname:
            all_deps.update(parse_requirements(text))
        elif fname == "Pipfile":
            in_pkg = False
            for line in text.split("\n"):
                if line.strip() == "[packages]":
                    in_pkg = True
                    continue
                if in_pkg:
                    if line.startswith("["):
                        in_pkg = False
                        continue
                    m2 = re.match(r'^([a-zA-Z][a-zA-Z0-9_\-]+)\s*=', line)
                    if m2:
                        all_deps.add(m2.group(1).lower())
        elif fname == "setup.py":
            m = re.search(r'install_requires\s*=\s*\[([\s\S]*?)\]', text)
            if m:
                for line in m.group(1).split("\n"):
                    line = line.strip().strip(',').strip('"').strip("'")
                    pkg = re.split(r'[<>=!~\[;]', line)[0].strip()
                    if pkg and len(pkg) > 1:
                        all_deps.add(pkg.lower())
        elif fname == "setup.cfg":
            in_inst = False
            for line in text.split("\n"):
                if line.strip().startswith("install_requires"):
                    in_inst = True
                    continue
                if in_inst:
                    if line and not line.startswith(" "):
                        in_inst = False
                        continue
                    line = line.strip()
                    if line and not line.startswith("#"):
                        pkg = re.split(r'[<>=!~\[;]', line)[0].strip()
                        if pkg and len(pkg) > 1:
                            all_deps.add(pkg.lower())
        elif fname == "environment.yml":
            for line in text.split("\n"):
                m2 = re.match(r'^\s*-\s+([a-zA-Z][a-zA-Z0-9_\-]+)', line)
                if m2:
                    pkg = m2.group(1).lower()
                    if pkg not in ("pip", "python", "conda"):
                        all_deps.add(pkg)

    # fallback اگر خالی بود
    if not all_deps and repo in KNOWN_DEPS_FALLBACK:
        all_deps.update(KNOWN_DEPS_FALLBACK[repo])

    return list(all_deps)



from concurrent.futures import ThreadPoolExecutor, as_completed


def _process_one(title):
    """پردازش یک repo — فقط از pyproject و requirements"""
    repo = title.strip()
    deps = extract_for_repo(repo)
    return repo, deps


def build(kb_limit=100, workers=8):
    import sys
    sys.path.insert(0, str(BASE))
    from evoscanner_v2 import KB
    kb = KB()

    print()
    print("=" * 60)
    print(f"  DEPENDENCY EXTRACTOR (parallel, {workers} workers)")
    print("=" * 60)
    print()

    rows = kb.conn.execute(
        """SELECT title FROM resources
           WHERE source='github' AND title LIKE '%/%'
           LIMIT ?""", (kb_limit,)
    ).fetchall()

    titles = [r[0] for r in rows]
    print(f"  {len(titles)} repo — موازی با {workers} worker")
    print()

    graph = {"edges": {}, "repos": {}}
    done = 0

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(_process_one, t): t for t in titles}
        for fut in as_completed(futures):
            done += 1
            try:
                repo, deps = fut.result(timeout=60)
            except Exception as e:
                print(f"  [{done}/{len(titles)}] ✗ {e}")
                continue

            if not deps:
                print(f"  [{done}/{len(titles)}] {repo}")
                continue

            graph["repos"][repo] = deps
            pkg_name = repo.split("/")[-1].lower()

            for dep in deps:
                key = f"{pkg_name}|requires|{dep}"
                if key not in graph["edges"]:
                    graph["edges"][key] = {
                        "a": pkg_name, "b": dep, "cat": "requires",
                        "observations": 0,
                        "confidence": 0.0,
                    }
                graph["edges"][key]["observations"] += 1

            print(f"  [{done}/{len(titles)}] {repo} → {len(deps)} dep")

    # اطمینان
    for key, e in graph["edges"].items():
        n = e["observations"]
        e["confidence"] = min(1.0, 0.5 + n * 0.5)

    graph["stats"] = {
        "edges": len(graph["edges"]),
        "repos": len(graph["repos"]),
        "built_at": datetime.now().isoformat(),
    }

    OUT.write_text(json.dumps(graph, indent=2, ensure_ascii=False))

    print()
    print(f"  ✓ {len(graph['edges'])} یال از {len(graph['repos'])} repo")
    print()



def stats():
    if not OUT.exists():
        print("  ! گراف نیست. اول build بزن")
        return
    g = json.loads(OUT.read_text())
    edges = g["edges"]
    print()
    print(f"  ◆ Dependency Graph Stats")
    print()
    print(f"  یال‌ها: {len(edges)}")
    print(f"  repoها: {len(g.get('repos', {}))}")
    print()
    # بالاترین اطمینان
    top = sorted(edges.values(), key=lambda x: -x["confidence"])[:20]
    print(f"  بالاترین اطمینان:")
    for e in top:
        print(f"    {e['confidence']:.0%}  {e['a']} → {e['b']}  ({e['observations']})")


def requires(pkg):
    if not OUT.exists():
        print("  ! گراف نیست")
        return
    g = json.loads(OUT.read_text())
    edges = g["edges"]
    pkg = pkg.lower()
    print()
    print(f"  ◆ requires {pkg}")
    print()
    found = []
    for e in edges.values():
        if e["a"] == pkg:
            found.append(e)
    found.sort(key=lambda x: -x["confidence"])
    if not found:
        print(f"  چیزی پیدا نشد")
        return
    for e in found[:20]:
        bar = "#" * int(e["confidence"] * 20)
        print(f"  {e['confidence']:.0%}  {e['b']:25s}  {bar}")


def breaks(pkg):
    if not OUT.exists():
        print("  ! گراف نیست")
        return
    g = json.loads(OUT.read_text())
    edges = g["edges"]
    pkg = pkg.lower()
    print()
    print(f"  ◆ breaks-if-removed {pkg}")
    print()
    found = [e for e in edges.values() if e["b"] == pkg]
    found.sort(key=lambda x: -x["confidence"])
    if not found:
        print(f"  هیچ‌کس به آن وابسته نیست")
        return
    for e in found[:20]:
        print(f"  {e['confidence']:.0%}  {e['a']:25s}")


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "stats"
    if cmd == "build":
        limit = 100
        for a in sys.argv[2:]:
            if a.startswith("--limit="):
                limit = int(a.split("=")[1])
        build(kb_limit=limit)
    elif cmd == "stats":
        stats()
    elif cmd == "requires" and len(sys.argv) > 2:
        requires(sys.argv[2])
    elif cmd == "breaks" and len(sys.argv) > 2:
        breaks(sys.argv[2])

