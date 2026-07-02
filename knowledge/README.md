# strauh.al Obsidian Knowledge Base

This vault turns the local `strauh.al` archives into an Obsidian wiki:

- HTML sources: `/Users/erneststrauhal/GitHub/strauh.al4`
- Image sources: `/Users/erneststrauhal/GitHub/strauh.al3.1`
- Compiled wiki: `knowledge/wiki/`
- Reports and search index: `knowledge/output/`
- Source media links: `media/`
- Linked reading library: `/Users/erneststrauhal/Library/Mobile Documents/com~apple~CloudDocs/Readings`

The image archive is not copied into this vault. The `media/` folder uses local symlinks so Obsidian can render the existing files without duplicating roughly 15 GB of images.

## Commands

Rebuild the generated wiki:

```sh
python3 tools/wiki_refresh.py
```

This runs the archive compiler, books importer, polish pass, missing-link anchors,
health check, and search indexing in the correct order.

Check the wiki:

```sh
python3 tools/wiki_lint.py
```

Search it:

```sh
python3 tools/wiki_search.py "moebius"
```

## Living Graph

Open **Living Graph** from Obsidian's left ribbon. The plugin uses
`knowledge/output/living-graph-index.json`, generated during every vault refresh.

- Click the waypoints ribbon icon and speak to rearrange the active memory field.
- Speech is transcribed locally with `whisper.cpp`; no network recognizer is used.
- Use Obsidian's normal hover, click, drag, zoom, and graph settings.
- Private correspondence is excluded unless the private layer is explicitly enabled.
- No external model or cloud service is required.

### Local Voice Graph

The waypoints ribbon icon transcribes speech locally with Whisper and filters
Obsidian's native graph using the existing relevance index. It does not start,
contact, or depend on Ollama or any language model.

The normal Obsidian graph shows the complete vault. **Show focused knowledge
graph** temporarily narrows it to concepts, works, people, maps, dreams, and
attributed sources. **Show complete archive graph** clears that temporary
filter and restores every node.

### Browser Graph

Use **Open browser graph** from Obsidian's command palette to open the
self-contained interactive browser view. It provides Core, Culture, Library,
Archive, and All layers, plus search, pan, zoom, category toggles, note details,
and links back into Obsidian. The generated file lives at
`knowledge/output/browser-graph.html` and is rebuilt by `wiki_refresh.py`.

## Book Metadata Overrides

The books importer parses author/title/year from filenames, which leaves many
entries as `author: Unknown` with garbled titles. Curated corrections live in
`knowledge/raw/books-metadata.json`, keyed by the exact source filename:

```json
"thus spoke zarathustra.pdf": {"title": "Thus Spoke Zarathustra", "author": "Friedrich Nietzsche", "year": "1883", "category": "Philosophy"}
```

These overrides are durable — they are re-applied on every `wiki_refresh.py`, so
fix metadata here rather than editing files under `knowledge/wiki/books/` (which
the importer overwrites). On each run the importer also:

- wikilinks each author that already has a note (so the graph grows as people
  pages are added), keeping the lint at zero broken links;
- preserves a retitled book's old machine title as an alias so prior references
  still resolve;
- writes `knowledge/output/book-author-candidates.md` — authors cited by 2+
  books with no note yet, a ranked queue of new-article candidates.

## Collaboration Notes

This setup is additive. It creates notes, indexes, reports, and symlinks, but it does not delete source material. The compiler owns `knowledge/wiki/pages`, `knowledge/wiki/images`, `knowledge/wiki/collections`, `knowledge/wiki/artists`, and `knowledge/wiki/books` (curate books via `books-metadata.json`, above). Curated `people`, `works`, and concept notes live alongside it without being overwritten. Stale auto-generated notes are moved under `_archive/`, not deleted.
# ChatGPT Import

Request an account export from ChatGPT, download the ZIP, then run:

```sh
python3 tools/wiki_refresh.py
```

The refresh automatically detects a ZIP containing `conversations.json` in either local
or iCloud Downloads, imports it once, and retains the extracted export under
`knowledge/raw/chatgpt/exports/`.

To include ChatGPT's current visible memory synthesis, save it in Downloads as
`ChatGPT Memory Summary.txt`, then run the same refresh. Explicit paths also work:

```sh
python3 tools/wiki_chatgpt_import.py ~/Downloads/chatgpt-export.zip
python3 tools/wiki_chatgpt_import.py --memory-summary /path/to/memory-summary.txt
```

Conversation notes are archival evidence. Automatically surfaced memory candidates remain a review queue and are not treated as verified personal facts.

<!-- vault-crosslinks:start -->
## Discovered Connections

- [[knowledge/wiki/maps/Map - Living Graph|Map - Living Graph]] — named in this note
- [[knowledge/wiki/maps/Map - ChatGPT Memory|Map - ChatGPT Memory]] — named in this note
- [[knowledge/wiki/pages/knowledge base|knowledge base]] — named in this note
- [[knowledge/wiki/maps/Map - ChatGPT Conversations|Map - ChatGPT Conversations]] — named in this note
- [[knowledge/wiki/maps/Map - 3D Graph|Map - 3D Graph]] — named in this note
- [[knowledge/wiki/concepts/Memory and Preservation|Memory and Preservation]] — named in this note
- [[knowledge/wiki/maps/Map - Works|Map - Works]] — named in this note
- [[Welcome|strauh.al Knowledge Base]] — shared language: knowledge, vault, graph
<!-- vault-crosslinks:end -->
