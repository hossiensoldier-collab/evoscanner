#!/usr/bin/env python3
import json, sqlite3, socket
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

HOME = Path.home()

HTML = '''<!DOCTYPE html><html dir="rtl"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>EvoScanner</title>
<style>
body{font-family:monospace;background:#0a0e14;color:#c8d0dc;margin:0;padding:16px}
h1{color:#64dce6;font-size:20px;border-bottom:1px solid #2a3441;padding-bottom:8px}
.tab{display:inline-block;padding:8px 14px;background:#151b24;border:1px solid #2a3441;margin:2px;border-radius:6px;cursor:pointer;font-size:14px;color:#c8d0dc}
.tab.on{background:#1e2a38;color:#64dce6}
.sec{display:none;margin-top:16px}.sec.on{display:block}
input{width:100%;padding:12px;background:#151b24;color:#c8d0dc;border:1px solid #2a3441;border-radius:6px;font-size:16px;box-sizing:border-box;margin-bottom:8px}
button{padding:12px 24px;background:#64dce6;color:#0a0e14;border:none;border-radius:6px;font-weight:bold;font-size:14px;cursor:pointer}
pre{background:#151b24;padding:12px;border-radius:6px;white-space:pre-wrap;word-wrap:break-word;font-size:13px;border:1px solid #2a3441;min-height:40px}
.st{color:#78e696;font-size:12px;margin-bottom:12px}
</style></head><body>
<h1>◆ EvoScanner</h1>
<div id="stats" class="st">...</div>
<div>
<div class="tab on" onclick="show('ask',event)">پرسش</div>
<div class="tab" onclick="show('search',event)">جستجو</div>
<div class="tab" onclick="show('graph',event)">گراف</div>
<div class="tab" onclick="show('kb',event)">دانش</div>
</div>
<div id="ask" class="sec on">
<input id="q" placeholder="سؤالت رو بنویس...">
<button onclick="run('/api/ask','q','ask_out')">بپرس</button>
<pre id="ask_out"></pre>
</div>
<div id="search" class="sec">
<input id="s" placeholder="کلیدواژه...">
<button onclick="run('/api/search','s','search_out')">جستجو</button>
<pre id="search_out"></pre>
</div>
<div id="graph" class="sec">
<button onclick="hit('/api/graph','graph_out')">نمایش گراف</button>
<pre id="graph_out"></pre>
</div>
<div id="kb" class="sec">
<button onclick="hit('/api/kb','kb_out')">آمار دیتابیس</button>
<pre id="kb_out"></pre>
</div>
<script>
function show(id,e){document.querySelectorAll('.tab').forEach(t=>t.classList.remove('on'));document.querySelectorAll('.sec').forEach(s=>s.classList.remove('on'));document.getElementById(id).classList.add('on');e.target.classList.add('on');}
async function run(p,i,o){const v=document.getElementById(i).value;const r=await fetch(p,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({q:v})});document.getElementById(o).textContent=await r.text();}
async function hit(p,o){const r=await fetch(p,{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});document.getElementById(o).textContent=await r.text();}
fetch('/api/stats').then(r=>r.text()).then(t=>document.getElementById('stats').textContent=t);
</script></body></html>'''

def find_db():
    for p in [HOME/"evoscanner"/"knowledge.db", HOME/"knowledgeforge"/"knowledge.db"]:
        if p.exists(): return p
    return None

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def do_GET(self):
        if self.path == "/":
            self._send(HTML, "text/html")
        elif self.path == "/api/stats":
            db = find_db()
            if not db: self._send("بدون دیتابیس"); return
            try:
                c = sqlite3.connect(db)
                n = c.execute("SELECT COUNT(*) FROM resources").fetchone()[0]
                self._send(f"منابع: {n}  |  DB: {db}")
            except Exception as e:
                self._send(f"خطا: {e}")
        else:
            self.send_response(404); self.end_headers()

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        try: data = json.loads(self.rfile.read(n) or b"{}")
        except: data = {}
        if self.path in ("/api/ask", "/api/search"):
            self._send(self._query(data.get("q","")))
        elif self.path == "/api/graph":
            self._send(self._graph())
        elif self.path == "/api/kb":
            self._send(self._kb())
        else:
            self.send_response(404); self.end_headers()

    def _send(self, text, ct="text/plain"):
        self.send_response(200)
        self.send_header("Content-Type", f"{ct}; charset=utf-8")
        self.end_headers()
        self.wfile.write(text.encode())

    def _query(self, q):
        if not q: return "سؤال خالی"
        db = find_db()
        if not db: return "دیتابیس نیست"
        try:
            c = sqlite3.connect(db)
            rows = c.execute(
                "SELECT title, url, source FROM resources WHERE title LIKE ? OR content LIKE ? LIMIT 8",
                (f"%{q}%", f"%{q}%")
            ).fetchall()
            if not rows: return f"چیزی برای «{q}» نیست"
            out = [f"یافته‌ها ({len(rows)}):\n"]
            for t,u,s in rows:
                out.append(f"● {t or '?'}\n  [{s or '?'}]\n  {u or '?'}\n")
            return "\n".join(out)
        except Exception as e:
            return f"خطا: {e}"

    def _graph(self):
        db = find_db()
        if not db: return "دیتابیس نیست"
        try:
            c = sqlite3.connect(db)
            n = c.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
            e = c.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
            return f"nodes: {n}\nedges: {e}"
        except Exception as e:
            return f"گراف در دسترس نیست: {e}"

    def _kb(self):
        db = find_db()
        if not db: return "دیتابیس نیست"
        try:
            c = sqlite3.connect(db)
            out = []
            for (t,) in c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
                try: n = c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                except: n = "?"
                out.append(f"{t:25} {n}")
            return "\n".join(out)
        except Exception as e:
            return f"خطا: {e}"

if __name__ == "__main__":
    port = 8090
    try:
        ip = socket.gethostbyname(socket.gethostname())
    except:
        ip = "localhost"
    print(f"\n  ◆ EvoScanner WebApp")
    print(f"  → http://localhost:{port}")
    print(f"  → http://{ip}:{port}")
    print(f"\n  Ctrl+C برای خروج\n")
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()
