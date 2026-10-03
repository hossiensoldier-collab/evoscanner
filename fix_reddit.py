#!/usr/bin/env python3
"""جایگزینی Reddit با Hacker News در evoscanner_v2.py"""
from pathlib import Path

src = Path("evoscanner_v2.py")
code = src.read_text()

old_reddit = '''def reddit(q, n=5):
    """Reddit JSON API — بدون کلید"""
    url = "https://www.reddit.com/search.json?" + urllib.parse.urlencode({
        "q": f"{q} subreddit:Python", "sort": "top",
        "t": "year", "limit": n})
    try:
        data = json.loads(get(url))
        out = []
        for it in data.get("data", {}).get("children", []):
            d = it["data"]
            out.append({
                "url": f"https://reddit.com{d['permalink']}",
                "title": d["title"],
                "content": (d.get("selftext") or "")[:500],
                "source": "reddit",
                "score": min(d.get("score", 0) / 1000, 1.0),
                "tags": f"r/{d['subreddit']}"})
        return out
    except Exception as e:
        print(f"  ! reddit: {e}"); return []'''

new_hn = '''def hackernews(q, n=5):
    """Hacker News API — بدون کلید، پایدار"""
    url = "https://hn.algolia.com/api/v1/search?" + urllib.parse.urlencode({
        "query": f"python {q}", "tags": "story",
        "numericFilters": "points>20", "hitsPerPage": n})
    try:
        data = json.loads(get(url))
        out = []
        for it in data.get("hits", []):
            out.append({
                "url": it.get("url") or f"https://news.ycombinator.com/item?id={it['objectID']}",
                "title": it.get("title", ""),
                "content": (it.get("story_text") or "")[:500],
                "source": "hackernews",
                "score": min(it.get("points", 0) / 500, 1.0),
                "tags": "hn,python"})
        return out
    except Exception as e:
        print(f"  ! hackernews: {e}"); return []'''

if old_reddit in code:
    code = code.replace(old_reddit, new_hn)
    code = code.replace('("reddit", reddit),', '("hackernews", hackernews),')
    src.write_text(code)
    print("✓ Reddit با Hacker News جایگزین شد")
else:
    print("! الگوی Reddit یافت نشد — شاید از قبل تغییر کرده")
