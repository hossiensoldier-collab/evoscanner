"""RAG v4 — از snippet و تکنیک‌های استخراج‌شده"""
import math
import re
from collections import Counter
from pathlib import Path

BASE = Path.home() / "evoscanner"

TOK = re.compile(r"[a-zA-Z_][a-zA-Z0-9_\-]{2,30}|[\u0600-\u06FF]{2,30}")
STOP = set("the a an and or of in on to for with is are was were be been "
           "this that it as at by if not my we you can will have has had "
           "do does did but from how what when where which who why "
           "را به از که این آن است بود با برای در".split())

JUNK = [
    "typeshed", "dnspython", "stub", "pywin32",
    "clips/pattern", "clips/", "shopify", "awslabs/",
]

# کلماتی که نویز هستند
JUNK_WORDS = {
    "if", "in", "on", "of", "to", "for", "from", "with",
    "the", "this", "that", "you", "can", "will",
}


def tokenize(text):
    return [t.lower() for t in TOK.findall(text or "")
            if t.lower() not in STOP]


def clean(text):
    if not text:
        return ""
    t = text
    t = re.sub(r'```[\s\S]*?```', ' ', t)
    t = re.sub(r'`[^`]*`', ' ', t)
    t = re.sub(r'<[^>]+>', ' ', t)
    t = re.sub(r'!\[.*?\]\(.*?\)', ' ', t)
    t = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', t)
    t = re.sub(r'[#*|>_~]+', ' ', t)
    t = re.sub(r'\s+', ' ', t)
    return t.strip()


def bm25(q_tokens, doc_tokens, avg_len, k1=1.5, b=0.75):
    if not doc_tokens:
        return 0.0
    dl = len(doc_tokens)
    tf = Counter(doc_tokens)
    score = 0.0
    for q in set(q_tokens):
        f = tf.get(q, 0)
        if f == 0:
            continue
        idf = math.log(1 + 1 / (f / dl + 0.5))
        score += idf * (f * (k1 + 1)) / (f + k1 * (1 - b + b * dl / avg_len))
    return score


def cosine(v1, v2):
    dot = sum(a * b for a, b in zip(v1, v2))
    m1 = math.sqrt(sum(a * a for a in v1))
    m2 = math.sqrt(sum(b * b for b in v2))
    if m1 == 0 or m2 == 0:
        return 0
    return dot / (m1 * m2)


def build_index(docs):
    """docs = [(text, url, title, source_type)]"""
    all_toks = [tokenize(d[0]) for d in docs]
    df = Counter()
    for toks in all_toks:
        for w in set(toks):
            df[w] += 1
    N = max(len(docs), 1)
    vocab = {w: i for i, w in enumerate(df.keys())}
    idf = {w: math.log(N / c) for w, c in df.items()}

    chunks = []
    for toks, doc in zip(all_toks, docs):
        text, url, title, src = doc
        vec = [0.0] * len(vocab)
        tf = Counter(toks)
        for w, f in tf.items():
            if w in vocab:
                vec[vocab[w]] = (1 + math.log(f)) * idf[w]
        m = math.sqrt(sum(x * x for x in vec))
        if m > 0:
            vec = [x / m for x in vec]
        chunks.append({
            "vec": vec, "text": text, "url": url,
            "title": title, "src": src, "toks": toks,
        })
    return {"chunks": chunks, "vocab": vocab, "idf": idf}


def vector_search(idx, q, top_k=20):
    toks = tokenize(q)
    if not toks:
        return []
    vocab = idx["vocab"]
    idf = idx["idf"]
    qvec = [0.0] * len(vocab)
    tf = Counter(toks)
    for w, f in tf.items():
        if w in vocab:
            qvec[vocab[w]] = (1 + math.log(f)) * idf[w]
    m = math.sqrt(sum(x * x for x in qvec))
    if m > 0:
        qvec = [x / m for x in qvec]

    scored = []
    for c in idx["chunks"]:
        s = cosine(qvec, c["vec"])
        if s > 0:
            scored.append((s, c))
    scored.sort(key=lambda x: -x[0])
    return scored[:top_k]


def bm25_search(idx, q, top_k=20):
    toks = tokenize(q)
    if not toks:
        return []
    docs = idx["chunks"]
    avg = sum(len(d["toks"]) for d in docs) / max(len(docs), 1)
    scored = []
    for d in docs:
        s = bm25(toks, d["toks"], avg)
        if s > 0:
            scored.append((s, d))
    scored.sort(key=lambda x: -x[0])
    return scored[:top_k]


def rrf(results_list, k=60, q_tokens=None):
    """RRF + boost بر اساس URL و type"""
    from collections import Counter as _C

    scores = {}
    seen = {}
    for results in results_list:
        for rank, (score, item) in enumerate(results, 1):
            key = item.get("url", "") + "|" + item["text"][:40]
            scores[key] = scores.get(key, 0) + 1 / (k + rank)
            seen[key] = item

    if q_tokens:
        qs = set(q_tokens)

        for key, item in seen.items():
            # ── ۱. boost URL (owner/repo)
            url = item.get("url", "").lower()
            # استخراج owner/repo از URL
            m = re.search(r'github\.com/([^/]+)/([^/]+)', url)
            if m:
                owner = m.group(1)
                repo = m.group(2).rstrip("/")
                url_tokens = _C()
                for t in tokenize(owner) + tokenize(repo):
                    url_tokens[t] += 1
                boost = 1.0
                for q in qs:
                    if url_tokens[q]:
                        # اگر کلمه در owner و repo هر دو → boost زیاد
                        boost += url_tokens[q] * 2.5
                scores[key] *= boost

            # ── ۲. boost عنوان
            title_toks = _C()
            for t in tokenize(item.get("title", "")):
                title_toks[t] += 1
            for q in qs:
                if title_toks[q]:
                    scores[key] *= (1 + title_toks[q] * 1.5)

            # ── ۳. boost type
            src_type = item.get("src", "")
            if src_type == "snippet":
                scores[key] *= 2.0
            elif src_type == "technique":
                scores[key] *= 1.5

            # ── ۴. جریمه کلمات عمومی
            generic = {"setup", "install", "run", "use", "using",
                       "how", "what", "get", "make", "build"}
            generic_hits = len(qs & generic)
            if generic_hits and not (qs - generic):
                # کل سؤال عمومی است
                scores[key] *= 0.3
            elif generic_hits:
                # قسمتی عمومی است
                scores[key] *= (1 - 0.15 * generic_hits)

    # ── ۵. Boost صریح: اگر repo name دقیقاً برابر کلمه باشد
    if q_tokens:
        qs = set(q_tokens)
        for key, item in seen.items():
            url = item.get("url", "").lower()
            m = re.search(r'github\.com/[^/]+/([^/]+)', url)
            if m:
                repo = m.group(1).rstrip("/")
                repo_toks = set(tokenize(repo))
                # اگر repo name یک کلمه سؤال است → boost ×5
                if repo in qs or (len(repo_toks) == 1 and repo_toks & qs):
                    scores[key] *= 5.0

    out = [(scores[k], seen[k]) for k in scores]
    out.sort(key=lambda x: -x[0])
    # فیلتر نویز
    out = [(s, i) for s, i in out
           if not any(j in i.get("url", "").lower() for j in JUNK)]
    return out


# ═══════════════════════════════════════════════════
#  جمع‌آوری docs از پایگاه
# ═══════════════════════════════════════════════════

def gather_docs(kb):
    """snippet + technique + resource title"""
    docs = []

    # ۱. Snippets (اولویت)
    try:
        rows = kb.conn.execute(
            """SELECT purpose, code, source_url FROM snippets
               WHERE length(code) > 30 LIMIT 500"""
        ).fetchall()
        for purpose, code, url in rows:
            text = clean(f"{purpose}. {code[:500]}")
            if len(text) > 40:
                docs.append((text, url or "", purpose or "", "snippet"))
    except Exception:
        pass

    # ۲. تکنیک‌ها
    try:
        rows = kb.conn.execute(
            """SELECT name, category, source_url, difficulty
               FROM techniques LIMIT 500"""
        ).fetchall()
        for name, cat, url, diff in rows:
            text = f"{name} — {cat} — {diff}"
            if len(text) > 15:
                docs.append((text, url or "", name or "", "technique"))
    except Exception:
        pass

    # ۳. عنوان منابع (بدون content)
    try:
        rows = kb.conn.execute(
            """SELECT title, url, category FROM resources
               WHERE length(title) > 5 LIMIT 500"""
        ).fetchall()
        for title, url, cat in rows:
            text = f"{title} — {cat}"
            docs.append((text, url or "", title or "", "resource"))
    except Exception:
        pass

    return docs


CY = "\033[38;2;100;220;230m"
WH = "\033[38;2;230;230;240m"
GY = "\033[38;2;130;135;150m"
GR = "\033[38;2;120;230;150m"
YL = "\033[38;2;255;215;80m"
PU = "\033[38;2;180;140;255m"
R = "\033[0m"


def ask(kb, question, top_k=5):
    print()
    print(f"  {'=' * 58}")
    print(f"  ❓ {question}")
    print(f"  {'=' * 58}")
    print()

    print(f"  جمع‌آوری...", end="", flush=True)
    docs = gather_docs(kb)
    print(f" {len(docs)} مورد")

    if not docs:
        print("  ✗ چیزی نیست — اول extract بزن")
        return

    # شمارش انواع
    types = Counter(d[3] for d in docs)
    print(f"  انواع: " + " | ".join(f"{k} {v}" for k, v in types.items()))

    print(f"  ایندکس...", end="", flush=True)
    idx = build_index(docs)
    print(f" vocab {len(idx['vocab'])}")

    q_toks = tokenize(question)
    print(f"  کلمات کلیدی: {', '.join(q_toks[:6])}")
    print()

    vec = vector_search(idx, question, top_k=20)
    bm = bm25_search(idx, question, top_k=20)
    fused = rrf([vec, bm], q_tokens=q_toks)

    # نمایش
    print(f"  {WH}{'─' * 56}{R}")
    print(f"  {CY}نتیجه:{R}")
    print()

    shown = 0
    seen_urls = set()      # فقط ۱ نتیجه per URL
    seen_texts = set()
    results = []
    for score, item in fused:
        url = item.get("url", "")
        text_key = item["text"][:60]

        if url and url in seen_urls:
            continue
        if text_key in seen_texts:
            continue

        if url:
            seen_urls.add(url)
        seen_texts.add(text_key)
        results.append((score, item))
        shown += 1
        if shown >= top_k:
            break

    if not results:
        print(f"  ✗ چیزی پیدا نشد")
        return

    for i, (score, item) in enumerate(results, 1):
        src = item["src"]
        src_color = {
            "snippet": GR, "technique": PU,
            "resource": CY
        }.get(src, CY)

        print(f"  {CY}[{i}]{R} {src_color}[{src}]{R} "
              f"{WH}{item['title'][:50]}{R}")
        print(f"      {item['text'][:300]}")
        if item["url"]:
            print(f"      {GY}{item['url']}{R}")
        print(f"      {YL}score: {score:.4f}{R}")
        print()


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(BASE))
    from evoscanner_v2 import KB
    kb = KB()
    if len(sys.argv) > 1:
        ask(kb, " ".join(sys.argv[1:]))
    else:
        q = input("سؤال: ").strip()
        if q:
            ask(kb, q)

