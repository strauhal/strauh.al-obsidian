#!/usr/bin/env python3
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path


VAULT = Path(__file__).resolve().parents[1]
WIKI = VAULT / "knowledge" / "wiki"
OUTPUT = VAULT / "knowledge" / "output"
DB = OUTPUT / "wiki-search.sqlite"


def rebuild(conn: sqlite3.Connection) -> None:
    conn.execute("drop table if exists notes")
    conn.execute("create virtual table notes using fts5(title, path, body)")
    rows = []
    for path in sorted(WIKI.rglob("*.md")):
        text = path.read_text(errors="ignore")
        rows.append((path.stem, str(path.relative_to(VAULT)), text))
    conn.executemany("insert into notes(title, path, body) values (?, ?, ?)", rows)
    conn.commit()


def search(conn: sqlite3.Connection, query: str, limit: int = 20) -> list[tuple[str, str, str]]:
    sql = """
        select title, path, snippet(notes, 2, '**', '**', ' ... ', 18)
        from notes
        where notes match ?
        order by bm25(notes)
        limit ?
    """
    return list(conn.execute(sql, (query, limit)))


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    query = " ".join(sys.argv[1:]).strip()
    with sqlite3.connect(DB) as conn:
        rebuild(conn)
        if not query:
            print(f"Indexed wiki into {DB}")
            print('Run: python3 tools/wiki_search.py "query"')
            return
        rows = search(conn, query)
    if not rows:
        print("No matches.")
        return
    for title, path, snippet in rows:
        print(f"- {title} ({path})")
        print(f"  {snippet}")


if __name__ == "__main__":
    main()
