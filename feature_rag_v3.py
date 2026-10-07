"""RAG v3 — Hybrid TF-IDF + BM25 + RRF"""
import math
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

BASE = Path.home() / "evoscanner"

TOK = re.compile(r"[a-zA-Z_][a-zA-Z0-9_\-]{2,30}|[\u0600-\u06FF]{2,30}")
STOP = set("the a an and or of in on to for with is are was were be been "
           "this that it as at by if not my we you can will have has had "
           "do does did but from how what when where which who why "
           "را به از که این آن است بود با برای در".split())


def tokenize(text):
    return [t.lower() for t in TOK.findall(text or "")
            if t.lower() not in STOP]


def smart_chunk(text, min_size=80, max_size=500):
    if not text:
        return []
    text = re.sub(r'```[\s\S]*?```', ' ', text)
    text = re.sub(r'`[^`]+`', ' ', text)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'!\[.*?\]\(.*?\)', ' ', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = re.sub(r'\[code\]', '', text, flags=re.I)
    text = re.sub(r'_+', ' ', text)
    text = re.sub(r'\*+', ' ', text)
    text = re.sub(r'\|', ' ', text)
    text = re.sub(r'#+\s*', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) < min_size:
        return []
    sents = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    cur = ""
    for s in sents:
        if len(cur) + len(s) < max_size:
            cur += " " + s
        else:
            if len(cur) >= min_size:
                chunks.append(cur.strip())
            cur = s
    if len(cur) >= min_size:
        chunks.append(cur.strip())
    return [c for c in chunks if min_size <= len(c) <= max_size * 2]


def bm25_score(q_tokens, doc_tokens, avg_len, k1=1.5, b=0.75):
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


class Index:
    def __init__(self):
        self.vocab = {}
        self.idf = {}
        self.chunks = []

    def build(self, docs):
        all_tokens = [tokenize(text) for text, _, _ in docs]
        df = Counter()
        for toks in all_tokens:
            for w in set(toks):
                df[w] += 1
        N = max(len(docs), 1)
        self.vocab = {w: i for i, w in enumerate(df.keys())}
        self.idf = {w: math.log(N / c) for w, c in df.items()}

        for toks, (text, url, title) in zip(all_tokens, docs):
            vec = [0.0] * len(self.vocab)
            tf = Counter(toks)
            for w, f in tf.items():
                if w in self.vocab:
                    vec[self.vocab[w]] = (1 + math.log(f)) * self.idf[w]
            m = math.sqrt(sum(x * x for x in vec))
            if m > 0:
                vec = [x / m for x in vec]
            self.chunks.append({"vec": vec, "text": text,
                                 "url": url, "title": title})
        return self

    def query(self, q, top_k=20):
        toks = tokenize(q)
        if not toks or not self.vocab:
            return []
        qvec = [0.0] * len(self.vocab)
        tf = Counter(toks)
        for w, f in tf.items():
            if w in self.vocab:
                qvec[self.vocab[w]] = (1 + math.log(f)) * self.idf[w]
        m = math.sqrt(sum(x * x for x in qvec))
        if m > 0:
            qvec = [x / m for x in qvec]
        scored = []
        for c in self.chunks:
            s = cosine(qvec, c["vec"])
            if s > 0:
                scored.append((s, c))
        scored.sort(key=lambda x: -x[0])
        return scored[:top_k]


def rrf(results_list, k=60, q_tokens=None):
    scores = {}
    seen = {}
    for results in results_list:
        for rank, (score, item) in enumerate(results, 1):
            key = item.get("url", "") + "|" + item["text"][:50]
            scores[key] = scores.get(key, 0) + 1 / (k + rank)
            seen[key] = item
    if q_tokens:
        for key, item in seen.items():
            title_toks = set(tokenize(item.get("title", "")))
            hits = len(set(q_tokens) & title_toks)
            if hits:
                scores[key] *= (1 + hits * 0.7)
    out = [(scores[k], seen[k]) for k in scores]
    out.sort(key=lambda x: -x[0])
    return out


# منابعی که در نتایج نویز هستند
JUNK_URLS = [
    "typeshed", "dnspython", "stub", "pywin32",
    "asyncio-stubs", "pytest-stubs", "types-",
]

SYNONYMS = {
    "async": ["asyncio", "coroutine"],
    "web": ["http", "server"],
    "db": ["database", "sql"],
    "ml": ["machine learning"],
    "test": ["pytest", "testing"],
    "rag": ["retrieval", "vector"],
    "سریع": ["performance", "fast"],
    "هوش": ["ai", "ml"],
}


def expand_query(q):
    raw = [t.lower() for t in TOK.findall(q or "") if len(t) > 1]
    expanded = set(raw)
    for t in raw:
        if t in SYNONYMS:
            for syn in SYNONYMS[t]:
                expanded.update(tokenize(syn))
    return list(expanded)


CY = "\033[38;2;100;220;230m"
WH = "\033[38;2;230;230;240m"
GY = "\033[38;2;130;135;150m"
R = "\033[0m"


def ask(kb, question, top_k=5):
    print()
    print(f"  {'=' * 58}")
    print(f"  ❓ {question}")
    print(f"  {'=' * 58}")
    print()

    print(f"  بارگذاری...", end="", flush=True)
    rows = kb.conn.execute(
        """SELECT hash, title, url, content FROM resources
           WHERE content IS NOT NULL AND length(content) > 200
           LIMIT 500"""
    ).fetchall()

    docs = []
    for h, title, url, content in rows:
        for chunk in smart_chunk(content):
            docs.append((chunk, url, title))
    print(f" {len(docs)} chunk")

    if not docs:
        print("  ✗ چیزی نیست")
        return

    print(f"  ساخت ایندکس...", end="", flush=True)
    idx = Index().build(docs)
    print(f" vocab {len(idx.vocab)}")

    expanded = expand_query(question)
    print(f"  Expand: {len(expanded)} توکن")

    vec_results = idx.query(question, top_k=20)

    avg_len = sum(len(tokenize(d[0])) for d in docs) / max(len(docs), 1)
    q_toks = tokenize(question)
    bm25_results = []
    for text, url, title in docs:
        toks = tokenize(text)
        s = bm25_score(q_toks, toks, avg_len)
        if s > 0:
            bm25_results.append((s, {"text": text, "url": url, "title": title}))
    bm25_results.sort(key=lambda x: -x[0])
    bm25_results = bm25_results[:20]

    fused = rrf([vec_results, bm25_results], q_tokens=q_toks)

    print()
    # ───────── نمایش ─────────
    print()
    print(f"  {WH}{'─' * 56}{R}")
    print(f"  {CY}پاسخ:{R}")
    print()

    shown = 0
    seen_urls = set()
    snippets = []
    for score, item in fused:
        if item["url"] in seen_urls:
            continue
        seen_urls.add(item["url"])
        snippets.append((score, item))
        shown += 1
        if shown >= top_k:
            break

    if not snippets:
        print(f"  ✗ چیزی پیدا نشد")
        return

    # پاسخ ترکیبی — دو تکه اول
    for i, (score, item) in enumerate(snippets[:2], 1):
        text = item["text"][:400]
        print(f"  {CY}▸{R} {text}")
        print()

    # منابع با score
    print(f"  {WH}{'─' * 56}{R}")
    print(f"  {CY}منابع:{R}")
    print()
    for i, (score, item) in enumerate(snippets, 1):
        title = item["title"][:55]
        url = item["url"]
        print(f"  {CY}[{i}]{R} {WH}{title}{R}")
        print(f"      {YL}score: {score:.4f}{R}")
        print(f"      {GY}{url}{R}")
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

