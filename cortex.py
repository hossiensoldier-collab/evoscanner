#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, json, re, time, sqlite3, subprocess
from pathlib import Path
from datetime import datetime

EVO = Path.home() / "evoscanner"
HOME = Path.home()
DB = EVO / "knowledge.db"
MEM = EVO / "cortex_memory.json"

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"  \033[2m[{ts}]\033[0m {msg}")

def load_mem():
    if MEM.exists():
        try: return json.loads(MEM.read_text(encoding="utf-8"))
        except: pass
    return {"sessions": [], "skills": {}, "insights": []}

def save_mem(m):
    MEM.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")

def perceive():
    s = {"resources":0,"nodes":0,"edges":0,"techniques":0,"snippets":0}
    # DB اصلی evoscanner
    if DB.exists():
        try:
            c = sqlite3.connect(DB)
            for t in ["resources","nodes","edges","techniques","snippets"]:
                try: s[t] = c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                except: pass
        except: pass
    # DB knowledgeforge
    forge = HOME / "knowledgeforge" / "knowledge.db"
    if forge.exists():
        try:
            c2 = sqlite3.connect(forge)
            for t in ["nodes","edges"]:
                try:
                    n = c2.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                    s[t] = max(s[t], n)
                except: pass
        except: pass
    return s

def plan(goal):
    g = goal.lower()
    if any(k in g for k in ["بهبود","improve","ارتقا","fix","درست","تعمیر","repair"]):
        return [("DIAGNOSE","تشخیص"),("TEST","تست"),("REPORT","گزارش")]
    if any(k in g for k in ["تحلیل","analyze","بررسی","review"]):
        return [("SCAN","اسکن"),("DUE","DUE"),("GRAPH","گراف"),("REPORT","گزارش")]
    if any(k in g for k in ["یاد","learn","آموزش","مفهوم","concept","مسیر"]):
        return [("SEARCH","جستجو"),("EXTRACT","استخراج"),("MAP","مسیر"),("REPORT","گزارش")]
    if any(k in g for k in ["پژوهش","research","کشف"]):
        return [("SEARCH","جستجو"),("ANALYZE","تحلیل"),("SYNTH","ترکیب"),("REPORT","گزارش")]
    if any(k in g for k in ["ساخت","build","تولید","generate","بنویس"]):
        return [("SEARCH","جستجو"),("ANALYZE","تحلیل"),("GENERATE","تولید"),("REPORT","گزارش")]
    return [("SEARCH","جستجو"),("ANALYZE","تحلیل"),("REPORT","گزارش")]

def a_search(goal, st):
    if not DB.exists(): return "DB نیست"
    fa2en = {"پنل":"panel","کد":"code","پروژه":"project","تحلیل":"analysis",
             "یادگیری":"learning","آموزش":"tutorial","گراف":"graph",
             "منبع":"source","دیتابیس":"database","خودکار":"auto","بهبود":"improve",
             "ساخت":"build","ابزار":"tool","وب":"web","سرور":"server"}
    words = [x for x in re.split(r"\s+", goal) if len(x)>2]
    eng = [fa2en[w] for w in words if w in fa2en]
    eng += [w for w in words if w.isascii()]
    if not eng: eng = ["python"]
    try:
        c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
        out = []
        for w in eng[:3]:
            try:
                for r in c.execute("SELECT title,url,source FROM resources WHERE title LIKE ? OR content LIKE ? ORDER BY score DESC LIMIT 5",(f"%{w}%",f"%{w}%")):
                    out.append(dict(r))
            except: pass
        if not out:
            try:
                for r in c.execute("SELECT title,url,source FROM resources ORDER BY score DESC LIMIT 5"):
                    out.append(dict(r))
            except: pass
        if not out: return "چیزی پیدا نشد"
        seen=set(); uniq=[]
        for r in out:
            k=r.get("title","")
            if k and k not in seen: seen.add(k); uniq.append(r)
        lines = [f"{len(uniq)} نتیجه:"]
        for r in uniq[:5]:
            lines.append(f"  ● {r.get('title','?')[:60]}")
        return "\n".join(lines)
    except Exception as e:
        return f"⚠ {e}"

def a_extract(goal, st):
    try:
        r = subprocess.run([sys.executable,"learn.py"],cwd=str(EVO),capture_output=True,text=True,timeout=60)
        return r.stdout[-400:] if r.returncode==0 else f"خطا: {r.stderr[-150:]}"
    except Exception as e: return f"⚠ {e}"

def a_due(goal, st):
    try:
        due = HOME/"due"/"due.py"
        if not due.exists(): return "DUE نیست"
        r = subprocess.run(
            [sys.executable, str(due), "analyze", str(EVO/"panel.py")],
            capture_output=True, text=True, timeout=30
        )
        if r.returncode != 0:
            return f"DUE خطا"
        out = r.stdout
        lines = []
        for line in out.splitlines():
            s = line.strip()
            if any(k in s for k in ["Nodes", "Edges", "Flows", "Constraints", "Evidence"]):
                lines.append(s)
        return " | ".join(lines[:6]) if lines else "DUE اجرا شد"
    except Exception as e: return f"⚠ {e}"

def a_graph(goal, st):
    forge = HOME / "knowledgeforge" / "knowledge.db"
    if forge.exists():
        try:
            c = sqlite3.connect(forge)
            n = c.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
            e = c.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
            r = c.execute("SELECT COUNT(*) FROM rules").fetchone()[0]
            return f"nodes={n} edges={e} rules={r}"
        except: pass
    if DB.exists():
        try:
            c = sqlite3.connect(DB)
            n = c.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
            e = c.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
            return f"nodes={n} edges={e}"
        except Exception as ex: return f"⚠ {ex}"
    return "بدون گراف"

def a_scan(goal, st):
    files = list(EVO.glob("*.py"))
    n = sum(len(p.read_text(encoding="utf-8").splitlines()) for p in files if p.exists())
    return f"{len(files)} فایل، {n:,} خط"

def a_generate(goal, st):
    try:
        s = HOME/"sacred"/"sacred.py"
        if s.exists():
            r = subprocess.run([sys.executable,str(s),"ask",goal],capture_output=True,text=True,timeout=20)
            return r.stdout[-400:] if r.returncode==0 else "sacred خطا"
        return "sacred نیست"
    except Exception as e: return f"⚠ {e}"

def a_diagnose(goal, st):
    try:
        sys.path.insert(0, str(EVO))
        import autoheal
        iss = autoheal.diagnose(EVO/"panel.py")
        if not iss:
            return f"پنل سالم — {len(list(EVO.glob('*.py')))} فایل پایتون بررسی شد"
        types = {}
        for i in iss:
            t = i.get("type","?")
            types[t] = types.get(t,0)+1
        return f"{len(iss)} مشکل: " + ", ".join(f"{k}×{v}" for k,v in types.items())
    except Exception as e: return f"⚠ {e}"

def a_test(goal, st):
    try:
        r = subprocess.run([sys.executable,"panel_test.py"],cwd=str(EVO),capture_output=True,text=True,timeout=120)
        m = re.search(r"OK:\s+(\d+).*?FAIL:\s+(\d+)", r.stdout, re.DOTALL)
        return f"OK:{m.group(1)} FAIL:{m.group(2)}" if m else "اجرا شد"
    except: return "timeout"

def a_map(goal, st):
    return f"مسیر یادگیری برای «{goal[:30]}»"

def a_report(goal, st):
    return f"منابع:{st.get('resources',0)} نود:{st.get('nodes',0)} یال:{st.get('edges',0)} تکنیک:{st.get('techniques',0)}"

def a_analyze(goal, st):
    return f"src={st.get('resources',0)} graph={st.get('nodes',0)} tech={st.get('techniques',0)}"

ACT = {"SEARCH":a_search,"EXTRACT":a_extract,"DUE":a_due,"GRAPH":a_graph,
       "SCAN":a_scan,"GENERATE":a_generate,"DIAGNOSE":a_diagnose,
       "TEST":a_test,"MAP":a_map,"REPORT":a_report,"ANALYZE":a_analyze}

def reflect(steps, results):
    ok = 0; notes = []
    for (name,_), r in zip(steps, results):
        if r is None: notes.append(f"✗ {name}"); continue
        t = str(r)
        if "⚠" in t or "خطا" in t or "نیست" in t:
            notes.append(f"⚠ {name}")
        elif len(t) < 10:
            notes.append(f"○ {name}")
        else:
            ok += 1; notes.append(f"✓ {name}")
    pct = int(100*ok/len(steps)) if steps else 0
    return {"score":pct,"notes":notes,"ok":ok,"total":len(steps)}

def run_cycle(goal):
    print()
    print("  ╔══════════════════════════════════════════════╗")
    print("  ║   ◆ CORTEX — ایجنت خودمختار                  ║")
    print("  ╚══════════════════════════════════════════════╝\n")
    print(f"  🎯 هدف: {goal}\n")

    print("  ┌─ [1/6] PERCEIVE ─────")
    st = perceive()
    log(f"منابع:{st['resources']} | نود:{st['nodes']} | یال:{st['edges']} | تکنیک:{st['techniques']}")
    print()

    print("  ┌─ [2/6] PLAN ─────")
    steps = plan(goal)
    for i,(n,d) in enumerate(steps,1): log(f"{i}. {n:10} {d}")
    print()

    print("  ┌─ [3/6] ACT ─────")
    results = []
    for n,d in steps:
        fn = ACT.get(n)
        if not fn: results.append(None); continue
        log(f"▸ {n}...")
        t0 = time.time()
        try: r = fn(goal, st)
        except Exception as e: r = f"⚠ {e}"
        results.append(r)
        s = str(r).split("\n")[0][:70] if r else "(خالی)"
        log(f"  → {s}  ({time.time()-t0:.1f}s)")
    print()

    print("  ┌─ [4/6] REFLECT ─────")
    fb = reflect(steps, results)
    log(f"امتیاز: {fb['score']}% ({fb['ok']}/{fb['total']})")
    for note in fb["notes"]: log(note)
    print()

    print("  ┌─ [5/6] LEARN ─────")
    mem = load_mem()
    mem["sessions"].append({"ts":datetime.now().isoformat(),"goal":goal,"score":fb["score"],"steps":[s[0] for s in steps]})
    mem["sessions"] = mem["sessions"][-50:]
    for name,_ in steps:
        if name not in mem["skills"]: mem["skills"][name] = {"used":0,"success":0}
        mem["skills"][name]["used"] += 1
        if fb["score"] >= 60: mem["skills"][name]["success"] += 1
    if fb["score"] >= 80:
        mem["insights"].append({"ts":datetime.now().isoformat(),"text":f"«{goal[:40]}» با {fb['score']}% حل شد"})
        mem["insights"] = mem["insights"][-20:]
    save_mem(mem)
    log(f"حافظه: {len(mem['sessions'])} session | {len(mem['skills'])} skill")
    print()

    print("  ┌─ [6/6] SUGGEST ─────")
    if st.get("resources",0) < 300: log("💡 منابع کمه — GET 2·2")
    if st.get("techniques",0) < 100: log("💡 تکنیک کم — LEARN 3·1")
    if st.get("nodes",0) < 500: log("💡 گراف کوچک — GET 2·3")
    if not any([st.get("resources",0)<300, st.get("techniques",0)<100, st.get("nodes",0)<500]):
        log("💡 همه‌چیز خوبه!")
    print()

    print("  ╔══════════════════════════════════════════════╗")
    print(f"  ║   ✓ چرخه کامل — امتیاز {fb['score']}%")
    print("  ╚══════════════════════════════════════════════╝")
    input("\n  ادامه...")

def history():
    os.system("clear")
    print("\n  === CORTEX — تاریخچه ===\n")
    mem = load_mem()
    for s in mem.get("sessions",[])[-15:]:
        ts = s["ts"][:16].replace("T"," ")
        bar = "█"*(s["score"]//10) + "░"*(10-s["score"]//10)
        print(f"  {ts}  {bar}  {s['score']:>3}%  {s['goal'][:50]}")
    print("\n  === Skills ===\n")
    for n,v in sorted(mem.get("skills",{}).items(), key=lambda x:-x[1]["used"]):
        rate = int(100*v["success"]/max(v["used"],1))
        print(f"  {n:12} used={v['used']:>3}  success={rate:>3}%")
    input("\n  ادامه...")

def main_menu():
    while True:
        os.system("clear")
        print("\n  ╔══════════════════════════════════════════════╗")
        print("  ║   ◆ CORTEX — ایجنت خودمختار                  ║")
        print("  ╚══════════════════════════════════════════════╝\n")
        print("  [1]  🎯 هدف جدید")
        print("  [2]  📚 تاریخچه")
        print("  [0]  بازگشت\n")
        try: c = input("  ❯ انتخاب: ").strip()
        except (EOFError, KeyboardInterrupt): return
        if c in ("0",""): return
        elif c == "1":
            try:
                g = input("\n  🎯 هدف: ").strip()
                if g: run_cycle(g)
            except (EOFError, KeyboardInterrupt): pass
        elif c == "2": history()

if __name__ == "__main__":
    main_menu()
