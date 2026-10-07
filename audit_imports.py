import ast
import json
from pathlib import Path

root = Path(".").resolve()
excluded = {".git", "__pycache__", ".venv", "venv", "exports"}
files = sorted(
    p for p in root.rglob("*.py")
    if not excluded.intersection(p.parts)
)

modules = {}
for path in files:
    rel = path.relative_to(root).with_suffix("")
    parts = list(rel.parts)
    if parts[-1] == "__init__":
        parts.pop()
    modules[".".join(parts)] = path

edges = []
errors = []

for module, path in sorted(modules.items()):
    try:
        tree = ast.parse(
            path.read_text(encoding="utf-8"),
            filename=str(path)
        )
    except (SyntaxError, UnicodeError) as exc:
        errors.append({
            "file": str(path.relative_to(root)),
            "error": str(exc)
        })
        continue

    package = module.split(".")[:-1]
    for node in ast.walk(tree):
        targets = []

        if isinstance(node, ast.Import):
            targets = [a.name for a in node.names]

        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                prefix = package[:len(package) - node.level + 1]
                base = ".".join(prefix + ([base] if base else []))
            targets = [base] if base else []
            targets += [
                f"{base}.{a.name}" for a in node.names
                if a.name != "*"
            ]

        for target in targets:
            local = target
            while local and local not in modules:
                local = local.rpartition(".")[0]
            if local in modules:
                edges.append({
                    "from": module,
                    "to": local,
                    "line": getattr(node, "lineno", None)
                })

result = {
    "schema": "evoscanner.import_audit.v1",
    "python_files": len(files),
    "local_import_edges": sorted(
        edges, key=lambda e: (e["from"], e["to"], e["line"] or 0)
    ),
    "parse_errors": errors,
}
out = root / "import_graph.json"
out.write_text(json.dumps(result, indent=2), encoding="utf-8")

print("Python files:", len(files))
print("Local import edges:", len(edges))
print("Parse errors:", len(errors))
print("Report:", out)
for e in errors:
    print("PARSE ERROR:", e["file"], e["error"])
