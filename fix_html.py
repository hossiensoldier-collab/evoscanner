#!/usr/bin/env python3
"""رفع HTML escape در عناوین و محتوا"""
from pathlib import Path
import re

src = Path("evoscanner_v2.py")
code = src.read_text()

# افزودن html.unescape
if "import html" not in code:
    code = code.replace(
        "import hashlib, json, re, sqlite3, ssl, sys, time",
        "import hashlib, html, json, re, sqlite3, ssl, sys, time"
    )

# پاکسازی در KB.add
old_add = '''            self.conn.execute("INSERT INTO resources VALUES (?,?,?,?,?,?,?,?)",
                (h, url, title, content[:800], source, score, tags,
                 datetime.now().isoformat()))'''
new_add = '''            title = html.unescape(title)
            content = html.unescape(content)
            self.conn.execute("INSERT INTO resources VALUES (?,?,?,?,?,?,?,?)",
                (h, url, title, content[:800], source, score, tags,
                 datetime.now().isoformat()))'''

if old_add in code and "html.unescape(title)" not in code:
    code = code.replace(old_add, new_add)
    src.write_text(code)
    print("✓ رفع HTML escape اضافه شد")
else:
    print("! الگو یافت نشد یا از قبل اضافه شده")
