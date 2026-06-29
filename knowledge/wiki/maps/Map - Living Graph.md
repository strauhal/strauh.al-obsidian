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

- [[knowledge/README|README]] — shared language: graph, obsidian's, ribbon
- [[knowledge/wiki/books/lewis-carroll-through-the-looking-glass-icon-group-international-inc|Through the Looking Glass -ICON Group International, Inc.]] — shared language: icon
- [[knowledge/wiki/books/cal-newport-deep-work-rules-for-focused-success-in-a-distracted-world|Deep Work Rules for focused success in a distracted world]] — shared language: focused
- [[knowledge/wiki/images/red ink abstract biomorphic drawing on graph paper bc6ed6cd|red ink abstract biomorphic drawing on graph paper]] — shared language: graph
- [[knowledge/wiki/images/red abstract looping line drawing on graph paper 83281a52|red abstract looping line drawing on graph paper]] — shared language: graph
- [[knowledge/wiki/images/magenta ink drawing of swirling patterns and mathematical equations on graph paper acc7c5e9|magenta ink drawing of swirling patterns and mathematical equations on graph paper]] — shared language: graph
- [[knowledge/wiki/images/the click by jonas wood 2019 e253761a|the click by jonas wood 2019]] — shared language: click
- [[knowledge/wiki/images/show 4ebe1817|show]] — shared language: show
<!-- vault-crosslinks:end -->
