"""رابط وب ساده با http.server استاندارد"""
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

HEAD = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>EvoScanner</title>
<style>
body{font-family:-apple-system,sans-serif;max-width:900px;margin:2em auto;
     padding:0 1em;background:#0d1117;color:#c9d1d9}
h1{color:#58a6ff}h2{color:#79c0ff;border-bottom:1px solid #30363d;padding-bottom:.3em}
input{width:70%;padding:.7em;background:#161b22;color:#c9d1d9;
      border:1px solid #30363d;border-radius:6px;font-size:1em}
button{padding:.7em 1.5em;background:#238636;color:#fff;border:0;
       border-radius:6px;font-size:1em;cursor:pointer}
button:hover{background:#2ea043}
.item{padding:.8em;margin:.5em 0;background:#161b22;
      border-left:3px solid #58a6ff;border-radius:4px}
.item a{color:#58a6ff;text-decoration:none;font-weight:bold}
.item a:hover{text-decoration:underline}
.src{font-size:.8em;color:#8b949e;background:#21262d;padding:.15em .5em;
     border-radius:10px;margin-right:.5em}
.score{font-size:.8em;color:#8b949e;float:right}
.cat-row{display:flex;align-items:center;gap:1em;margin:.3em 0}
.bar{height:14px;background:#238636;border-radius:7px;min-width:2px}
</style></head><body><h1>🔍 EvoScanner</h1>"""

TAIL = "</body></html>"


def serve(kb, evo, port=8080):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass

        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            qs = urllib.parse.parse_qs(parsed.query)
            q = qs.get("q", [""])[0]
            cat = qs.get("cat", [""])[0]

            html = [HEAD]
            html.append(
                '<form method="get" action="/">'
                f'<input name="q" value="{q}" placeholder="جستجو..." autofocus>'
                '<button>جستجو</button></form>'
            )

            cats = kb.categories_stats()
            html.append('<h2>دسته‌ها</h2>')
            max_n = max((c for _, c, _ in cats), default=1)
            for c, n, avg in cats:
                bar_w = int(n / max_n * 300)
                html.append(
                    f'<div class="cat-row">'
                    f'<a href="/?cat={c}" style="color:#79c0ff;'
                    f'text-decoration:none;width:100px">{c}</a>'
                    f'<div class="bar" style="width:{bar_w}px"></div>'
                    f'<span>{n} | ⌀ {avg:.2f}</span></div>'
                )

            if q:
                results = kb.search(q, 30)
                html.append(f'<h2>نتایج "{q}" ({len(results)})</h2>')
                for src_, title, url, score in results:
                    html.append(
                        f'<div class="item"><span class="src">{src_}</span>'
                        f'<a href="{url}" target="_blank">{title}</a>'
                        f'<span class="score">⭐ {score:.2f}</span></div>'
                    )
            elif cat:
                results = kb.by_category(cat, 50)
                html.append(f'<h2>دسته {cat} ({len(results)})</h2>')
                for src_, title, url, score in results:
                    html.append(
                        f'<div class="item"><span class="src">{src_}</span>'
                        f'<a href="{url}" target="_blank">{title}</a>'
                        f'<span class="score">⭐ {score:.2f}</span></div>'
                    )
            else:
                html.append(
                    f'<p style="color:#8b949e">کل: {kb.total()} '
                    f'| چرخه: {evo.state["cycle"]}</p>'
                )

            html.append(TAIL)
            body = "".join(html).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    print(f"\n🌐 سرور: http://localhost:{port}")
    print("   Ctrl+C برای توقف\n")
    try:
        HTTPServer(("", port), Handler).serve_forever()
    except KeyboardInterrupt:
        print("\n⏸ متوقف شد")
