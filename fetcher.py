"""دریافت README کامل از GitHub"""
import base64, json, os, ssl, time, urllib.request
from pathlib import Path

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE
TOKEN = os.environ.get("GITHUB_TOKEN", "")
if not TOKEN:
    _env = Path.home() / "evoscanner" / ".env"
    if _env.exists():
        for _line in _env.read_text().splitlines():
            if _line.startswith("GITHUB_TOKEN="):
                TOKEN = _line.split("=", 1)[1].strip()
                break


def _headers():
    h = {"User-Agent": "Mozilla/5.0 EvoScanner/1.3",
         "Accept": "application/vnd.github.v3+json"}
    if TOKEN:
        h["Authorization"] = f"token {TOKEN}"
    return h


def _get(url, timeout=15):
    req = urllib.request.Request(url, headers=_headers())
    with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as r:
        return r.read(), dict(r.headers)


def fetch_readme(repo):
    url = f"https://api.github.com/repos/{repo}/readme"
    try:
        body, hdrs = _get(url)
        data = json.loads(body.decode("utf-8"))
        content = data.get("content", "")
        if data.get("encoding") == "base64":
            return base64.b64decode(content).decode("utf-8", errors="ignore")
        return content
    except Exception as e:
        return None


def enrich_top(kb, limit=100, min_score=0.3, skip_short=True):
    """غنی‌سازی منابع - از قبل غنی‌شده را رد می‌کند"""
    if skip_short:
        # منابعی که content کمتر از 2000 کاراکتر دارند
        rows = kb.conn.execute(
            """SELECT hash, title FROM resources
               WHERE source='github' AND score >= ?
                 AND length(content) < 2000
               ORDER BY score DESC LIMIT ?""",
            (min_score, limit)
        ).fetchall()
    else:
        rows = kb.conn.execute(
            """SELECT hash, title FROM resources
               WHERE source='github' AND score >= ?
               ORDER BY score DESC LIMIT ?""",
            (min_score, limit)
        ).fetchall()

    print(f"📥 {len(rows)} منبع نیاز به غنی‌سازی")
    if TOKEN:
        print("   ✓ با توکن (سهمیه ۵۰۰۰/ساعت)")
    else:
        print("   ⚠ بدون توکن (سهمیه ۶۰/ساعت) — برای توکن:")
        print("      export GITHUB_TOKEN=ghp_xxxx")
    print()

    ok, fail, rate = 0, 0, 0
    for i, (h, title) in enumerate(rows, 1):
        readme = fetch_readme(title)
        if readme is None:
            fail += 1
            if fail > 5 and fail == i:
                print(f"  ⚠ احتمالاً rate limit — صبر کن یا توکن بگذار")
                rate += 1
                if rate >= 3:
                    break
            continue
        kb.conn.execute(
            "UPDATE resources SET content=? WHERE hash=?",
            (readme[:5000], h))
        ok += 1
        if ok % 10 == 0 or ok <= 5:
            print(f"  ✓ [{ok}] {title[:50]} ({len(readme)} کاراکتر)")
        time.sleep(0.3)

    kb.conn.commit()
    print(f"\n✓ {ok} موفق | ✗ {fail} رد")
    return ok

