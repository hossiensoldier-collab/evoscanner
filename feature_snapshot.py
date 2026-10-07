"""Project Snapshot - بسته کامل برای AI"""
import json
import os
import re
from datetime import datetime
from pathlib import Path

BASE = Path.home() / "evoscanner"
OUT = BASE / "snapshots"
OUT.mkdir(exist_ok=True)

# فایل‌هایی که کپی می‌شوند
EXT = {".py", ".md", ".txt", ".json", ".sh"}

# نادیده گرفته‌شده‌ها
SKIP_DIRS = {
    "__pycache__", ".git", "node_modules", "archive",
    "agent_backups", "meta_backups", "upgrade_backups",
    "exports", "snapshots", "ai_prompts", "kb_data",
    "meta_agents", "ssh_keys", "server", "features",
}

BIG_FILES = {
    "deps_graph.json", "causal_graph.json", "graph.json",
    "knowledge.db", "curiosity.json",
}

SKIP_FILES = {
    ".env", ".agent.json", ".auth.json", ".net.json",
    ".proxies.json", ".ssh_hosts.json", ".worker.json",
    "knowledge.db", "graph.json", "daemon.log", "api.log",
    "cycle.log", "auto.log", "task_log.json", "agent_log.json",
    "meta_log.json", "agents.json", "health.json",
    "evolution.json", "user_snippets.json",
    "panel_config.json", "panel_history.json",
    "panel_bookmarks.json", "upgrade_history.json",
    "learned_queries.json",
    "panel_good.py", "panel_works.py",
    "fix_403.py", "fix_html.py", "fix_network.py",
    "fix_offline.py", "fix_reddit.py", "fix_explorer.py",
    "fix_v12.py", "migrate_knowledge.py",
    "file.py",  # فایل خالی
}

# ماسک توکن‌ها
PATTERNS = [
    (re.compile(r"gsk_[A-Za-z0-9]{20,}"), "gsk_MASKED_KEY"),
    (re.compile(r"sk-or-v1-[A-Za-z0-9]{20,}"), "sk-or-v1-MASKED"),
    (re.compile(r"ghp_[A-Za-z0-9]{20,}"), "ghp_MASKED_TOKEN"),
    (re.compile(r"github_pat_[A-Za-z0-9_]{20,}"), "github_pat_MASKED"),
    (re.compile(r"sk-[A-Za-z0-9]{30,}"), "sk-MASKED"),
]


def mask(text):
    for pat, repl in PATTERNS:
        text = pat.sub(repl, text)
    return text


def should_include(f):
    if f.name in SKIP_FILES:
        return False
    if f.name in BIG_FILES:
        return False
    try:
        if f.stat().st_size > 500 * 1024:
            return False
    except Exception:
        pass
    if f.name.startswith("."):
        return False
    return f.suffix in EXT


def collect():
    files = []
    for root, dirs, names in os.walk(BASE):
        dirs[:] = [d for d in dirs
                   if d not in SKIP_DIRS and not d.startswith(".")]
        for name in names:
            f = Path(root) / name
            if not should_include(f):
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
                files.append({
                    "path": str(f.relative_to(BASE)),
                    "lines": text.count("\n"),
                    "content": mask(text),
                })
            except Exception as e:
                print(f"  skip {name}: {e}")
    return files


def stats():
    st = {"version": "3.0.0", "resources": 0, "graph_nodes": 0,
          "graph_edges": 0, "techniques": 0, "snippets": 0}
    vf = BASE / "version.txt"
    if vf.exists():
        st["version"] = vf.read_text().strip()
    try:
        import sqlite3
        db = sqlite3.connect(BASE / "knowledge.db")
        st["resources"] = db.execute(
            "SELECT COUNT(*) FROM resources").fetchone()[0]
        for k, t in [("techniques", "techniques"),
                     ("snippets", "snippets")]:
            try:
                st[k] = db.execute(
                    f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            except Exception:
                pass
        db.close()
    except Exception:
        pass
    try:
        g = json.loads((BASE / "graph.json").read_text())
        st["graph_nodes"] = sum(1 for v in g["nodes"].values()
                                 if v.get("type") == "entity")
        st["graph_edges"] = len(g.get("edges", {}))
    except Exception:
        pass
    return st


def build():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    st = stats()

    print()
    print("=" * 60)
    print("  EvoScanner - Snapshot Builder")
    print("=" * 60)
    print()

    print("  [1/3] collect files...")
    files = collect()
    print(f"        {len(files)} files")

    print("  [2/3] build readme...")

    readme_parts = [
        "# EvoScanner - Complete Snapshot",
        "",
        f"**Generated:** {datetime.now():%Y-%m-%d %H:%M}",
        f"**Version:** v{st['version']}",
        "",
        "## Current State",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Resources | {st['resources']} |",
        f"| Graph nodes | {st['graph_nodes']} |",
        f"| Graph edges | {st['graph_edges']} |",
        f"| Techniques | {st['techniques']} |",
        f"| Snippets | {st['snippets']} |",
        f"| Files | {len(files)} |",
        "",
        "## How to Use",
        "",
        "This snapshot contains all project files with masked tokens.",
        "",
        "**To REBUILD in another AI:**",
        "1. Give this .md file to any AI assistant",
        "2. Ask: 'extract all code to ~/evoscanner/'",
        "3. The AI will give `cat > file.py << PYEOF` blocks",
        "",
        "**To UPGRADE:**",
        "AI has full context, can suggest patches.",
        "",
        "---",
        "",
        "## FILE CONTENTS",
        "",
    ]

    print("  [3/3] write files...")
    lines = list(readme_parts)

    for f in files:
        lines.append(f"\n### `{f['path']}` ({f['lines']} lines)\n")
        ext = Path(f["path"]).suffix
        lang = {"py": "python", "sh": "bash",
                "json": "json", "md": "markdown"}.get(ext.lstrip("."), "")
        lines.append("```" + lang)
        lines.append(f["content"])
        lines.append("```\n")

    md_text = "\n".join(lines)
    md_file = OUT / f"snapshot_{ts}.md"
    md_file.write_text(md_text, encoding="utf-8")

    # JSON
    json_data = {
        "meta": {"ts": ts, "version": st["version"],
                 "stats": st, "files_count": len(files)},
        "files": files,
    }
    json_file = OUT / f"snapshot_{ts}.json"
    json_file.write_text(
        json.dumps(json_data, ensure_ascii=False, indent=2),
        encoding="utf-8")

    print()
    print("=" * 60)
    print("  OK - Snapshot ready")
    print("=" * 60)
    print()
    print(f"  MD   : {md_file.name}  ({md_file.stat().st_size // 1024} KB)")
    print(f"  JSON : {json_file.name}  ({json_file.stat().st_size // 1024} KB)")
    print()
    print(f"  PATH: {md_file}")
    print()
    return md_file


def list_snaps():
    files = sorted(OUT.glob("snapshot_*.md"), reverse=True)
    if not files:
        print("  (empty)")
        return
    print()
    for f in files[:20]:
        print(f"  {f.name}  ({f.stat().st_size // 1024} KB)")
    print()


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    if cmd == "build":
        build()
    elif cmd == "list":
        list_snaps()

