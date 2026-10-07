"""Auto-generated agent: QualityRanker"""
import json
from datetime import datetime
from pathlib import Path

BASE = Path.home() / "evoscanner"

PURPOSE = 'رتبه\u200cبندی کیفیت منابع'
INPUTS = ['db']
OUTPUTS = ['ranking']



def run(kb, graph):
    rows = kb.conn.execute(
        "SELECT title, score FROM resources ORDER BY score DESC LIMIT 20"
    ).fetchall()
    return {"top": [{"title": t, "score": s} for t, s in rows]}



def report():
    print(f"Agent: QualityRanker")
    print(f"Purpose: {PURPOSE}")
    print(f"Inputs: {INPUTS}")
    print(f"Outputs: {OUTPUTS}")


if __name__ == "__main__":
    report()
