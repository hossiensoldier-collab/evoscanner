#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dashboard.py — داشبورد وب جامع EvoScanner"""
import json, sqlite3, socket, subprocess, sys, os
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from datetime import datetime

HOME = Path.home()
EVO = HOME / "evoscanner"

HTML = r'''<!DOCTYPE html><html dir="rtl" lang="fa"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>EvoScanner Dashboard</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='85' font-size='90' fill='%2364dce6'>◆</text></svg>">
<style>
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
:root{--bg:#080c12;--card:#111720;--card2:#182130;--bd:#232c38;--txt:#c8d0dc;--dim:#8a94a3;
--accent:#64dce6;--green:#78e696;--red:#ff6e6e;--yellow:#ffd750;--purple:#b48cff;--blue:#5aa3ff;--pink:#ff8cc8}
body{margin:0;font-family:-apple-system,'Segoe UI',Roboto,sans-serif;background:var(--bg);color:var(--txt);font-size:14px;padding-bottom:70px}
.top{background:linear-gradient(135deg,#0f1620,#1a2535);padding:14px 16px;border-bottom:2px solid var(--accent);position:sticky;top:0;z-index:100;box-shadow:0 2px 12px rgba(0,0,0,.5)}
h1{margin:0;color:var(--accent);font-size:19px;display:flex;align-items:center;gap:8px;font-weight:600}
h1 .badge{background:var(--accent);color:#080c12;padding:2px 8px;border-radius:12px;font-size:10px;margin-right:auto}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-top:10px;font-size:10px;text-align:center}
.stat{background:var(--card);border:1px solid var(--bd);border-radius:8px;padding:6px 2px}
.stat b{display:block;color:var(--green);font-size:15px;margin-bottom:1px;font-weight:700}
.stat span{color:var(--dim)}
.grid{padding:12px;display:grid;grid-template-columns:repeat(2,1fr);gap:8px}
.grid.g3{grid-template-columns:repeat(3,1fr)}
.card{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:14px 10px;text-align:center;cursor:pointer;transition:all .15s;user-select:none}
.card:active{transform:scale(.95);background:var(--card2)}
.card .icon{font-size:22px;margin-bottom:4px}
.card .name{font-size:12px;font-weight:600;color:var(--txt)}
.card .sub{font-size:10px;color:var(--dim);margin-top:2px}
.card.c1{border-color:#64dce6} .card.c1 .name{color:var(--accent)}
.card.c2{border-color:#78e696} .card.c2 .name{color:var(--green)}
.card.c3{border-color:#ffd750} .card.c3 .name{color:var(--yellow)}
.card.c4{border-color:#b48cff} .card.c4 .name{color:var(--purple)}
.card.c5{border-color:#ff6e6e} .card.c5 .name{color:var(--red)}
.card.c6{border-color:#5aa3ff} .card.c6 .name{color:var(--blue)}
.card.c7{border-color:#ff8cc8} .card.c7 .name{color:var(--pink)}
.section{padding:0 12px;margin-bottom:8px}
.section h2{font-size:13px;color:var(--purple);margin:14px 0 8px;font-weight:600;display:flex;align-items:center;gap:6px}
.section h2::before{content:"◆";color:var(--accent);font-size:9px}
.modal{display:none;position:fixed;inset:0;background:rgba(0,0,0,.85);z-index:1000;padding:14px;overflow-y:auto}
.modal.on{display:block}
.modal-box{background:var(--card);border:1px solid var(--accent);border-radius:14px;max-width:600px;margin:0 auto;overflow:hidden}
.modal-head{padding:14px;border-bottom:1px solid var(--bd);display:flex;align-items:center;justify-content:space-between;background:linear-gradient(135deg,#0f1620,#1a2535)}
.modal-head h3{margin:0;color:var(--accent);font-size:16px}
.modal-head .close{background:var(--red);color:#fff;border:none;width:32px;height:32px;border-radius:50%;font-size:18px;cursor:pointer;font-weight:bold}
.modal-body{padding:16px}
input,textarea{width:100%;padding:12px;background:var(--bg);color:var(--txt);border:1px solid var(--bd);border-radius:10px;font-size:15px;margin-bottom:10px;font-family:inherit}
input:focus,textarea:focus{outline:none;border-color:var(--accent)}
button.btn{padding:12px 18px;background:var(--accent);color:#080c12;border:none;border-radius:10px;font-weight:600;font-size:14px;cursor:pointer;font-family:inherit;transition:transform .1s}
button.btn:active{transform:scale(.96)}
button.btn.g{background:var(--green)} button.btn.p{background:var(--purple);color:#fff}
button.btn.r{background:var(--red);color:#fff} button.btn.y{background:var(--yellow)}
.row{display:flex;gap:8px;flex-wrap:wrap}
.row button{flex:1;min-width:100px}
pre{background:var(--bg);padding:12px;border-radius:10px;white-space:pre-wrap;word-wrap:break-word;font-size:12px;border:1px solid var(--bd);max-height:55vh;overflow-y:auto;font-family:'SF Mono',Consolas,monospace;line-height:1.5}
pre.ok{border-color:var(--green)}
pre.err{border-color:var(--red)}
.nav{position:fixed;bottom:0;left:0;right:0;background:var(--card);border-top:1px solid var(--bd);display:grid;grid-template-columns:repeat(4,1fr);z-index:50;padding:6px 4px;box-shadow:0 -2px 12px rgba(0,0,0,.4)}
.nav div{padding:8px 4px;text-align:center;font-size:10px;color:var(--dim);cursor:pointer;border-radius:8px;transition:all .2s}
.nav div.on{color:var(--accent);background:var(--card2)}
.nav div .icon{font-size:18px;display:block;margin-bottom:2px}
.page{display:none}
.page.on{display:block;animation:fade .2s}
@keyframes fade{from{opacity:0}to{opacity:1}}
.spin{display:inline-block;width:12px;height:12px;border:2px solid var(--bd);border-top-color:var(--accent);border-radius:50%;animation:sp .6s linear infinite;margin-left:6px;vertical-align:middle}
@keyframes sp{to{transform:rotate(360deg)}}
.toast{position:fixed;bottom:80px;left:50%;transform:translateX(-50%);background:var(--green);color:#080c12;padding:10px 20px;border-radius:20px;font-weight:600;font-size:13px;z-index:2000;opacity:0;transition:opacity .3s}
.toast.on{opacity:1}
</style></head><body>

<div class="top">
  <h1>◆ EvoScanner <span class="badge" id="ver">v10</span></h1>
  <div class="stats" id="stats"><div class="stat">...</div></div>
</div>

<!-- صفحه اصلی -->
<div class="page on" id="p-home">
  <div class="section">
    <h2>عملیات اصلی</h2>
    <div class="grid">
      <div class="card c1" onclick="openModal('ask')"><div class="icon">🎯</div><div class="name">ASK</div><div class="sub">پرسش</div></div>
      <div class="card c3" onclick="openModal('get')"><div class="icon">📥</div><div class="name">GET</div><div class="sub">جذب منابع</div></div>
      <div class="card c2" onclick="openModal('learn')"><div class="icon">🎓</div><div class="name">LEARN</div><div class="sub">یادگیری</div></div>
      <div class="card c4" onclick="openModal('evolve')"><div class="icon">🧬</div><div class="name">EVOLVE</div><div class="sub">خودارتقایی</div></div>
      <div class="card c6" onclick="openModal('graph')"><div class="icon">📊</div><div class="name">GRAPH</div><div class="sub">گراف</div></div>
      <div class="card c5" onclick="openModal('search')"><div class="icon">🔍</div><div class="name">SEARCH</div><div class="sub">جستجو</div></div>
    </div>
  </div>

  <div class="section">
    <h2>موتورها</h2>
    <div class="grid g3">
      <div class="card c7" onclick="run('due')"><div class="icon">🧠</div><div class="name">DUE</div></div>
      <div class="card c7" onclick="run('forge')"><div class="icon">⚙️</div><div class="name">FORGE</div></div>
      <div class="card c7" onclick="run('sacred')"><div class="icon">✨</div><div class="name">SACRED</div></div>
    </div>
  </div>

  <div class="section">
    <h2>ابزارها</h2>
    <div class="grid g3">
      <div class="card c2" onclick="run('health')"><div class="icon">🏥</div><div class="name">HEALTH</div></div>
      <div class="card c3" onclick="run('test')"><div class="icon">🧪</div><div class="name">TEST</div></div>
      <div class="card c5" onclick="run('autoheal')"><div class="icon">🩺</div><div class="name">HEAL</div></div>
    </div>
  </div>

  <div class="section">
    <h2>دیتا</h2>
    <div class="grid">
      <div class="card c1" onclick="run('kb')"><div class="icon">💾</div><div class="name">KB</div><div class="sub">دیتابیس</div></div>
      <div class="card c6" onclick="run('history')"><div class="icon">📚</div><div class="name">HISTORY</div><div class="sub">تاریخچه</div></div>
    </div>
  </div>
</div>

<!-- صفحه CORTEX -->
<div class="page" id="p-cortex">
  <div class="section">
    <h2>CORTEX — ایجنت خودمختار</h2>
    <input id="goal" placeholder="🎯 هدف: تحلیل پروژه، یادگیری asyncio، بهبود پنل...">
    <div class="row">
      <button class="btn p" onclick="runCortex()">🤖 اجرا</button>
      <button class="btn y" onclick="cortexHistory()">📚 تاریخچه</button>
    </div>
    <pre id="cortex_out" style="margin-top:12px">آماده...</pre>
  </div>
</div>

<!-- صفحه جستجو -->
<div class="page" id="p-search">
  <div class="section">
    <h2>جستجو در دیتابیس</h2>
    <input id="q" placeholder="مثلاً: asyncio, pandas...">
    <div class="row">
      <button class="btn" onclick="doSearch()">🔍 جستجو</button>
      <button class="btn g" onclick="randomPick()">🎲 شانسی</button>
    </div>
    <pre id="search_out" style="margin-top:12px">آماده...</pre>
  </div>
</div>

<!-- صفحه لاگ -->
<div class="page" id="p-logs">
  <div class="section">
    <h2>لاگ‌های سیستم</h2>
    <div class="row">
      <button class="btn" onclick="loadLog('cortex')">CORTEX</button>
      <button class="btn y" onclick="loadLog('selfcare')">SELF-CARE</button>
      <button class="btn g" onclick="loadLog('selfrun')">SELFRUN</button>
    </div>
    <pre id="log_out" style="margin-top:12px">آماده...</pre>
  </div>
</div>

<!-- Modal عمومی -->
<div class="modal" id="modal">
  <div class="modal-box">
    <div class="modal-head">
      <h3 id="modal-title">عنوان</h3>
      <button class="close" onclick="closeModal()">×</button>
    </div>
    <div class="modal-body">
      <div id="modal-input-wrap"></div>
      <div class="row" id="modal-btns"></div>
      <pre id="modal_out" style="margin-top:12px">آماده...</pre>
    </div>
  </div>
</div>

<!-- نویگیشن پایین -->
<div class="nav">
  <div class="on" onclick="go('home',this)"><span class="icon">🏠</span>خانه</div>
  <div onclick="go('cortex',this)"><span class="icon">🤖</span>CORTEX</div>
  <div onclick="go('search',this)"><span class="icon">🔍</span>جستجو</div>
  <div onclick="go('logs',this)"><span class="icon">📜</span>لاگ</div>
</div>

<div class="toast" id="toast">✓ انجام شد</div>

<script>
const $ = s => document.querySelector(s);
const $$ = s => document.querySelectorAll(s);

function toast(msg){
  const t = $('#toast');
  t.textContent = msg;
  t.classList.add('on');
  setTimeout(()=>t.classList.remove('on'), 1500);
}

function go(page, el){
  $$('.page').forEach(p=>p.classList.remove('on'));
  $('#p-'+page).classList.add('on');
  $$('.nav div').forEach(d=>d.classList.remove('on'));
  el.classList.add('on');
}

async function api(path, body){
  const r = await fetch(path, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body||{})});
  return await r.text();
}

function show(el, text, cls){
  el.textContent = text;
  el.className = cls || '';
}

// Modal برای عملیات نیازمند ورودی
function openModal(type){
  const m = $('#modal');
  const title = $('#modal-title');
  const inp = $('#modal-input-wrap');
  const btns = $('#modal-btns');
  const out = $('#modal_out');

  const configs = {
    ask:    {t:"🎯 ASK — سؤال", ph:"سؤالت رو بنویس...", ep:"/api/ask"},
    get:    {t:"📥 GET — جذب منابع", ph:"کلیدواژه (خالی = چرخه)", ep:"/api/get"},
    learn:  {t:"🎓 LEARN — یادگیری", ph:"موضوع", ep:"/api/learn"},
    evolve: {t:"🧬 EVOLVE — خودارتقایی", ph:"", ep:"/api/evolve"},
    graph:  {t:"📊 GRAPH — گراف", ph:"", ep:"/api/graph"},
    search: {t:"🔍 SEARCH — جستجو", ph:"کلیدواژه", ep:"/api/search"},
  };
  const c = configs[type];
  title.textContent = c.t;
  inp.innerHTML = c.ph ? `<input id="modal_q" placeholder="${c.ph}">` : '';
  btns.innerHTML = `<button class="btn" onclick="doModal('${c.ep}')">اجرا</button>`;
  show(out, 'آماده...', '');
  m.classList.add('on');
}

function closeModal(){ $('#modal').classList.remove('on'); }

async function doModal(ep){
  const out = $('#modal_out');
  const q = $('#modal_q') ? $('#modal_q').value.trim() : '';
  show(out, '⏳ در حال اجرا...', '');
  const res = await api(ep, {q:q});
  show(out, res, 'ok');
}

async function run(action){
  const m = $('#modal');
  $('#modal-title').textContent = '⏳ در حال اجرا...';
  $('#modal-input-wrap').innerHTML = '';
  $('#modal-btns').innerHTML = '';
  show($('#modal_out'), '⏳ ...', '');
  m.classList.add('on');
  const res = await api('/api/' + action);
  show($('#modal_out'), res, 'ok');
}

async function doSearch(){
  const q = $('#q').value.trim();
  if(!q) return;
  const out = $('#search_out');
  show(out, '⏳ ...', '');
  show(out, await api('/api/search', {q:q}), 'ok');
}

async function randomPick(){
  const out = $('#search_out');
  show(out, '⏳ ...', '');
  show(out, await api('/api/random'), 'ok');
}

async function runCortex(){
  const g = $('#goal').value.trim();
  if(!g) { toast('هدف رو وارد کن'); return; }
  const out = $('#cortex_out');
  show(out, '⏳ اجرای CORTEX...\n', '');
  show(out, await api('/api/cortex', {goal:g}), 'ok');
}

async function cortexHistory(){
  const out = $('#cortex_out');
  show(out, '⏳ ...', '');
  show(out, await api('/api/cortex_history'), 'ok');
}

async function loadLog(name){
  const out = $('#log_out');
  show(out, '⏳ ...', '');
  show(out, await api('/api/log/' + name), 'ok');
}

// آمار اولیه
(async () => {
  const r = await fetch('/api/stats');
  const txt = await r.text();
  $('#stats').innerHTML = txt;
})();

// آپدیت آمار هر ۱۰ ثانیه
setInterval(async () => {
  const r = await fetch('/api/stats');
  $('#stats').innerHTML = await r.text();
}, 10000);

// ESC برای بستن modal
document.addEventListener('keydown', e => { if(e.key === 'Escape') closeModal(); });
</script></body></html>'''

def find_db():
    for p in [EVO/"knowledge.db", HOME/"knowledgeforge"/"knowledge.db"]:
        if p.exists(): return p
    return None

def run_script(name, timeout=60):
    p = EVO / name
    if not p.exists(): return f"فایل {name} نیست"
    try:
        r = subprocess.run(["python", str(p)], cwd=str(EVO), capture_output=True, text=True, timeout=timeout)
        out = (r.stdout or "") + (r.stderr or "")
        return out[-3000:] if out else "(خروجی خالی)"
    except subprocess.TimeoutExpired: return "⏱ timeout"
    except Exception as e: return f"خطا: {e}"

def run_py_inline(code, timeout=60):
    try:
        r = subprocess.run(["python","-c",code], cwd=str(EVO), capture_output=True, text=True, timeout=timeout)
        out = (r.stdout or "") + (r.stderr or "")
        return out[-3000:] if out else "(خالی)"
    except subprocess.TimeoutExpired: return "⏱ timeout"
    except Exception as e: return f"خطا: {e}"

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def do_GET(self):
        if self.path == "/":
            self._send(HTML, "text/html")
        elif self.path == "/api/stats":
            self._send(self._stats())
        else:
            self.send_response(404); self.end_headers()

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        try: data = json.loads(self.rfile.read(n) or b"{}")
        except: data = {}
        q = data.get("q","")
        routes = {
            "/api/ask":       lambda: self._ask(q),
            "/api/search":    lambda: self._search(q),
            "/api/random":    lambda: self._random(),
            "/api/get":       lambda: "📥 GET (شبیه‌سازی) — از پنل استفاده کن",
            "/api/learn":     lambda: self._learn(q),
            "/api/evolve":    lambda: "🧬 EVOLVE — از پنل استفاده کن",
            "/api/graph":     lambda: self._graph(),
            "/api/kb":        lambda: self._kb(),
            "/api/history":   lambda: self._history(),
            "/api/health":    lambda: run_script("health.py", timeout=10),
            "/api/test":      lambda: run_script("panel_test.py", timeout=180),
            "/api/autoheal":  lambda: self._autoheal(),
            "/api/due":       lambda: self._due(),
            "/api/forge":     lambda: self._forge(),
            "/api/sacred":    lambda: self._sacred(),
            "/api/cortex":    lambda: self._cortex(q),
            "/api/cortex_history": lambda: self._cortex_history(),
        }
        if self.path.startswith("/api/log/"):
            name = self.path.split("/")[-1]
            return self._send(self._log(name))
        fn = routes.get(self.path)
        if fn: self._send(fn())
        else: self.send_response(404); self.end_headers()

    def _send(self, t, ct="text/plain"):
        self.send_response(200)
        self.send_header("Content-Type", f"{ct}; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(t.encode("utf-8"))

    def _stats(self):
        parts = []
        labels = [("resources","منابع","evoscanner"),("techniques","تکنیک","evoscanner"),
                  ("snippets","کد","evoscanner"),("nodes","نود","forge")]
        for t, label, src in labels:
            n = "—"
            try:
                db = EVO/"knowledge.db" if src=="evoscanner" else HOME/"knowledgeforge"/"knowledge.db"
                if db.exists():
                    c = sqlite3.connect(db)
                    n = c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            except: pass
            parts.append(f'<div class="stat"><b>{n}</b><span>{label}</span></div>')
        return "".join(parts)

    def _ask(self, q):
        if not q: return "سؤال خالی"
        db = find_db()
        if not db: return "دیتابیس نیست"
        try:
            c = sqlite3.connect(db)
            rows = c.execute("SELECT title,url,source FROM resources WHERE title LIKE ? OR content LIKE ? ORDER BY score DESC LIMIT 10", (f"%{q}%",f"%{q}%")).fetchall()
            if not rows: return f"چیزی برای «{q}» نیست"
            return f"✅ {len(rows)} نتیجه:\n\n" + "\n".join(f"● {t}\n  📌 {s}\n  🔗 {u}" for t,u,s in rows)
        except Exception as e: return f"خطا: {e}"

    def _search(self, q): return self._ask(q)

    def _random(self):
        db = find_db()
        if not db: return "دیتابیس نیست"
        try:
            c = sqlite3.connect(db)
            rows = c.execute("SELECT title,url,source FROM resources ORDER BY RANDOM() LIMIT 5").fetchall()
            return "🎲 ۵ منبع شانسی:\n\n" + "\n".join(f"● {t}\n  📌 {s}\n  🔗 {u}" for t,u,s in rows)
        except Exception as e: return f"خطا: {e}"

    def _learn(self, q):
        if not q: return "موضوع خالی"
        return run_py_inline(f"import sys; sys.path.insert(0,'.'); import learn; learn.print_learning_path(None,'{q}')", timeout=30)

    def _graph(self):
        db = HOME/"knowledgeforge"/"knowledge.db"
        if not db.exists(): db = find_db()
        if not db: return "دیتابیس نیست"
        try:
            c = sqlite3.connect(db)
            n = c.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
            e = c.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
            return f"📊 گراف:\n  nodes: {n:,}\n  edges: {e:,}\n\nاز پنل gزینه 7 برای کاوش تعاملی استفاده کن"
        except Exception as ex: return f"خطا: {ex}"

    def _kb(self):
        db = find_db()
        if not db: return "دیتابیس نیست"
        try:
            c = sqlite3.connect(db)
            out = [f"💾 {db.name} — {db.stat().st_size:,}B\n"]
            for (t,) in c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
                try: n = c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                except: n = "?"
                out.append(f"  {t:25} {n}")
            return "\n".join(out)
        except Exception as e: return f"خطا: {e}"

    def _history(self):
        f = EVO / "panel_history.json"
        if not f.exists(): return "تاریخچه نیست"
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            items = d if isinstance(d, list) else d.get("items", [])
            out = [f"📚 {len(items)} مورد اخیر:\n"]
            for it in items[-20:]:
                out.append(f"  ● {it.get('query') or it.get('cmd') or it}")
            return "\n".join(out)
        except: return "خطا در خواندن"

    def _autoheal(self):
        return run_py_inline("import sys; sys.path.insert(0,'.'); import autoheal; iss = autoheal.diagnose(__import__('pathlib').Path('panel.py')); print('✓ سالم' if not iss else f'{len(iss)} مشکل')", timeout=15)

    def _due(self):
        return run_py_inline(f"import sys,subprocess; r = subprocess.run(['python',r'{HOME}/due/due.py','analyze','panel.py'], capture_output=True, text=True, timeout=20); print(r.stdout[-2000:] if r.stdout else r.stderr[-500:])", timeout=25)

    def _forge(self):
        return run_py_inline(f"import sys,subprocess; r = subprocess.run(['python',r'{HOME}/knowledgeforge/knowledgeforge.py'], capture_output=True, text=True, timeout=10); print((r.stdout or '')[-1500:])", timeout=15)

    def _sacred(self):
        return run_py_inline(f"import sys,subprocess; r = subprocess.run(['python',r'{HOME}/sacred/sacred.py','shapes'], capture_output=True, text=True, timeout=10); print((r.stdout or '')[-1500:])", timeout=15)

    def _cortex(self, goal):
        if not goal: return "هدف خالی"
        code = f'''
import sys
sys.path.insert(0, "{EVO}")
import cortex
state = cortex.perceive()
steps = cortex.plan("{goal}")
print(f"🎯 هدف: {goal}\\n")
print(f"PERCEIVE: منابع={{state['resources']}} نود={{state['nodes']}} یال={{state['edges']}} تکنیک={{state['techniques']}}\\n")
print("PLAN:")
for i,(n,d) in enumerate(steps,1): print(f"  {{i}}. {{n}} — {{d}}")
print()
print("ACT:")
results=[]
for n,d in steps:
    fn = cortex.ACT.get(n)
    if not fn: results.append(None); continue
    try: r = fn("{goal}", state)
    except Exception as e: r = f"خطا: {{e}}"
    results.append(r)
    s = str(r).split("\\n")[0][:100] if r else "(خالی)"
    print(f"  ▸ {{n}}: {{s}}")
print()
fb = cortex.reflect(steps, results)
print(f"REFLECT: {{fb['score']}}% ({{fb['ok']}}/{{fb['total']}})")
for n in fb["notes"]: print(f"  {{n}}")
mem = cortex.load_mem()
mem["sessions"].append({{"ts":"now","goal":"{goal}","score":fb["score"],"steps":[s[0] for s in steps]}})
for n,_ in steps:
    if n not in mem["skills"]: mem["skills"][n] = {{"used":0,"success":0}}
    mem["skills"][n]["used"] += 1
    if fb["score"] >= 60: mem["skills"][n]["success"] += 1
cortex.save_mem(mem)
'''
        return run_py_inline(code, timeout=120)

    def _cortex_history(self):
        f = EVO / "cortex_memory.json"
        if not f.exists(): return "حافظه خالی"
        try:
            mem = json.loads(f.read_text(encoding="utf-8"))
            out = [f"📚 {len(mem.get('sessions',[]))} session:\n"]
            for s in mem.get("sessions",[])[-12:]:
                bar = "█"*(s["score"]//10) + "░"*(10-s["score"]//10)
                out.append(f"  {bar} {s['score']:>3}%  {s['goal'][:45]}")
            out.append("\n🎓 Skills:")
            for n,v in sorted(mem.get("skills",{}).items(), key=lambda x:-x[1]["used"]):
                rate = int(100*v["success"]/max(v["used"],1))
                out.append(f"  {n:12} used={v['used']:>3}  {rate:>3}%")
            return "\n".join(out)
        except Exception as e: return f"خطا: {e}"

    def _log(self, name):
        p = EVO / f"{name}.log"
        if not p.exists(): return f"لاگ {name} نیست"
        try:
            lines = p.read_text(encoding="utf-8").splitlines()
            return f"📜 {name}.log ({len(lines)} خط):\n\n" + "\n".join(lines[-50:])
        except: return "خطا"

if __name__ == "__main__":
    port = 8090
    try: ip = socket.gethostbyname(socket.gethostname())
    except: ip = "localhost"
    print(f"\n  ◆ EvoScanner Dashboard")
    print(f"  → http://localhost:{port}")
    print(f"  → http://{ip}:{port}")
    print(f"\n  Ctrl+C برای خروج\n")
    HTTPServer(("0.0.0.0", port), H).serve_forever()
