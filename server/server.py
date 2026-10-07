"""HTTP Server on 8080"""
import json, os, signal, socket, ssl, sys, time
import urllib.parse, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE = Path(__file__).parent
LOG = BASE / "server.log"
PID = BASE / "server.pid"
PORT = 8080

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE


def log(msg):
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _j(self, data, status=200):
        b = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(p.query)
        path = p.path

        if path == "/health":
            self._j({"ok": True, "ts": time.time()})
        elif path == "/info":
            self._j({
                "hostname": socket.gethostname(),
                "port": PORT,
                "python": sys.version.split()[0],
            })
        elif path == "/proxy":
            url = qs.get("url", [""])[0]
            if not url:
                self._j({"error": "url required"}, 400); return
            try:
                req = urllib.request.Request(
                    url, headers={"User-Agent": "EvoScanner/1.0"})
                with urllib.request.urlopen(
                        req, timeout=20, context=SSL_CTX) as r:
                    self._j({"ok": True, "status": r.status,
                             "body": r.read(50000).decode(
                                 "utf-8", errors="ignore")})
            except Exception as e:
                self._j({"ok": False, "error": str(e)[:200]}, 502)
        else:
            self._j({"endpoints": [
                "GET /health", "GET /info",
                "POST /echo", "GET /proxy?url=...",
            ]})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else b""
        if urllib.parse.urlparse(self.path).path == "/echo":
            self._j({"ok": True,
                     "received": body.decode("utf-8", errors="ignore")[:2000],
                     "length": len(body)})
        else:
            self._j({"error": "not found"}, 404)


def start():
    if PID.exists():
        try:
            os.kill(int(PID.read_text()), 0)
            print("already running"); return
        except Exception:
            PID.unlink()
    if os.fork() != 0:
        print("starting..."); time.sleep(1)
        if PID.exists():
            print(f"PID: {PID.read_text().strip()}")
            print(f"http://127.0.0.1:{PORT}")
        return
    os.setsid()
    with open(os.devnull, "w") as dn:
        os.dup2(dn.fileno(), 1); os.dup2(dn.fileno(), 2)
    PID.write_text(str(os.getpid()))
    log("start")
    try:
        srv = ThreadingHTTPServer(("127.0.0.1", PORT), H)
        srv.daemon_threads = True
        srv.serve_forever()
    except Exception as e:
        log(f"error: {e}")
    finally:
        if PID.exists(): PID.unlink()
        log("stop")


def stop():
    if not PID.exists():
        print("not running"); return
    try:
        os.kill(int(PID.read_text()), signal.SIGTERM)
        time.sleep(1); PID.unlink(); print("stopped")
    except Exception as e:
        print(f"error: {e}")
        if PID.exists(): PID.unlink()


def status():
    if PID.exists():
        try:
            pid = int(PID.read_text())
            os.kill(pid, 0)
            print(f"running (PID {pid})")
            print(f"http://127.0.0.1:{PORT}")
            return
        except Exception:
            pass
    print("stopped")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "start": start()
    elif cmd == "stop": stop()
    elif cmd == "restart": stop(); time.sleep(1); start()
    else: status()
