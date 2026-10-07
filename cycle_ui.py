#!/usr/bin/env python3
"""Cycle UI v4 — استفاده از clear سیستمی"""
import os
import re
import subprocess
import sys
import time
from pathlib import Path

BASE = Path.home() / "evoscanner"
LOG = BASE / "cycle.log"

R="\033[0;31m"; G="\033[0;32m"; Y="\033[1;33m"
Cy="\033[0;36m"; W="\033[1;37m"; D="\033[0m"
Bold="\033[1m"; Dim="\033[2m"

STEPS = [
    ("reset",   "Reset Health",     ["reset-health"],      1),
    ("run",     "Discovery",        ["run", "2"],          5),
    ("enrich",  "Enrich READMEs",   ["enrich", "50"],      3),
    ("rebuild", "Rebuild Graph",    ["rebuild"],           1),
    ("learn",   "Learn",            ["learn", "extract"],  2),
    ("agents",  "Agents",           ["agents"],            1),
    ("export",  "Export",           ["export"],            1),
]
TOTAL_W = sum(s[3] for s in STEPS)

LOGO = (
    "  ####  #   #  ####   ####  ####   ##   #   # ##### ##### ####\n"
    "  #     #   # #    # #     #     #   #  ##  # #     #     #   #\n"
    "  ###   #   # #    # ###   ###   #####  # # # ###   ###   ####\n"
    "  #      # #  #    # #     #     #   #  #  ## #     #     #  #\n"
    "  ####    #    ####   ####  ####  #   #  #   # ##### ##### #   #"
)


def fmt(t):
    t = int(max(0, t))
    if t < 60:
        return f"{t}s"
    m, s = divmod(t, 60)
    return f"{m}m{s}s" if m < 60 else f"{m//60}h{m%60}m"


def bar(pct, width=40):
    pct = max(0, min(100, pct))
    fill = int(width * pct / 100)
    col = R if pct < 30 else (Y if pct < 70 else G)
    return col + "#" * fill + Dim + "." * (width - fill) + D


def tail_new(path, pos):
    if not path.exists():
        return [], pos
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            f.seek(pos)
            lines = f.readlines()
            return lines, f.tell()
    except Exception:
        return [], pos


def initial_stats():
    s = {"total": 0, "tech": 0, "snip": 0, "gfx": 0}
    try:
        import sqlite3
        db = sqlite3.connect(BASE / "knowledge.db")
        s["total"] = db.execute(
            "SELECT COUNT(*) FROM resources").fetchone()[0]
        for key, tbl in (("tech", "techniques"), ("snip", "snippets"),
                         ("gfx", "graphics_topics")):
            try:
                s[key] = db.execute(
                    f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
            except Exception:
                pass
        db.close()
    except Exception:
        pass
    return s


def draw(step_idx, label, elapsed, stats, recent, marks):
    os.system("clear")
    print(Cy + LOGO + D)
    print(Dim + "  Auto Cycle Runner v4" + D)
    print()

    done_w = sum(STEPS[i][3] for i in range(step_idx))
    cur_w = STEPS[step_idx][3] if step_idx < len(STEPS) else 0
    frac = min(1.0, elapsed / max(cur_w * 25, 1))
    pct = (done_w + cur_w * frac) / TOTAL_W * 100

    print(f"  {Dim}Progress:{D}  {bar(pct, 40)}  "
          f"{Bold}{W}{pct:5.1f}%{D}")
    print()
    print(f"  {Bold}{Cy}Step:{D}  {W}{label}{D}")
    print()

    speed = stats.get("new", 0) / max(elapsed / 60, 0.1) if elapsed > 3 else 0

    print(f"  {Cy}+---------------------------------------+{D}")
    print(f"  {Cy}|{D} {Y}New resources:{D}  "
          f"{W}{Bold}{stats['new']:>5d}{D}                 {Cy}|{D}")
    print(f"  {Cy}|{D} {Y}Total:{D}          "
          f"{W}{Bold}{stats['total']:>5d}{D}                 {Cy}|{D}")
    print(f"  {Cy}|{D} {Y}Techniques:{D}     "
          f"{G}{stats['tech']:>5d}{D}                 {Cy}|{D}")
    print(f"  {Cy}|{D} {Y}Snippets:{D}       "
          f"{G}{stats['snip']:>5d}{D}                 {Cy}|{D}")
    print(f"  {Cy}|{D} {Y}Graphics:{D}       "
          f"{G}{stats['gfx']:>5d}{D}                 {Cy}|{D}")
    print(f"  {Cy}|{D} {Y}Speed:{D}          "
          f"{G}{speed:>5.1f}{D}/min             {Cy}|{D}")
    print(f"  {Cy}|{D} {Y}Elapsed:{D}        "
          f"{W}{fmt(elapsed):>9s}{D}             {Cy}|{D}")
    print(f"  {Cy}+---------------------------------------+{D}")
    print()

    if recent:
        print(f"  {Dim}Latest log:{D}")
        shown = 0
        for line in reversed(recent):
            line = line.strip()
            if not line:
                continue
            if any(x in line for x in ("+ [", "تکنیک", "جدید:", "graphics", "OK")):
                print(f"    {Dim}>{D} {line[:58]}")
                shown += 1
                if shown >= 3:
                    break
    print()
    print(f"  {Dim}Steps:{D}  " + "  ".join(marks))
    sys.stdout.flush()


def run():
    LOG.write_text("")
    log_pos = 0
    stats = initial_stats()
    stats["new"] = 0
    recent = []
    t_start = time.time()

    for idx, (name, label, cmd, weight) in enumerate(STEPS):
        t0 = time.time()
        est = weight * 25

        proc = subprocess.Popen(
            [sys.executable, "evoscanner_v2.py"] + cmd,
            cwd=str(BASE),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        while proc.poll() is None:
            elapsed = time.time() - t0
            lines, log_pos = tail_new(LOG, log_pos)
            recent.extend(lines)
            recent = recent[-40:]

            for l in lines:
                m = re.search(r"جدید:\s*(\d+)", l)
                if m:
                    stats["new"] += int(m.group(1))
                m = re.search(r"کل:\s*(\d+)", l)
                if m:
                    try:
                        stats["total"] = int(m.group(1))
                    except Exception:
                        pass
                m = re.search(r"تکنیک:\s*(\d+)", l)
                if m:
                    stats["tech"] = max(stats["tech"], int(m.group(1)))
                m = re.search(r"کد:\s*(\d+)", l)
                if m:
                    stats["snip"] = max(stats["snip"], int(m.group(1)))
                m = re.search(r"graphics topics:\s*(\d+)", l)
                if m:
                    stats["gfx"] = max(stats["gfx"], int(m.group(1)))

            marks = []
            for i, s in enumerate(STEPS):
                if i < idx:
                    marks.append(G + "[x]" + D)
                elif i == idx:
                    sp = "|/-\\"[int(time.time() * 4) % 4]
                    marks.append(Y + "[" + sp + "]" + D)
                else:
                    marks.append(Dim + "[ ]" + D)

            draw(idx, label, elapsed, stats, recent, marks)
            time.sleep(1.5)

        proc.wait()

    total_elapsed = time.time() - t_start
    os.system("clear")
    print(Cy + LOGO + D)
    print()
    print(f"  {G}{Bold}Cycle complete!{D}")
    print()
    print(f"  {Cy}+---------------------------------------+{D}")
    print(f"  {Cy}|{D} {Y}Total time:{D}     "
          f"{W}{Bold}{fmt(total_elapsed):>9s}{D}             {Cy}|{D}")
    print(f"  {Cy}|{D} {Y}New resources:{D}  "
          f"{G}{Bold}{stats['new']:>9d}{D}             {Cy}|{D}")
    print(f"  {Cy}|{D} {Y}Total:{D}          "
          f"{W}{Bold}{stats['total']:>9d}{D}             {Cy}|{D}")
    print(f"  {Cy}|{D} {Y}Techniques:{D}     "
          f"{G}{stats['tech']:>9d}{D}             {Cy}|{D}")
    print(f"  {Cy}|{D} {Y}Snippets:{D}       "
          f"{G}{stats['snip']:>9d}{D}             {Cy}|{D}")
    print(f"  {Cy}|{D} {Y}Graphics:{D}       "
          f"{G}{stats['gfx']:>9d}{D}             {Cy}|{D}")
    print(f"  {Cy}+---------------------------------------+{D}")
    print()


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        os.system("clear")
        print(f"\n  {Y}Cancelled{D}\n")
        sys.exit(1)

