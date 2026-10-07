"""Auto-generated agent: PatternFinder"""
import json
from datetime import datetime
from pathlib import Path

BASE = Path.home() / "evoscanner"

PURPOSE = 'پیدا کردن الگوهای مشترک در منابع'
INPUTS = ['db', 'graph']
OUTPUTS = ['patterns']



def run(kb, graph):
    # تحلیل co-occurrence
    patterns = []
    cooc = graph.get("cooc", {})
    for pair, w in sorted(cooc.items(), key=lambda x: -x[1])[:20]:
        a, b = pair.split("|", 1)
        if a.startswith("cat:") or b.startswith("cat:"):
            continue
        if w >= 3:
            patterns.append({"a": a, "b": b, "weight": w})
    return {"patterns": patterns}



def report():
    print(f"Agent: PatternFinder")
    print(f"Purpose: {PURPOSE}")
    print(f"Inputs: {INPUTS}")
    print(f"Outputs: {OUTPUTS}")


if __name__ == "__main__":
    report()
