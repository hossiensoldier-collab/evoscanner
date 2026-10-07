import re, sys
from pathlib import Path
base = Path.home() / "evoscanner"
text = Path(sys.argv[1]).read_text(encoding="utf-8")
hdr = re.compile(r'^### `([^`]+)` \(\d+ lines\)$', re.M)
ms = list(hdr.finditer(text))
for i, m in enumerate(ms):
    end = ms[i+1].start() if i+1 < len(ms) else len(text)
    lines = text[m.end():end].strip("\n").split("\n")
    if lines and lines[0].startswith("```"): lines = lines[1:]
    if lines and lines[-1].strip() == "```": lines = lines[:-1]
    p = (base / m.group(1)).resolve()
    if not str(p).startswith(str(base)): continue
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(len(ms), "files written")
