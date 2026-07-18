---
title: Map - Living Graph
type: map
tags: [map, interface, knowledge-graph, voice]
created: 2026-06-22
updated: 2026-06-23
---

# Map - Living Graph

Voice control for Obsidian's untouched native Graph View. A spoken idea is transcribed locally with Whisper, then becomes a filtered, rearranged field of relevant notes and their graph neighbors without adding any interface to the graph itself.

## Open

Click the waypoints icon in Obsidian's left ribbon. The native graph opens and begins recording. Recording stops after a short pause, then local Whisper transcribes the phrase.

## Interaction

- Click the waypoints icon and speak a thought or question.
- Click the icon again to stop listening.
- Use Obsidian's normal graph hover, click, zoom, drag, and settings controls.
- Drag nodes to hold an idea in place; scroll over the field to zoom.

## Retrieval

The runtime is small and entirely local:

1. `whisper.cpp` transcribes microphone audio on the Mac.
2. The existing relevance index scores titles, note text, and note type.
3. Strong matches and a bounded set of their neighbors are selected.
4. The resulting paths are applied to Obsidian's native graph search filter.
5. Private notes remain excluded unless enabled in the plugin settings.

The index is rebuilt during `python3 tools/wiki_refresh.py`.

## Graph Presets

- **Show focused knowledge graph** returns to the readable default network.
- **Show complete archive graph** reveals every retained low-level archive node.
- Clicking Obsidian's ordinary graph ribbon icon returns to the focused graph.

[[Map - Maintenance]] remains the operational hub.

## See also

- [[Map - 3D Graph]] — a fully three-dimensional, fly-through view of the whole vault (open in a browser), where height encodes abstraction and the floor plane encodes theme.

<!-- vault-crosslinks:start -->
## Discovered Connections

- [[Welcome|strauh.al Knowledge Base]] — shared language: graph, fly-through, height
- [[knowledge/wiki/Home|strauh.al Knowledge Base]] — shared language: graph, fly-through, height
- [[knowledge/README|README]] — shared language: obsidian's, graph, waypoints
- [[knowledge/wiki/books/lewis-carroll-through-the-looking-glass-icon-group-international-inc|Through the Looking Glass -ICON Group International, Inc.]] — shared language: icon
- [[knowledge/wiki/books/cal-newport-deep-work-rules-for-focused-success-in-a-distracted-world|Deep Work Rules for focused success in a distracted world]] — shared language: focused
- [[knowledge/wiki/images/Illustration Red Abstract Looping Line Drawing On Graph Paper ab7a839e|Illustration Red Abstract Looping Line Drawing On Graph Paper]] — shared language: graph
- [[knowledge/wiki/images/Illustration Abstract Red Ink Biomorphic Drawing on Graph Paper 45c8b400|Illustration Abstract Red Ink Biomorphic Drawing on Graph Paper]] — shared language: graph
- [[knowledge/wiki/images/the living room by Paul Heaston (2009) 06093bca|the living room by Paul Heaston (2009)]] — shared language: living
<!-- vault-crosslinks:end -->
