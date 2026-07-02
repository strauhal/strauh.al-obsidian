# Site Sync Log

## 2026-07-01

**Baseline established.** No prior state file (`knowledge/output/site-sync-state.json`) existed, so this run recorded the current HEAD commit of each site repo as the starting point. No prior state to diff against — commit-level diffing for the three site repos is skipped this run and will resume next month.

Baseline commits recorded:
- `computerdrawing.club` — `c737502716b3af2c51e82b58676efcc63bbb1dbf`
- `strauh.al3.1` — `687fca447713e841bd9691f2b32a4170f471ada0`
- `strauh.al4` — `f42161f7d2140b0a392a68175a0f1a0452c5c9af`

All three site repos were already at these commits locally (fetch found nothing new to pull).

### Vault sync (`tools/wiki_refresh.py`)

Ran the full pipeline (`wiki_compile` → `wiki_browser_graph`) against the current on-disk state of `strauh.al4` and `strauh.al3.1`. Result: 74 HTML pages and 8,116 images compiled (up from 7,598 images tracked previously), 9,944 total vault notes (up from 9,371).

`git diff --stat` inside the vault after the run showed roughly 10,900 modified files and 579 new files, almost entirely under `knowledge/wiki/` and `_archive/auto-generated/`. The bulk of the modified count is expected pipeline churn (every note's `updated:` frontmatter date and its auto-generated "Discovered Connections" crosslink block get rewritten each run), not content loss. New files: 518 new image notes, 55 new artist notes, 1 new page, 1 new anchor note.

Two pipeline steps could not complete in this run's environment and were skipped (existing output left untouched, nothing lost):
- `wiki_books.py` — its fallback input path lives outside the synced folder (an iCloud "Readings" folder plus a one-off `.codex/attachments` file) and wasn't reachable from this automation context.
- `wiki_search.py` — hit a `disk I/O error` mid-rebuild in this environment; a leftover `.sqlite-journal` file was found and cleared, and the existing search index (9,910 notes) was confirmed intact and readable, but the index was not refreshed with this run's new content.

Both should run cleanly next time this job executes with full filesystem access (e.g. directly on Ernest's machine rather than this sandboxed run). Worth a manual re-run of `wiki_books.py` and `wiki_search.py` if the search index / library needs to be current sooner.

### computerdrawing.club

First run — no prior sync point, so no commit-level diff was produced. Repo is at `c737502716b3af2c51e82b58676efcc63bbb1dbf`. Future runs will report commits/files changed since this baseline.

### Skipped repos

None — all four repos were reachable and processed (fetch/pull succeeded on all three site repos as fast-forwards or no-ops).

### Notes

- `strauh.al3.1` had a pre-existing local `.DS_Store` modification. It was stashed for safety; the stash could not be automatically popped back due to a filesystem restriction in this run's environment (see below), so it remains saved as `stash@{0}` in that repo, unapplied but not lost.
- The `obsidian` repo had pre-existing uncommitted local edits (`.obsidian/graph.json`, `build-graph-html.py`, a pending deletion of `obsidian-graph.html`, and an untracked `brain.html`) from Ernest's own work in progress. These were left exactly as they were and were **not** included in this run's commit.
- This automation environment enforces a no-delete policy on the connected GitHub folder, which is generally good safety behavior but caused some git plumbing (lockfile/journal cleanup that normally happens via delete) to need manual workarounds this run. Noting here in case it recurs.
