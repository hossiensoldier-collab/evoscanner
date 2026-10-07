#!/usr/bin/env python3
"""EvoScanner IDE — برای صفحه‌های باریک"""
import curses, json, sys, urllib.parse, urllib.request
from pathlib import Path

API = "http://localhost:8081"
DEFAULT = Path.home() / "project.py"


def api_get(path):
    try:
        with urllib.request.urlopen(API + path, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e)}


def api_post(path, data):
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(API + path, data=body,
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e)}


class Editor:
    def __init__(self, scr, fp):
        self.scr = scr
        self.fp = Path(fp)
        self.lines = [""]
        self.cx = self.cy = 0
        self.oy = 0
        self.mod = False
        self.msg = "Ready"
        self.panel = None       # None | "suggest" | "related" | "ask" | "help"
        self.panel_items = []
        self.panel_title = ""
        self.ask_q = ""

        if self.fp.exists():
            try:
                t = self.fp.read_text(encoding="utf-8")
                self.lines = t.split("\n") or [""]
            except Exception as e:
                self.msg = f"open err: {e}"

        curses.curs_set(1)
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, -1)
        curses.init_pair(2, curses.COLOR_GREEN, -1)
        curses.init_pair(3, curses.COLOR_YELLOW, -1)
        curses.init_pair(4, curses.COLOR_RED, -1)
        curses.init_pair(5, curses.COLOR_MAGENTA, -1)
        curses.init_pair(6, curses.COLOR_BLUE, -1)
        curses.init_pair(7, curses.COLOR_WHITE, -1)
        curses.init_pair(8, curses.COLOR_BLACK, curses.COLOR_CYAN)

    def save(self):
        try:
            self.fp.write_text("\n".join(self.lines), encoding="utf-8")
            self.mod = False
            self.msg = "Saved"
        except Exception as e:
            self.msg = f"save err: {e}"

    def word_at_cursor(self):
        if self.cy >= len(self.lines):
            return ""
        line = self.lines[self.cy]
        i = min(self.cx, max(0, len(line) - 1))
        if i < 0 or not line:
            return ""
        s = e = i
        ok = lambda c: c.isalnum() or c in "_-."
        while s > 0 and ok(line[s-1]):
            s -= 1
        while e < len(line) and ok(line[e]):
            e += 1
        return line[s:e]

    def do_suggest(self):
        code = "\n".join(self.lines)
        d = api_post("/suggest", {"code": code})
        if "error" in d:
            self.msg = f"API: {d['error']}"
            return
        sugs = d.get("suggestions", [])
        if not sugs:
            self.msg = "No suggestions (write imports first)"
            return
        self.panel_title = "SUGGESTIONS"
        self.panel_items = [
            f"{s['pkg']:22s}  w={s['weight']}  ({s['for']})"
            for s in sugs
        ]
        self.panel = "suggest"
        self.msg = f"{len(sugs)} suggestions"

    def do_related(self):
        w = self.word_at_cursor()
        if not w:
            self.msg = "Put cursor on a word"
            return
        d = api_get(f"/related?pkg={urllib.parse.quote(w)}")
        if "error" in d:
            self.msg = f"API: {d['error']}"
            return
        items = []
        for r in d.get("related", [])[:25]:
            items.append(f"{r['name']:26s}  w={r['weight']}")
        for r in d.get("peers", [])[:10]:
            items.append(f"[peer] {r['name']:19s}  {r['weight']}")
        if not items:
            self.msg = f"No data for {w}"
            return
        self.panel_title = f"RELATED: {w} [{d.get('category','?')}]"
        self.panel_items = items
        self.panel = "related"
        self.msg = f"related to {w}"

    def do_ask(self, q):
        if not q:
            return
        self.msg = "asking..."
        self.draw()
        d = api_get(f"/ask?q={urllib.parse.quote(q)}&top=3")
        if "error" in d:
            self.msg = f"API: {d['error']}"
            return
        items = []
        for i, a in enumerate(d.get("answers", []), 1):
            items.append(f"--- [{i}] {a['title'][:40]} ---")
            text = a["text"][:500]
            # wrap
            W = max(30, self.w - 4)
            for j in range(0, len(text), W):
                items.append("  " + text[j:j+W])
            items.append(f"  {a['url']}")
            items.append("")
        if not items:
            self.msg = "No answer"
            return
        self.panel_title = f"ASK: {q[:40]}"
        self.panel_items = items
        self.panel = "ask"
        self.msg = f"{len(d.get('answers',[]))} answers"

    def draw(self):
        self.scr.erase()
        h, w = self.scr.getmaxyx()
        self.h, self.w = h, w
        status_y = h - 2
        line_area = h - 3

        # هدر
        name = self.fp.name + (" ●" if self.mod else "")
        header = f" EvoScanner IDE │ {name} "
        try:
            self.scr.addstr(0, 0, header.ljust(w)[:w],
                            curses.color_pair(1) | curses.A_BOLD)
        except curses.error:
            pass

        # ادیتور
        num_w = max(3, len(str(len(self.lines))) + 1)
        text_w = w - num_w - 1
        for i in range(line_area):
            y = 1 + i
            ln = self.oy + i
            if ln >= len(self.lines):
                break
            try:
                self.scr.addstr(y, 0, f"{ln+1:>{num_w}} ",
                                curses.color_pair(6))
                text = self.lines[ln][:text_w]
                self.scr.addstr(y, num_w + 1, text)
            except curses.error:
                pass

        # پنل overlay
        if self.panel:
            self._draw_panel(h, w, status_y)

        # status
        bar = f" [{self.panel or 'edit'}] {self.msg} "
        try:
            self.scr.addstr(status_y, 0, bar.ljust(w)[:w], curses.color_pair(8))
        except curses.error:
            pass

        # help
        keys = "^S save  ^E sug  ^R rel  ^A ask  ^F close  ^Q quit"
        try:
            self.scr.addstr(status_y + 1, 0, keys.ljust(w)[:w],
                            curses.color_pair(1))
        except curses.error:
            pass

        # مکان‌نما
        if not self.panel:
            sy = 1 + (self.cy - self.oy)
            sx = num_w + 1 + self.cx
            if 0 <= sy < status_y and 0 <= sx < w:
                try:
                    self.scr.move(sy, sx)
                except curses.error:
                    pass

        self.scr.refresh()

    def _draw_panel(self, h, w, status_y):
        # overlay از وسط تا پایین
        top = 3
        bottom = status_y - 1
        title_y = top
        try:
            self.scr.addstr(title_y, 0, " " * w, curses.color_pair(5))
            self.scr.addstr(title_y, 1, self.panel_title[:w-2],
                            curses.color_pair(5) | curses.A_BOLD)
        except curses.error:
            pass

        for i, line in enumerate(self.panel_items):
            y = title_y + 1 + i
            if y >= bottom:
                break
            attr = curses.color_pair(7)
            if line.startswith("["):
                attr = curses.color_pair(3)
            if line.startswith("---"):
                attr = curses.color_pair(1) | curses.A_BOLD
            try:
                self.scr.addstr(y, 1, line[:w-2], attr)
            except curses.error:
                pass

    def handle(self, key):
        h, w = self.h, self.w
        line = self.lines[self.cy] if self.cy < len(self.lines) else ""

        # اگر پنل باز است، Ctrl+F ببندد
        if key == 6:  # Ctrl+F
            self.panel = None
            self.msg = "closed"
            return True

        # Ctrl+S
        if key == 19:
            self.save(); return True
        # Ctrl+Q
        if key == 17:
            if self.mod:
                self.msg = "Unsaved! Ctrl+Q again to force"
                self.mod = False
                return True
            return False
        # Ctrl+E
        if key == 5:
            self.do_suggest(); return True
        # Ctrl+R
        if key == 18:
            self.do_related(); return True
        # Ctrl+A
        if key == 1:
            q = self._ask_input()
            if q:
                self.do_ask(q)
            return True
        # Ctrl+K
        if key == 11:
            self.lines[self.cy] = ""; self.cx = 0; self.mod = True
            return True

        # اگر پنل باز است، جهت‌ها را نادیده بگیر برای حرکت
        if self.panel and key in (curses.KEY_UP, curses.KEY_DOWN):
            return True

        # F1
        if key == curses.KEY_F1:
            self.panel_title = "HELP"
            self.panel_items = [
                "Ctrl+S  save file",
                "Ctrl+E  suggest imports",
                "Ctrl+R  related to word",
                "Ctrl+A  ask question",
                "Ctrl+K  clear line",
                "Ctrl+F  close panel",
                "Ctrl+Q  quit (twice if modified)",
                "",
                "Arrows  move cursor",
                "Home/End  line start/end",
                "PgUp/PgDn  page",
                "F1  this help",
            ]
            self.panel = "help"
            return True

        # حرکت
        if key == curses.KEY_UP:
            if self.cy > 0:
                self.cy -= 1; self.cx = min(self.cx, len(self.lines[self.cy]))
                self._scroll()
        elif key == curses.KEY_DOWN:
            if self.cy < len(self.lines) - 1:
                self.cy += 1; self.cx = min(self.cx, len(self.lines[self.cy]))
                self._scroll()
        elif key == curses.KEY_LEFT:
            if self.cx > 0: self.cx -= 1
        elif key == curses.KEY_RIGHT:
            if self.cx < len(line): self.cx += 1
        elif key == curses.KEY_HOME:
            self.cx = 0
        elif key == curses.KEY_END:
            self.cx = len(line)
        elif key == curses.KEY_PPAGE:
            self.cy = max(0, self.cy - (h - 4))
            self.cx = min(self.cx, len(self.lines[self.cy]) if self.cy < len(self.lines) else 0)
            self._scroll()
        elif key == curses.KEY_NPAGE:
            self.cy = min(len(self.lines) - 1, self.cy + (h - 4))
            self.cx = min(self.cx, len(self.lines[self.cy]))
            self._scroll()
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            if self.cx > 0:
                self.lines[self.cy] = line[:self.cx-1] + line[self.cx:]
                self.cx -= 1; self.mod = True
            elif self.cy > 0:
                prev = self.lines[self.cy-1]
                self.cx = len(prev)
                self.lines[self.cy-1] = prev + line
                del self.lines[self.cy]
                self.cy -= 1; self.mod = True
                self._scroll()
        elif key == curses.KEY_DC:
            if self.cx < len(line):
                self.lines[self.cy] = line[:self.cx] + line[self.cx+1:]
                self.mod = True
        elif key in (10, 13, curses.KEY_ENTER):
            rest = line[self.cx:]
            self.lines[self.cy] = line[:self.cx]
            self.lines.insert(self.cy + 1, rest)
            self.cy += 1; self.cx = 0; self.mod = True
            self._scroll()
        elif key == 9:
            self.lines[self.cy] = line[:self.cx] + "    " + line[self.cx:]
            self.cx += 4; self.mod = True
        elif 32 <= key < 127:
            self.lines[self.cy] = line[:self.cx] + chr(key) + line[self.cx:]
            self.cx += 1; self.mod = True
        return True

    def _scroll(self):
        h = self.h
        if self.cy < self.oy:
            self.oy = self.cy
        elif self.cy >= self.oy + h - 3:
            self.oy = self.cy - (h - 4)

    def _ask_input(self):
        """درخواست یک خط ورودی"""
        h, w = self.h, self.w
        curses.echo()
        curses.curs_set(1)
        try:
            self.scr.addstr(h - 1, 0, " " * (w - 1))
            self.scr.addstr(h - 1, 0, "Q: ", curses.color_pair(3))
            self.scr.refresh()
            raw = self.scr.getstr(h - 1, 3, 200)
            q = raw.decode("utf-8", errors="ignore").strip()
        except Exception:
            q = ""
        curses.noecho()
        return q


def main(scr, path):
    e = Editor(scr, path)
    scr.keypad(True)
    while True:
        e.draw()
        try:
            k = scr.getch()
        except KeyboardInterrupt:
            break
        if k == -1:
            continue
        if not e.handle(k):
            break


if __name__ == "__main__":
    fp = sys.argv[1] if len(sys.argv) > 1 else str(DEFAULT)
    try:
        urllib.request.urlopen(API + "/health", timeout=2)
    except Exception:
        print("API is down. Start with: ./evosh start")
        sys.exit(1)
    curses.wrapper(main, fp)

