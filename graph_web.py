"""رابط وب گراف — SVG interactive با force layout"""
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

BASE = Path.home() / "evoscanner"
GRAPH_FILE = BASE / "graph.json"


JUNK = {
    "build", "git", "none", "pip", "top", "data", "file", "files",
    "user", "users", "name", "value", "type", "text", "line", "list",
    "dict", "str", "int", "float", "bool", "true", "false", "null",
    "get", "set", "add", "new", "old", "run", "start", "end", "main",
    "core", "base", "test", "tests", "doc", "docs", "readme", "license",
    "python", "py", "lib", "app", "apps", "site", "page", "api", "apis",
    "code", "item", "items", "return", "class", "function", "method",
}


def load_graph(limit=200, min_weight=1):
    """بارگذاری گراف با فیلتر"""
    if not GRAPH_FILE.exists():
        return {"nodes": [], "edges": []}
    g = json.loads(GRAPH_FILE.read_text())
    raw_nodes = g.get("nodes", {})
    raw_edges = g.get("edges", {})
    cooc = g.get("cooc", {})

    # شمارش درجه هر نود
    degree = {}
    for key, w in raw_edges.items():
        a, b = key.split("\u2192", 1)
        degree[a] = degree.get(a, 0) + w
        degree[b] = degree.get(b, 0) + w

    # نودهای برتر (موجودیت‌های متصل)
    ents = []
    for k, v in raw_nodes.items():
        if v.get("type") != "entity":
            continue
        if k.startswith("cat:"):
            continue
        cnt = v.get("count", 0)
        deg = degree.get(k, 0)
        if cnt < 1:
            continue
        if k in JUNK or len(k) < 3:
            continue
        ents.append((k, cnt, deg))

    ents.sort(key=lambda x: -(x[1] + x[2]))
    top = ents[:limit]
    top_keys = {e[0] for e in top}

    # نودهای خروجی
    nodes_out = []
    for k, cnt, deg in top:
        info = raw_nodes[k]
        cats = info.get("cats", {})
        main_cat = max(cats, key=cats.get) if cats else "other"
        nodes_out.append({
            "id": k,
            "count": cnt,
            "degree": deg,
            "cat": main_cat,
        })

    # یال‌های co-occurrence (پرقوی‌تر)
    edges_out = []
    seen_pairs = set()
    for pair, w in cooc.items():
        if w < min_weight:
            continue
        a, b = pair.split("|", 1)
        if a not in top_keys or b not in top_keys:
            continue
        if a.startswith("cat:") or b.startswith("cat:"):
            continue
        key = tuple(sorted([a, b]))
        if key in seen_pairs:
            continue
        seen_pairs.add(key)
        edges_out.append({"source": a, "target": b, "weight": w})

    return {"nodes": nodes_out, "edges": edges_out}


HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>EvoScanner Graph</title>
<style>
* { box-sizing: border-box; }
body { margin:0; font-family:-apple-system,sans-serif;
       background:#0d1117; color:#c9d1d9; overflow:hidden; }
#header { position:fixed; top:0; left:0; right:0; height:48px;
          background:#161b22; border-bottom:1px solid #30363d;
          display:flex; align-items:center; padding:0 1.2em; z-index:10; }
#header h1 { color:#58a6ff; font-size:1em; margin:0; white-space:nowrap; }
#header input { padding:.4em .8em; background:#0d1117; color:#c9d1d9;
                border:1px solid #30363d; border-radius:6px; width:200px; }
#header button { padding:.4em 1em; background:#238636; color:#fff;
                 border:0; border-radius:6px; margin-left:.5em; cursor:pointer; }
#header button:hover { background:#2ea043; }
#stats { font-size:.85em; color:#8b949e; margin-left:1em; }
#canvas { width:100vw; height:100vh; display:block; cursor:grab; }
#canvas:active { cursor:grabbing; }
#info { position:fixed; top:60px; right:10px; width:min(280px, 80vw); max-height:70vh;
        background:#161b22; border:1px solid #30363d; border-radius:8px;
        padding:1em; overflow-y:auto; font-size:.85em;
        display:none; z-index:10; }
#info h3 { color:#58a6ff; margin:0 0 .5em 0; font-size:1em; }
#info .row { padding:.3em 0; border-bottom:1px solid #21262d; }
#info .row a { color:#79c0ff; text-decoration:none; }
#info .row a:hover { text-decoration:underline; }
#info .w { color:#8b949e; font-size:.8em; float:right; }
#info .close { float:right; color:#f85149; cursor:pointer; font-size:1.2em; }
#legend { position:fixed; bottom:10px; left:10px; background:#161b22;
          border:1px solid #30363d; border-radius:8px; padding:.6em 1em;
          font-size:.8em; max-width:300px; }
#legend .item { display:inline-block; margin:.15em .5em .15em 0; }
#legend .dot { display:inline-block; width:10px; height:10px;
               border-radius:50%; margin-right:.3em; vertical-align:middle; }
</style></head><body>

<div id="header">
  <h1>🕸 EvoScanner Graph</h1>
  <input id="search" placeholder="جستجو...">
  <button onclick="doSearch()">برو</button>
  <button onclick="restart()" style="background:#6e7681">↻</button>
  <button onclick="restart()" style="background:#6e7681">↻</button>
  <span id="stats"></span>
</div>
<svg id="canvas"></svg>
<div id="info"><span class="close" onclick="closeInfo()">×</span><div id="infoBody"></div></div>
<div id="legend"></div>

<script>
const COLORS = {
  "web":        "#58a6ff",
  "async":      "#79c0ff",
  "ml-ai":      "#f85149",
  "data":       "#a371f7",
  "testing":    "#7ee787",
  "performance":"#ffa657",
  "typing":     "#ff7b72",
  "patterns":   "#d2a8ff",
  "packaging":  "#79c0ff",
  "parsing":    "#ffa657",
  "security":   "#f85149",
  "devops":     "#7ee787",
  "bots":       "#d2a8ff",
  "other":      "#8b949e"
};

let NODES = [], EDGES = [];
let svg, gZoom, gLinks, gNodes;
let sim;

async function load() {
  const r = await fetch("/api/graph");
  const data = await r.json();
  NODES = data.nodes.map((n, i) => ({...n, x: 0, y: 0, vx: 0, vy: 0, i}));
  EDGES = data.edges.map(e => ({...e}));
  document.getElementById("stats").textContent =
    NODES.length + " نود | " + EDGES.length + " یال";
  drawLegend();
  initSim();
  render();
}

function drawLegend() {
  const cats = new Set(NODES.map(n => n.cat));
  const legend = document.getElementById("legend");
  legend.innerHTML = [...cats].slice(0, 12).map(c =>
    `<span class="item"><span class="dot" style="background:${COLORS[c]||'#8b949e'}"></span>${c}</span>`
  ).join("");
}

function initSim() {
  const W = window.innerWidth, H = window.innerHeight;
  NODES.forEach(n => {
    n.x = W/2 + (Math.random()-0.5)*400;
    n.y = H/2 + (Math.random()-0.5)*400;
  });
}

function tick() {
  const W = window.innerWidth, H = window.innerHeight;
  const cx = W/2, cy = H/2;

  // دافعه بین نودها
  for (let i=0; i<NODES.length; i++) {
    for (let j=i+1; j<NODES.length; j++) {
      const a = NODES[i], b = NODES[j];
      let dx = b.x-a.x, dy = b.y-a.y;
      let d2 = dx*dx + dy*dy + 0.01;
      let d = Math.sqrt(d2);
      if (d < 300) {
        const f = 800 / d2;
        const fx = (dx/d) * f, fy = (dy/d) * f;
        a.vx -= fx; a.vy -= fy;
        b.vx += fx; b.vy += fy;
      }
    }
  }

  // جاذبه یال‌ها
  const idx = {}; NODES.forEach((n,i) => idx[n.id]=i);
  for (const e of EDGES) {
    const a = NODES[idx[e.source]], b = NODES[idx[e.target]];
    if (!a || !b) continue;
    const dx = b.x-a.x, dy = b.y-a.y;
    const d = Math.sqrt(dx*dx+dy*dy) + 0.01;
    const target = 90 - Math.min(e.weight, 10)*3;
    const f = (d - target) * 0.03;
    const fx = (dx/d)*f, fy = (dy/d)*f;
    a.vx += fx; a.vy += fy;
    b.vx -= fx; b.vy -= fy;
  }

  // گرانش مرکزی
  for (const n of NODES) {
    n.vx += (cx - n.x) * 0.001;
    n.vy += (cy - n.y) * 0.001;
    n.vx *= 0.85; n.vy *= 0.85;
    n.x += n.vx; n.y += n.vy;
  }
}

function render() {
  svg = document.getElementById("canvas");
  svg.setAttribute("viewBox", `0 0 ${window.innerWidth} ${window.innerHeight}`);
  svg.innerHTML = "";

  // یال‌ها
  const linksG = document.createElementNS("http://www.w3.org/2000/svg", "g");
  const idx = {}; NODES.forEach((n,i) => idx[n.id]=i);
  for (const e of EDGES) {
    const a = NODES[idx[e.source]], b = NODES[idx[e.target]];
    if (!a || !b) continue;
    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("x1", a.x); line.setAttribute("y1", a.y);
    line.setAttribute("x2", b.x); line.setAttribute("y2", b.y);
    line.setAttribute("stroke", "#1c2128");
    line.setAttribute("stroke-width", 0.5 + Math.min(e.weight, 5) * 0.8);
    line.setAttribute("data-a", e.source);
    line.setAttribute("data-b", e.target);
    linksG.appendChild(line);
  }
  svg.appendChild(linksG);

  // نودها
  const nodesG = document.createElementNS("http://www.w3.org/2000/svg", "g");
  NODES.forEach(n => {
    const c = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    const r = 5 + Math.min(n.count, 20) * 0.6;
    c.setAttribute("cx", n.x); c.setAttribute("cy", n.y);
    c.setAttribute("r", r);
    c.setAttribute("fill", COLORS[n.cat] || "#8b949e");
    c.setAttribute("stroke", "#0d1117");
    c.setAttribute("stroke-width", 1.5);
    c.style.cursor = "pointer";
    c.onclick = (ev) => { ev.stopPropagation(); showInfo(n.id); };
    c.onmouseover = () => { c.setAttribute("stroke", "#fff"); };
    c.onmouseout = () => { c.setAttribute("stroke", "#0d1117"); };
    nodesG.appendChild(c);

    if (n.count > 3 || r > 10) {
      const t = document.createElementNS("http://www.w3.org/2000/svg", "text");
      t.setAttribute("x", n.x); t.setAttribute("y", n.y - r - 3);
      t.setAttribute("text-anchor", "middle");
      t.setAttribute("fill", "#c9d1d9");
      t.setAttribute("font-size", "10");
      t.setAttribute("pointer-events", "none");
      t.textContent = n.id;
      nodesG.appendChild(t);
    }
  });
  svg.appendChild(nodesG);
}

let frameCount = 0;
let running = true;

function animate() {
  if (!running) return;
  for (let i=0; i<3; i++) tick();
  render();
  frameCount++;
  if (frameCount > 200) running = false;
  requestAnimationFrame(animate);
}

function restart() {
  frameCount = 0;
  running = true;
  animate();
}

async function showInfo(id) {
  const r = await fetch("/api/neighbors?id=" + encodeURIComponent(id));
  const data = await r.json();
  const box = document.getElementById("infoBody");
  let html = `<h3>${id}</h3>`;
  html += `<div class="row">دسته: <b>${data.cat}</b> | تکرار: ${data.count}</div>`;
  if (data.neighbors.length) {
    html += `<div style="margin-top:.6em;color:#8b949e">مرتبط‌ها:</div>`;
    for (const nb of data.neighbors.slice(0, 20)) {
      html += `<div class="row"><a href="#" onclick="showInfo('${nb.id}');return false">${nb.id}</a><span class="w">${nb.weight}</span></div>`;
    }
  }
  if (data.resources.length) {
    html += `<div style="margin-top:.6em;color:#8b949e">منابع:</div>`;
    for (const r of data.resources.slice(0, 8)) {
      html += `<div class="row"><a href="${r.url}" target="_blank">${r.title.slice(0,45)}</a></div>`;
    }
  }
  box.innerHTML = html;
  document.getElementById("info").style.display = "block";
}

function closeInfo() {
  document.getElementById("info").style.display = "none";
}

function doSearch() {
  const q = document.getElementById("search").value.trim().toLowerCase();
  if (!q) return;
  const found = NODES.find(n => n.id.includes(q));
  if (found) {
    showInfo(found.id);
  } else {
    alert("پیدا نشد");
  }
}

load();
animate();
</script>
</body></html>
"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _json(self, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _html(self, text):
        body = text.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        path = p.path
        qs = urllib.parse.parse_qs(p.query)

        if path == "/" or path == "/graph":
            self._html(HTML)
            return

        if path == "/api/graph":
            limit = int(qs.get("limit", ["200"])[0])
            min_w = int(qs.get("min_weight", ["1"])[0])
            self._json(load_graph(limit=limit, min_weight=min_w))
            return

        if path == "/api/neighbors":
            nid = qs.get("id", [""])[0]
            self._json(neighbors_data(nid))
            return

        self.send_error(404)


def neighbors_data(nid):
    """همسایه‌های یک نود + منابع مرتبط"""
    if not GRAPH_FILE.exists():
        return {"id": nid, "cat": "?", "count": 0, "neighbors": [], "resources": []}
    g = json.loads(GRAPH_FILE.read_text())
    nodes = g.get("nodes", {})
    cooc = g.get("cooc", {})
    edges = g.get("edges", {})

    info = nodes.get(nid, {})
    cats = info.get("cats", {})
    main_cat = max(cats, key=cats.get) if cats else "other"

    # همسایه‌های cooc
    rels = []
    for pair, w in cooc.items():
        a, b = pair.split("|", 1)
        if a == nid and not b.startswith("cat:"):
            rels.append((b, w))
        elif b == nid and not a.startswith("cat:"):
            rels.append((a, w))
    rels.sort(key=lambda x: -x[1])
    neighbors = [{"id": n, "weight": w} for n, w in rels[:30]]

    # منابع
    resources = []
    for key, w in edges.items():
        if key.startswith(nid + "\u2192"):
            rid = key.split("\u2192", 1)[1]
            rinfo = nodes.get(rid, {})
            if rinfo.get("type") == "resource":
                resources.append({
                    "title": rinfo.get("title", "")[:60],
                    "url": "https://github.com/" + rinfo.get("title", "")
                           if rinfo.get("source") == "github"
                           else "#",
                })
    return {
        "id": nid,
        "cat": main_cat,
        "count": info.get("count", 0),
        "neighbors": neighbors,
        "resources": resources[:10],
    }


def serve(port=8082):
    print(f"\n🌐 گراف وب: http://localhost:{port}")
    print(f"   Ctrl+C برای توقف\n")
    try:
        HTTPServer(("", port), Handler).serve_forever()
    except KeyboardInterrupt:
        print("\n⏸ متوقف شد")

