"""کشف دسته جدید با k-means روی TF-IDF — بدون sklearn"""
import math, random, re
from collections import Counter

STOP = set("""
the a an and or of in on to for with is are was were be been this that
it as at by if not my we you can will have has had do does did but from
how what when where which who why read write run make see also more less
very example code file files name main test tests data version using used

https http www com org io github gitlab pypi npm img image images badge
badges shields shield svg png jpg jpeg gif readme license mit apache
install pip setup build docs documentation guide tutorial reference
api apis support user users project projects library libraries package
packages python3 py3 pip3 json yaml toml markdown rst txt md html css
js javascript node npm docker kubernetes cli gui ui ux web site server
client side backend frontend cloud host hosting service services
issue issues pr prs pull request requests commit commits branch
release releases changelog contribute contributing contribution
href src alt title target rel class style width height center align
img svg png jpg jpeg gif latest master main dev div span body html head
logo assets raw icon favicon demo screenshot preview thumb thumbnail
pywinauto seleniumbase connexion splinter reflex dowhy aiortc jittor
quot its these those other same different new old first last next prev
img svg png jpg gif latest master main dev none all any makefile
uses name id data value text link href srcset sizes loading
""".split())

TOK = re.compile(r'[a-zA-Z][a-zA-Z0-9_\-]{2,25}')



def clean_html(text):
    """پاکسازی HTML برای tokenize بهتر"""
    if not text:
        return ""
    import re as _re
    # حذف بلوک‌های کد
    text = _re.sub(r'```[\s\S]*?```', ' ', text)
    # حذف inline code
    text = _re.sub(r'`[^`]+`', ' ', text)
    # حذف تگ‌های HTML
    text = _re.sub(r'<[^>]+>', ' ', text)
    # حذف تصاویر markdown
    text = _re.sub(r'!\[[^\]]*\]\([^)]*\)', ' ', text)
    # حذف لینک‌های markdown
    text = _re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # حذف URL
    text = _re.sub(r'https?://\S+', ' ', text)
    # حذف entityها
    text = _re.sub(r'&[a-z]+;', ' ', text)
    # حذف نمادهای تکراری
    text = _re.sub(r'[=|\-]{3,}', ' ', text)
    return text


def tokenize(text):
    return [t.lower() for t in TOK.findall(text or "")
            if t.lower() not in STOP]


def build_tfidf(docs, min_df=3, max_df_ratio=0.8):
    """ساخت بردارهای TF-IDF نرمال"""
    doc_tokens = [tokenize(clean_html(d[2])) for d in docs]
    df = Counter()
    for tks in doc_tokens:
        for w in set(tks):
            df[w] += 1
    N = len(docs)
    vocab = [w for w, c in df.items()
             if c >= min_df and c < N * max_df_ratio]
    idx = {w: i for i, w in enumerate(vocab)}

    vectors = []
    for tks in doc_tokens:
        tf = Counter(tks)
        vec = [0.0] * len(vocab)
        for w, f in tf.items():
            if w in idx:
                idf = math.log(N / df[w])
                vec[idx[w]] = (1 + math.log(f)) * idf
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        vectors.append([v / norm for v in vec])
    return vectors, vocab, df, doc_tokens


def kmeans(vectors, k=6, iters=15, seed=42):
    """k-means ساده با cosine (dot)"""
    random.seed(seed)
    if len(vectors) < k:
        k = max(2, len(vectors) // 3)
    centroids = random.sample(vectors, k)
    assignments = [0] * len(vectors)

    for _ in range(iters):
        new_assign = []
        for vec in vectors:
            sims = [sum(a * b for a, b in zip(vec, c)) for c in centroids]
            new_assign.append(sims.index(max(sims)))
        if new_assign == assignments:
            break
        assignments = new_assign
        for ci in range(k):
            members = [vectors[i] for i, a in enumerate(assignments) if a == ci]
            if not members:
                continue
            nc = [0.0] * len(vectors[0])
            for m in members:
                for i, v in enumerate(m):
                    nc[i] += v
            norm = math.sqrt(sum(v * v for v in nc)) or 1.0
            centroids[ci] = [v / norm for v in nc]
    return assignments, k


def discover(kb, k=6, min_size=8):
    """کشف کلاسترها و پیشنهاد نام دسته"""
    rows = kb.conn.execute(
        "SELECT hash, title, content, category FROM resources "
        "WHERE content IS NOT NULL AND length(content) > 200"
    ).fetchall()
    docs = [(h, t, ((t or "") + " " + (c or ""))[:2000], cat)
            for h, t, c, cat in rows]
    if len(docs) < 20:
        print("  ✗ منابع کافی نیست (حداقل ۲۰)")
        return []

    vectors, vocab, df, doc_tokens = build_tfidf(docs)
    if not vocab:
        print("  ✗ vocabulary خالی")
        return []

    assign, k = kmeans(vectors, k=k)

    clusters = {}
    for i, ci in enumerate(assign):
        clusters.setdefault(ci, []).append(i)

    # دسته‌های موجود
    existing = set(d[3] for d in docs)

    print(f"\n🔬 کشف دسته — {len(clusters)} کلاستر روی {len(docs)} منبع")
    print("═" * 62)

    proposals = []
    for ci, members in sorted(clusters.items(), key=lambda x: -len(x[1])):
        if len(members) < min_size:
            continue

        # کلمات برتر
        all_toks = Counter()
        for mi in members:
            all_toks.update(doc_tokens[mi])
        top_terms = [w for w, _ in all_toks.most_common(8)]

        # دسته غالب
        cats_in = Counter(docs[mi][3] for mi in members)
        dom, dom_n = cats_in.most_common(1)[0]
        purity = dom_n / len(members)

        # نام پیشنهادی
        name_terms = [t for t in top_terms if len(t) > 3][:3]
        proposed = "_".join(name_terms) if name_terms else f"cluster_{ci}"

        proposals.append({
            "id": ci,
            "size": len(members),
            "top_terms": top_terms[:6],
            "dominant": dom,
            "purity": purity,
            "proposed_name": proposed,
            "samples": [docs[mi][1] for mi in members[:3]],
        })

    # نمایش
    for p in proposals:
        flag = "✓" if p["purity"] > 0.7 else "?"
        print(f"\n{flag} کلاستر #{p['id']} — {p['size']} منبع "
              f"(غلبه: {p['dominant']} — {p['purity']:.0%})")
        print(f"   کلمات: {', '.join(p['top_terms'])}")
        print(f"   نام پیشنهادی: {p['proposed_name']}")
        print(f"   نمونه‌ها:")
        for s in p["samples"]:
            print(f"     • {s[:60]}")
        if p["purity"] < 0.7:
            print(f"   ⚠ کلاستر جدید بالقوه!")

    new_candidates = [p for p in proposals if p["purity"] < 0.7 and p["size"] >= min_size]
    if new_candidates:
        print(f"\n🎯 {len(new_candidates)} کلاستر بالقوه‌ی جدید:")
        for p in new_candidates:
            print(f"   • {p['proposed_name']}  ({p['size']} منبع)")

    return proposals


def propose_cats(proposals):
    """فقط نام دسته‌های جدید را برگردان"""
    return [p["proposed_name"] for p in proposals
            if p["purity"] < 0.7 and p["size"] >= 8]

