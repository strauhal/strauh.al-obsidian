#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


VAULT = Path(__file__).resolve().parents[1]


def run(*args: str) -> None:
    command = [sys.executable, *args]
    print(f"\n> {' '.join(command)}")
    subprocess.run(command, cwd=VAULT, check=True)


def main() -> None:
    run("tools/wiki_compile.py")
    run("tools/wiki_books.py")
    run("tools/wiki_culture.py")
    run("tools/wiki_dream_journal.py")
    run("tools/wiki_chatgpt_import.py")
    run("tools/wiki_chatgpt_memory_compile.py")
    run("tools/wiki_friend_paper.py")
    run("tools/wiki_fanmail.py")
    run("tools/wiki_polish.py")
    run("tools/wiki_archive_stale.py")
    run("tools/wiki_anchor_missing.py")
    run("tools/wiki_crosslink.py")
    run("tools/wiki_living_graph_index.py")
    run("tools/wiki_concept_links.py")
    run("tools/wiki_knowledge_base.py")
    run("tools/wiki_quotes.py")
    run("tools/wiki_lint.py")
    run("tools/wiki_search.py")
    run("tools/wiki_graph3d.py")
    run("tools/wiki_browser_graph.py")
    print("\nVault refresh complete.")


if __name__ == "__main__":
    main()
