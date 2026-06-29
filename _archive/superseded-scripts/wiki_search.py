#!/usr/bin/env python3
"""Full-text search over the second-brain wiki + raw sources.

SQLite FTS5, zero external dependencies. The index is rebuilt from the markdown
files on demand, so the .db is disposable.

Usage:
  python3 scripts/wiki_search.py --reindex            # (re)build the index
  python3 scripts/wiki_search.py "implicit distance"  # search
  python3 scripts/wiki_search.py -n 20 latent space   # more results
"""
import argparse
import os
import re
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "scripts", ".wiki_index.db")
SCAN_DIRS = [
    os.path.join(ROOT, "knowledge", "wiki"),
    os.path.join(ROOT, "knowledge", "raw"),
]


def iter_md():
    for base in SCAN_DIRS:
        for dirpath, _, files in os.walk(base):
            for name in files:
                if name.endswith(".md"):
                    yield os.path.join(dirpath, name)


def parse(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    title = os.path.splitext(os.path.basename(path))[0]
    m = re.search(r"^---\n(.*?)\n---\n", text, re.S)
    kind = "raw" if os.sep + "raw" + os.sep in path else "wiki"
    if m:
        fm = m.group(1)
        tm = re.search(r"^title:\s*(.+)$", fm, re.M)
        if tm:
            title = tm.group(1).strip()
        ty = re.search(r"^type:\s*(.+)$", fm, re.M)
        if ty:
            kind = ty.group(1).strip()
        body = text[m.end():]
    else:
        body = text
    return title, kind, body


def reindex():
    if os.path.exists(DB):
        os.remove(DB)
    con = sqlite3.connect(DB)
    con.execute(
        "CREATE VIRTUAL TABLE docs USING fts5("
        "path UNINDEXED, rel UNINDEXED, title, kind UNINDEXED, body)"
    )
    n = 0
    for path in iter_md():
        if os.path.basename(path).startswith("_"):
            continue
        title, kind, body = parse(path)
        rel = os.path.relpath(path, ROOT)
        con.execute(
            "INSERT INTO docs (path, rel, title, kind, body) VALUES (?,?,?,?,?)",
            (path, rel, title, kind, body),
        )
        n += 1
    con.commit()
    con.close()
    print(f"indexed {n} notes -> {os.path.relpath(DB, ROOT)}")


def search(query, limit):
    if not os.path.exists(DB):
        reindex()
    con = sqlite3.connect(DB)
    # FTS5 MATCH. Quote each term (tolerates punctuation) and AND them together.
    # A fully-quoted "phrase" is honored if the user passes one.
    if query.startswith('"') and query.endswith('"') and len(query) > 1:
        q = '"' + query.strip('"').replace('"', '""') + '"'
    else:
        terms = [t for t in query.split() if t]
        q = " ".join('"' + t.replace('"', '""') + '"' for t in terms) or '""'
    try:
        rows = con.execute(
            "SELECT rel, title, kind, snippet(docs, 4, '>>', '<<', ' … ', 12) "
            "FROM docs WHERE docs MATCH ? ORDER BY rank LIMIT ?",
            (q, limit),
        ).fetchall()
    except sqlite3.OperationalError as e:
        print(f"query error: {e}", file=sys.stderr)
        sys.exit(2)
    con.close()
    if not rows:
        print("no matches")
        return
    for rel, title, kind, snip in rows:
        print(f"\n[{kind}] {title}\n  {rel}\n  … {snip.strip()}")


def main():
    ap = argparse.ArgumentParser(description="Search the second-brain wiki.")
    ap.add_argument("query", nargs="*", help="search terms")
    ap.add_argument("--reindex", action="store_true", help="rebuild the index and exit")
    ap.add_argument("-n", type=int, default=10, help="max results (default 10)")
    args = ap.parse_args()
    if args.reindex:
        reindex()
        return
    if not args.query:
        ap.print_help()
        return
    search(" ".join(args.query), args.n)


if __name__ == "__main__":
    main()
