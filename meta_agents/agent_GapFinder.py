"""Auto-generated agent: GapFinder"""
import json
from datetime import datetime
from pathlib import Path

BASE = Path.home() / "evoscanner"

PURPOSE = 'پیدا کردن شکاف\u200cهای دانشی'
INPUTS = ['db', 'categories']
OUTPUTS = ['gaps']



def run(kb, graph):
    gaps = []
    cats = {c: n for c, n, _ in kb.categories_stats()}
    for c, n in cats.items():
        if c != "other" and n < 10:
            gaps.append({"category": c, "count": n})
    return {"gaps": gaps}



def report():
    print(f"Agent: GapFinder")
    print(f"Purpose: {PURPOSE}")
    print(f"Inputs: {INPUTS}")
    print(f"Outputs: {OUTPUTS}")


if __name__ == "__main__":
    report()
