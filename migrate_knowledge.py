"""افزودن جداول دانش به knowledge.db"""
import sqlite3
from pathlib import Path

DB = Path.home() / "evoscanner" / "knowledge.db"
conn = sqlite3.connect(DB)

conn.executescript("""
CREATE TABLE IF NOT EXISTS techniques (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT, category TEXT, description TEXT, code TEXT,
    source_hash TEXT, source_url TEXT, difficulty TEXT,
    prerequisites TEXT, lang TEXT DEFAULT 'python',
    extracted_at TEXT, UNIQUE(name, source_hash));

CREATE TABLE IF NOT EXISTS concepts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE, description TEXT, category TEXT,
    difficulty TEXT, prerequisites TEXT, related TEXT, source_hash TEXT);

CREATE TABLE IF NOT EXISTS snippets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_hash TEXT, source_url TEXT, lang TEXT, purpose TEXT,
    code TEXT, lines INTEGER, extracted_at TEXT,
    UNIQUE(source_hash, code));

CREATE TABLE IF NOT EXISTS learn_paths (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT, level TEXT, step INTEGER, title TEXT, description TEXT,
    resource_url TEXT, source_hash TEXT, completed INTEGER DEFAULT 0,
    UNIQUE(topic, level, step));

CREATE TABLE IF NOT EXISTS graphics_topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT, subtopic TEXT, level TEXT, description TEXT,
    code TEXT, source_url TEXT, library TEXT,
    UNIQUE(topic, subtopic, library, source_url));

CREATE TABLE IF NOT EXISTS learn_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT, topic TEXT, difficulty TEXT, count INTEGER);

CREATE INDEX IF NOT EXISTS idx_tech_cat ON techniques(category);
CREATE INDEX IF NOT EXISTS idx_snip_src ON snippets(source_hash);
CREATE INDEX IF NOT EXISTS idx_path_topic ON learn_paths(topic);
CREATE INDEX IF NOT EXISTS idx_gfx_topic ON graphics_topics(topic);
""")

conn.commit()
print("✓ جداول جدید اضافه شدند")
for t in ("techniques","concepts","snippets","learn_paths","graphics_topics"):
    n = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"  {t}: {n}")
conn.close()
