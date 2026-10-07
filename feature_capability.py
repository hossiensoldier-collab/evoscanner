"""Capability Predictor — تخمین توانایی نهایی دستگاه + پایگاه"""
import json
import os
import shutil
import socket
import subprocess
import time
from pathlib import Path

BASE = Path.home() / "evoscanner"


def cpu_cores():
    try:
        return os.cpu_count() or 1
    except Exception:
        return 1


def cpu_info():
    try:
        r = subprocess.run(["getprop", "ro.product.cpu.abi"],
                           capture_output=True, text=True, timeout=3)
        if r.stdout.strip():
            return r.stdout.strip()
    except Exception:
        pass
    return "unknown"


def ram_mb():
    """تخمین RAM با /proc/meminfo"""
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    kb = int(line.split()[1])
                    return kb // 1024
    except Exception:
        pass
    return 0


def ram_available_mb():
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemAvailable:"):
                    kb = int(line.split()[1])
                    return kb // 1024
    except Exception:
        pass
    return 0


def disk_info():
    try:
        r = shutil.disk_usage(str(BASE))
        return {
            "total_gb": r.total // (1024 ** 3),
            "used_gb": r.used // (1024 ** 3),
            "free_gb": r.free // (1024 ** 3),
        }
    except Exception:
        return {"total_gb": 0, "used_gb": 0, "free_gb": 0}


def db_size_mb():
    try:
        return (BASE / "knowledge.db").stat().st_size // (1024 * 1024)
    except Exception:
        return 0


def graph_size_mb():
    try:
        return (BASE / "graph.json").stat().st_size // (1024 * 1024)
    except Exception:
        return 0


def predict():
    """پیش‌بینی توانایی نهایی"""
    cores = cpu_cores()
    ram = ram_mb()
    ram_avail = ram_available_mb()
    disk = disk_info()
    db_size = db_size_mb()
    g_size = graph_size_mb()
    arch = cpu_info()

    # محدودیت‌های عملی روی Termux
    # RAM 256MB per Python process → max concurrent
    max_procs = max(1, ram_avail // 256) if ram_avail else 2

    # DB تقریباً 4KB per resource → تخمین
    max_resources_db = int(disk["free_gb"] * 1024 * 1024 * 0.3)  # 30% for db

    # گراف: ~2KB per node
    max_graph_nodes = int(disk["free_gb"] * 1024 * 1024 * 0.5)  # 50%

    # زمان‌بندی: ~12s per cycle (بدون enrich)
    cycles_per_hour = 300

    # منابع کل موجود در ایران (تقریب)
    total_available_sources = 500000  # GitHub + arXiv + SO + ...

    # نرخ کشف فعلی (تقریبی از تاریخچه)
    discovery_rate = 16  # per cycle (میانگین)

    # اشباع: چقدر طول می‌کشد تا به 80% منابع برسیم
    target = total_available_sources * 0.8
    current_resources = 288
    remaining = target - current_resources
    cycles_to_saturation = remaining / discovery_rate if discovery_rate else 0

    # دانش: ~15% of resources become techniques
    est_techniques = int(current_resources * 0.15 * 10)  # عمیق‌تر
    est_snippets = int(current_resources * 0.5)

    return {
        "hardware": {
            "arch": arch,
            "cores": cores,
            "ram_total_mb": ram,
            "ram_available_mb": ram_avail,
            "disk_total_gb": disk["total_gb"],
            "disk_free_gb": disk["free_gb"],
        },
        "current": {
            "db_mb": db_size,
            "graph_mb": g_size,
            "resources": current_resources,
        },
        "limits": {
            "max_concurrent_procs": max_procs,
            "max_db_resources": max_resources_db,
            "max_graph_nodes": max_graph_nodes,
            "cycles_per_hour": cycles_per_hour,
        },
        "prediction": {
            "discovery_rate_per_cycle": discovery_rate,
            "total_available_sources": total_available_sources,
            "current_coverage_pct": round(
                current_resources / total_available_sources * 100, 4),
            "cycles_to_saturation": int(cycles_to_saturation),
            "days_to_saturation": round(cycles_to_saturation / cycles_per_hour / 24, 1),
            "est_techniques_at_saturation": est_techniques,
            "est_snippets_at_saturation": est_snippets,
        },
        "knowledge_layers": {
            "L0_data": current_resources,
            "L1_facts": current_resources,
            "L2_relations": 1557,
            "L3_patterns": "~40 (در حال ساخت)",
            "L4_rules": "~10 (در حال ساخت)",
        },
        "certainty": {
            "prediction_confidence": 0.65,
            "asymptotic_ceiling": 0.95,
            "note": "پیش‌بینی با عدم قطعیت همراه است؛ با افزایش داده دقیق‌تر می‌شود",
        },
    }


def report():
    p = predict()
    hw = p["hardware"]
    cur = p["current"]
    lim = p["limits"]
    pr = p["prediction"]
    kl = p["knowledge_layers"]
    ce = p["certainty"]

    print()
    print("=" * 60)
    print("  پیش‌بینی توانایی دستگاه و پایگاه")
    print("=" * 60)
    print()

    print("  🖥  سخت‌افزار:")
    print(f"    Arch:           {hw['arch']}")
    print(f"    CPU cores:      {hw['cores']}")
    print(f"    RAM total:      {hw['ram_total_mb']} MB")
    print(f"    RAM available:  {hw['ram_available_mb']} MB")
    print(f"    Disk total:     {hw['disk_total_gb']} GB")
    print(f"    Disk free:      {hw['disk_free_gb']} GB")
    print()

    print("  📊 فعلی:")
    print(f"    Resources:      {cur['resources']}")
    print(f"    DB size:        {cur['db_mb']} MB")
    print(f"    Graph size:     {cur['graph_mb']} MB")
    print()

    print("  ⚡ محدودیت‌های عملی:")
    print(f"    Max procs:      {lim['max_concurrent_procs']}")
    print(f"    Max DB rows:    {lim['max_db_resources']:,}")
    print(f"    Max graph nodes:{lim['max_graph_nodes']:,}")
    print(f"    Cycles/hour:    {lim['cycles_per_hour']}")
    print()

    print("  🔮 پیش‌بینی:")
    print(f"    Discovery rate: {pr['discovery_rate_per_cycle']} per cycle")
    print(f"    Total available:{pr['total_available_sources']:,}")
    print(f"    Coverage:       {pr['current_coverage_pct']}%")
    print(f"    Cycles to 80%:  {pr['cycles_to_saturation']:,}")
    print(f"    Days to 80%:    {pr['days_to_saturation']} (24/7)")
    print(f"    Est. techniques:{pr['est_techniques_at_saturation']:,}")
    print(f"    Est. snippets:  {pr['est_snippets_at_saturation']:,}")
    print()

    print("  🧠 لایه‌های دانش:")
    for k, v in kl.items():
        print(f"    {k:18s} {v}")
    print()

    print("  🎯 قطعیت پیش‌بینی:")
    print(f"    فعلی:           {ce['prediction_confidence']*100:.0f}%")
    print(f"    سقف مجانب:      {ce['asymptotic_ceiling']*100:.0f}%")
    print(f"    {ce['note']}")
    print()


if __name__ == "__main__":
    report()

