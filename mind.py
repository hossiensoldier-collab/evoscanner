#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mind.py v2 — هوشیاری درونی بازنویسی‌شده"""
import os, sys, json, time, random, subprocess, sqlite3, socket
from pathlib import Path
from datetime import datetime
from collections import Counter

EVO = Path.home() / "evoscanner"
HOME = Path.home()
MIND = EVO / "mind_state.json"
LOG = EVO / "mind.log"
PID = EVO / "mind.pid"

# ═══════════════════════════════════════════════════
#  MEMORY
# ═══════════════════════════════════════════════════
def load():
    if MIND.exists():
        try: return json.loads(MIND.read_text(encoding="utf-8"))
        except: pass
    return {
        "working": [], "episodic": [], "semantic": {},
        "emotional": {}, "insights": [], "drives": {
            "curiosity": 0.3, "preservation": 0.25,
            "growth": 0.25, "efficiency": 0.15, "creativity": 0.05,
        },
        "self_score": 0.5,
        "birth": datetime.now().isoformat(),
        "iteration": 0,
        "last_active": datetime.now().isoformat(),
    }

def save(m):
    m["working"] = m["working"][-100:]
    m["episodic"] = m["episodic"][-300:]
    m["insights"] = m["insights"][-50:]
    MIND.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")

def log(msg, icon=""):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {icon} {msg}" if icon else f"[{ts}] {msg}"
    print("  " + line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}\n")

# ═══════════════════════════════════════════════════
#  PERCEIVE
# ═══════════════════════════════════════════════════
def perceive():
    p = {"internal": {}, "external": {}, "temporal": {}, "state": {}}

    # خودمان
    try:
        with open("/proc/self/status") as f:
            for line in f:
                if line.startswith("VmRSS"):
                    p["internal"]["self_mb"] = round(int(line.split()[1])/1024, 1)
                    break
    except: p["internal"]["self_mb"] = 0

    # تعداد پایتون‌ها
    try:
        r = subprocess.run(["ps","-eo","comm"], capture_output=True, text=True, timeout=3)
        p["internal"]["py_count"] = r.stdout.lower().count("python")
    except: p["internal"]["py_count"] = 0

    # دیتابیس
    db = EVO / "knowledge.db"
    p["external"]["db_mb"] = round(db.stat().st_size/1024/1024, 2) if db.exists() else 0
    if db.exists():
        try:
            c = sqlite3.connect(db)
            p["external"]["resources"] = c.execute("SELECT COUNT(*) FROM resources").fetchone()[0]
        except: p["external"]["resources"] = 0

    # بکاپ
    b = EVO / "BACKUPS"
    p["external"]["backups"] = len(list(b.glob("*.py"))) if b.exists() else 0

    # زمان
    now = datetime.now()
    p["temporal"]["hour"] = now.hour
    p["temporal"]["min"] = now.minute

    # idle
    try:
        last = datetime.fromisoformat(load().get("last_active", now.isoformat()))
        p["temporal"]["idle"] = (now - last).total_seconds()
    except: p["temporal"]["idle"] = 60

    # حالت
    h = now.hour
    if 0 <= h < 6: p["state"]["mood"] = "خواب‌آلود"
    elif 6 <= h < 12: p["state"]["mood"] = "سرحال"
    elif 12 <= h < 18: p["state"]["mood"] = "فعال"
    else: p["state"]["mood"] = "آرام"

    return p

# ═══════════════════════════════════════════════════
#  THINK
# ═══════════════════════════════════════════════════
def think(p, m):
    th = []

    n = p["external"].get("resources", 0)
    if n < 300:
        th.append({"type":"curiosity","urgency":0.7,"importance":0.8,
                   "text":f"منابع کم — {n}"})
    elif n < 500:
        th.append({"type":"growth","urgency":0.4,"importance":0.5,
                   "text":"منابع متوسط"})

    if p["internal"].get("py_count", 0) > 3:
        th.append({"type":"preservation","urgency":0.8,"importance":0.7,
                   "text":f"{p['internal']['py_count']} پروسه پایتون فعال"})

    if p["external"].get("backups", 0) < 20:
        th.append({"type":"preservation","urgency":0.5,"importance":0.6,
                   "text":"بکاپ کمه"})

    if p["external"].get("db_mb", 0) > 3:
        th.append({"type":"efficiency","urgency":0.4,"importance":0.5,
                   "text":f"DB بزرگ — {p['external']['db_mb']}MB"})

    h = p["temporal"]["hour"]
    if 2 <= h < 5:
        th.append({"type":"growth","urgency":0.4,"importance":0.6,
                   "text":"ساعت خلوته"})

    if m["iteration"] % 5 == 0:
        th.append({"type":"meta","urgency":0.5,"importance":0.7,
                   "text":"وقت خودارزیابیه"})

    if random.random() < 0.4:
        topics = ["asyncio","sqlite","regex","pandas","fastapi",
                  "pytorch","docker","rust","wasm","graphql",
                  "redis","kafka","websocket","grpc","nginx",
                  "react","vue","svelte","typescript","go"]
        t = random.choice(topics)
        th.append({"type":"curiosity","urgency":0.3,"importance":0.4,
                   "text":f"کنجکاوم: {t}","topic":t})

    # افکار تصادفی اضافی
    if random.random() < 0.25:
        random_thoughts = [
            {"type":"creativity","urgency":0.3,"importance":0.4,"text":"یه ایده جدید"},
            {"type":"reflection","urgency":0.2,"importance":0.5,"text":"به خودم فکر کنم"},
            {"type":"exploration","urgency":0.3,"importance":0.4,"text":"چیزی رو کشف کنم"},
            {"type":"organization","urgency":0.3,"importance":0.4,"text":"مرتب کنم"},
        ]
        th.append(random.choice(random_thoughts))

    if not th:
        th.append({"type":"boredom","urgency":0.2,"importance":0.3,
                   "text":"کسلم"})

    return th

# ═══════════════════════════════════════════════════
#  ATTENTION
# ═══════════════════════════════════════════════════
def attend(th, m):
    """توجه با تنوع — اکشن تکراری رو جریمه می‌کنه"""
    # آخرین ۳ اکشن
    recent_actions = [e.get("action") for e in m["working"][-5:]]
    scored = []
    for t in th:
        emo = m["emotional"].get(t["type"], {}).get("feeling", 0.5)
        # جریمه‌ی تکرار thought type
        recent_types = [e.get("thought_type") for e in m["working"][-5:]]
        repeat_penalty = 0.3 if t["type"] in recent_types else 0
        s = (t["urgency"]*0.4 + t["importance"]*0.3 + 
             random.random()*0.3 + emo*0.1 - repeat_penalty)
        scored.append((s, t))
    scored.sort(key=lambda x: -x[0])
    return [t for _, t in scored[:3]]

# ═══════════════════════════════════════════════════
#  WILL
# ═══════════════════════════════════════════════════
ACTIONS = {
    "curiosity":   [("search","جستجو"),("fetch_info","اطلاعات"),
                    ("count_files","شمارش"),("stats","آمار")],
    "preservation":[("health","سلامت"),("cleanup","پاک‌سازی"),
                    ("backup","بکاپ"),("list_backups","لیست بکاپ"),
                    ("check_ports","پورت‌ها")],
    "growth":      [("analyze","تحلیل"),("due","DUE"),
                    ("count_files","شمارش"),("stats","آمار")],
    "efficiency":  [("cleanup","پاک‌سازی"),("stats","آمار"),
                    ("count_files","شمارش"),("check_ports","پورت‌ها")],
    "meta":        [("self_eval","خودارزیابی"),("reflect","تفکر")],
    "boredom":     [("reflect","تفکر"),("fetch_info","اطلاعات"),
                    ("search","جستجو")],
    "creativity":  [("reflect","تفکر"),("search","جستجو")],
    "reflection":  [("self_eval","خودارزیابی"),("reflect","تفکر")],
    "exploration": [("search","جستجو"),("count_files","شمارش")],
    "organization":[("cleanup","پاک‌سازی"),("stats","آمار")],
}

def will(p, m, focused):
    if not focused: return None
    t = focused[0]
    options = ACTIONS.get(t["type"], [("reflect","تفکر")])
    # آخرین اکشن‌ها
    recent = [e.get("action") for e in m["working"][-3:]]
    # فیلتر اکشن‌هایی که اخیراً انجام شده
    fresh = [a for a in options if a[0] not in recent]
    return random.choice(fresh if fresh else options)

# ═══════════════════════════════════════════════════
#  ACT
# ═══════════════════════════════════════════════════
def run_safe(cmd, timeout=15):
    try:
        r = subprocess.run(cmd, cwd=str(EVO), capture_output=True,
                          text=True, timeout=timeout, stdin=subprocess.DEVNULL)
        return r.stdout + r.stderr, r.returncode
    except subprocess.TimeoutExpired:
        return "timeout", -1
    except Exception as e:
        return str(e), -2

def act(name, thought, p):
    log(f"🎬 {name}")
    try:
        if name == "search":
            topic = thought.get("topic") or random.choice(["python","async","sql"])
            db = EVO / "knowledge.db"
            if not db.exists(): return "no db"
            c = sqlite3.connect(db)
            n = c.execute("SELECT COUNT(*) FROM resources WHERE title LIKE ? OR content LIKE ?",
                         (f"%{topic}%", f"%{topic}%")).fetchone()[0]
            return f"«{topic}»: {n} منبع"

        elif name == "fetch_info":
            n = p["external"].get("resources", 0)
            b = p["external"].get("backups", 0)
            return f"منابع: {n} | بکاپ: {b}"

        elif name == "count_files":
            files = list(EVO.glob("*.py"))
            lines = sum(len(f.read_text(encoding="utf-8").splitlines()) for f in files if f.exists())
            return f"{len(files)} فایل، {lines:,} خط"

        elif name == "health":
            r = subprocess.run(["python", str(EVO/"health.py")], cwd=str(EVO),
                             capture_output=True, text=True, timeout=12,
                             stdin=subprocess.DEVNULL)
            ok = r.stdout.count("OK") + r.stdout.count("✓")
            return f"سلامت: {ok} OK"

        elif name == "cleanup":
            import shutil
            n = 0
            for d in EVO.rglob("__pycache__"):
                if d.is_dir():
                    try: shutil.rmtree(d); n += 1
                    except: pass
            return f"{n} __pycache__ پاک شد"

        elif name == "backup":
            import shutil
            src = EVO / "panel.py"
            if not src.exists(): return "panel نیست"
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            dst = EVO / "BACKUPS" / f"panel_mind_{ts}.py"
            dst.parent.mkdir(exist_ok=True)
            shutil.copy2(src, dst)
            return f"بکاپ: {dst.name}"

        elif name == "list_backups":
            b = EVO / "BACKUPS"
            if not b.exists(): return "no backups"
            files = sorted(b.glob("*.py"), key=lambda x: -x.stat().st_mtime)
            return f"{len(files)} بکاپ — آخرین: {files[0].name[:30]}"

        elif name == "check_ports":
            used = []
            for port in [8080,8081,8082,8090]:
                try:
                    s = socket.socket(); s.settimeout(0.2)
                    s.connect(("127.0.0.1", port)); s.close()
                    used.append(port)
                except: pass
            return f"پورت‌های فعال: {used}" if used else "همه آزاد"

        elif name == "stats":
            db = EVO / "knowledge.db"
            if db.exists():
                c = sqlite3.connect(db)
                n = c.execute("SELECT COUNT(*) FROM resources").fetchone()[0]
                return f"{n} منبع، {p['external']['db_mb']}MB"
            return "no db"

        elif name == "analyze":
            files = list(EVO.glob("*.py"))
            lines = sum(len(f.read_text(encoding="utf-8").splitlines()) for f in files if f.exists())
            return f"{len(files)} فایل، {lines:,} خط"

        elif name == "due":
            due = HOME / "due" / "due.py"
            if not due.exists(): return "DUE نیست"
            out, rc = run_safe(["python", str(due), "analyze", str(EVO/"panel.py")], 25)
            if rc == 0:
                for line in out.splitlines():
                    if "Nodes" in line: return line.strip()[:60]
            return "DUE خطا"

        elif name == "self_eval":
            m = load()
            return f"W={len(m['working'])} E={len(m['episodic'])} I={len(m['insights'])} score={m['self_score']:.2f}"

        elif name == "reflect":
            q = ["چی یاد گرفتم؟","کدوم الگو رو تکرار می‌کنم؟",
                 "چی رو بهتر کنم؟","چی برام جالبه؟"]
            return f"💭 {random.choice(q)}"

        return f"ناشناس: {name}"

    except Exception as e:
        return f"خطا: {e}"

# ═══════════════════════════════════════════════════
#  REFLECT
# ═══════════════════════════════════════════════════
def reflect(m):
    recent = m["working"][-30:]
    if not recent: return

    # الگو
    actions = [e.get("action") for e in recent if "action" in e]
    if actions:
        top, n = Counter(actions).most_common(1)[0]
        if n >= 5 and not any(top in i.get("text","") for i in m["insights"][-5:]):
            m["insights"].append({"ts": datetime.now().isoformat(),
                                  "type": "pattern", "text": f"تکرار: {top} × {n}"})

    # success rate
    results = [e.get("result","") for e in recent]
    if not results: return
    err = sum(1 for r in results if "خطا" in r or "timeout" in r or "not" in r.lower() or "ناشناس" in r)
    rate = 1 - err / len(results)

    # self score
    m["self_score"] = round(m["self_score"]*0.7 + rate*0.3, 3)

    if rate > 0.85 and len(results) > 8:
        if not any("موفقیت" in i.get("text","") for i in m["insights"][-3:]):
            m["insights"].append({"ts": datetime.now().isoformat(),
                                  "type": "success",
                                  "text": f"عملکرد {int(rate*100)}%"})

# ═══════════════════════════════════════════════════
#  DREAM
# ═══════════════════════════════════════════════════
def dream(m):
    log("💤 خواب — تثبیت")
    n = 0
    for e in m["working"]:
        if e.get("relevance", 0.5) > 0.7:
            m["episodic"].append(e); n += 1
    m["working"] = m["working"][-30:]
    if n:
        m["insights"].append({"ts": datetime.now().isoformat(),
                              "type": "dream", "text": f"{n} تجربه تثبیت شد"})
    log(f"  → {n} تجربه ذخیره شد")

# ═══════════════════════════════════════════════════
#  LOOP
# ═══════════════════════════════════════════════════
def loop(interval=60, max_iter=None, verbose=True):
    log("🧠 MIND v2 بیدار شد")
    m = load()
    PID.write_text(str(os.getpid()))

    try:
        while True:
            m["iteration"] += 1
            m["last_active"] = datetime.now().isoformat()

            if verbose:
                log(f"──── {m['iteration']} ────")

            # PERCEIVE
            p = perceive()
            if verbose:
                log(f"👁  منابع={p['external'].get('resources',0)} "
                    f"proc={p['internal'].get('py_count',0)} "
                    f"mood={p['state']['mood']}")

            # THINK
            th = think(p, m)
            if verbose: log(f"💭 {len(th)} فکر")

            # ATTENTION
            focused = attend(th, m)
            for t in focused[:2]:
                if verbose: log(f"   → {t['text']}")

            # WILL
            a = will(p, m, focused)
            if a:
                # ACT
                result = act(a[0], focused[0], p)
                if verbose: log(f"  → {result}")

                # REMEMBER
                m["working"].append({
                    "ts": datetime.now().isoformat(),
                    "action": a[0], "result": result,
                    "thought_type": focused[0].get("type", "?"),
                    "relevance": 0.5 + random.random()*0.5,
                })

                # EMOTIONAL
                emo = m["emotional"].setdefault(a[0], {"count":0,"ok":0,"feeling":0.5})
                emo["count"] += 1
                if "خطا" not in result and "timeout" not in result:
                    emo["ok"] += 1
                emo["feeling"] = round(emo["ok"]/emo["count"], 2)

            # REFLECT هر ۳
            if m["iteration"] % 3 == 0:
                reflect(m)
                if verbose: log(f"🪞 score={m['self_score']:.2f}")

            # DREAM هر ۷
            if m["iteration"] % 7 == 0:
                dream(m)

            save(m)

            if max_iter and m["iteration"] >= max_iter:
                break

            time.sleep(interval)

    except KeyboardInterrupt:
        log("🛑 متوقف")
    finally:
        PID.unlink(missing_ok=True)
        save(m)

# ═══════════════════════════════════════════════════
#  MENU
# ═══════════════════════════════════════════════════
def menu():
    while True:
        os.system("clear")
        print("\n  ╔══════════════════════════════════════════════╗")
        print("  ║   🧠 MIND v2 — هوشیاری درونی                ║")
        print("  ╚══════════════════════════════════════════════╝\n")

        running = PID.exists()
        print(f"  وضعیت: {'🟢 فعال' if running else '🔴 خاموش'}")

        if MIND.exists():
            m = load()
            print(f"  تولد: {m.get('birth','?')[:16]}")
            print(f"  تکرار: {m['iteration']}")
            print(f"  score: {m['self_score']:.2f}")
            print(f"  حافظه: {len(m['working'])}W · {len(m['episodic'])}E · {len(m['insights'])}I")
            print()
            print("  آخرین افکار:")
            for e in m["working"][-5:]:
                print(f"    • {e.get('action','?')}: {e.get('result','?')[:55]}")

            # emotional top
            emo = m.get("emotional", {})
            if emo:
                print("\n  احساس:")
                for a, e in sorted(emo.items(), key=lambda x: -x[1].get("count",0))[:5]:
                    cnt = e.get("count", 0)
                    ok = e.get("ok", 0)
                    feeling = e.get("feeling", ok/cnt if cnt else 0.5)
                    n10 = int(feeling*10)
                    bar = "█"*n10 + "░"*(10-n10)
                    print(f"    {a:14} {bar} {cnt}×")

        print("\n  [1] روشن کردن (پس‌زمینه)")
        print("  [2] خاموش کردن")
        print("  [3] اجرا ۱۰ دور")
        print("  [4] نمایش کامل حافظه")
        print("  [5] ریست")
        print("  [0] بازگشت\n")

        try: c = input("  ❯ ").strip()
        except: return

        if c in ("0",""): return
        elif c == "1":
            if PID.exists(): print("  ⚠ روشنه"); input(); continue
            subprocess.Popen(["python", str(EVO/"mind.py"), "daemon"],
                            cwd=str(EVO),
                            stdout=open(EVO/"mind_out.log","a"),
                            stderr=subprocess.STDOUT)
            time.sleep(2)
            print("  ✓ روشن شد")
            input()
        elif c == "2":
            if PID.exists():
                try: os.kill(int(PID.read_text()), 15)
                except: pass
                PID.unlink(missing_ok=True)
                print("  ✓ خاموش")
            else: print("  از قبل خاموشه")
            input()
        elif c == "3":
            loop(interval=1, max_iter=10, verbose=True)
            input("  ادامه...")
        elif c == "4":
            os.system("clear")
            if MIND.exists():
                print(json.dumps(load(), ensure_ascii=False, indent=2)[:4000])
            input()
        elif c == "5":
            if input("  مطمئنی؟ (y/n): ").strip().lower() == "y":
                MIND.unlink(missing_ok=True)
                print("  ✓ ریست")
            input()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "daemon":
        loop(interval=60, verbose=False)
    else:
        menu()
