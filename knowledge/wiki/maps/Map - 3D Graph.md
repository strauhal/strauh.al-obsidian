---
title: Map - 3D Graph
type: map
aliases: [3D Graph, 3D View, Map of the Mind, 3D map]
tags: [map, graph, 3d, interface]
created: 2026-06-23
updated: 2026-06-23
---

# Map - 3D Graph

A fully three-dimensional, fly-through view of all ~10,000 notes — a literal map of
the mind. It's a single self-contained HTML file (data baked in, WebGL engine from a
CDN), so it opens with a double-click; no server, no Obsidian plugin required.

[▶ Open the 3D graph](file:///Users/erneststrauhal/Library/Mobile%20Documents/com~apple~CloudDocs/obsidian/knowledge/output/graph-3d.html)

## The axes mean something

This is not a random force-blob — every coordinate is designed:

- **Y (up / down) = abstraction.** [[Map - Concepts|Ideas]] crown the top; below them
  fall maps → works → people → culture/dreams → books → pages → anchors → artists →
  collections, with the **image archive** as the deep floor. You fly *down and out*
  from mind to raw material.
- **X / Z (the floor plane) = theme + cluster.** The four idea-themes own four angular
  wedges, and a curated note sits in the wedge of the concept it feeds — so a vertical
  slice reads as a single theme. The archive fans across a wide disk by collection.
- **Distance is deliberate:** a tight bright idea-crown (~radius 150) hovering far above
  a vast archive plain (~radius 1,150), with big gaps between tiers so the strata stay
  legible instead of collapsing into one ball.

## Navigating (trackpad)

- **Drag** — rotate / orbit the whole map.
- **Two-finger drag** (or right-click-drag) — pan.
- **Pinch or two-finger scroll** — zoom in and out.
- **Click a node** — fly the camera to it.
- **Legend** (top-left) — click any layer to show/hide it.
- **Ideas layer only** — strips the archive down to the bright semantic core.
- **Search box** — type a note name and hit enter to fly there.

## Rebuilding

The view is regenerated from the live vault:

```sh
python3 tools/wiki_graph3d.py     # just the 3D file
python3 tools/wiki_refresh.py     # full vault refresh (includes it)
```

## Connections

- [[Map - Concepts]] — the idea spine the 3D heights are built from.
- [[Map - Image Archive]] — the deep floor of the 3D view.
- [[Map - Living Graph]] — the in-Obsidian, voice-driven companion view.
- [[Map - Maintenance]] — how the vault and its views are built.

<!-- vault-crosslinks:start -->
## Discovered Connections

- [[knowledge/wiki/maps/Map - Works|Map - Works]] — named in this note
- [[knowledge/wiki/concepts/The Archive as Consciousness|The Archive as Consciousness]] — shared language: mind, vault, literal
- [[Welcome|strauh.al Knowledge Base]] — shared language: graph, ideas, vault
- [[knowledge/wiki/Home|strauh.al Knowledge Base]] — shared language: graph, ideas, vault
- [[knowledge/wiki/images/red ink abstract biomorphic drawing on graph paper bc6ed6cd|red ink abstract biomorphic drawing on graph paper]] — shared language: graph
- [[knowledge/wiki/images/black and white graph showing a single line splitting repeatedly into a dense chaotic region 034260fb|black and white graph showing a single line splitting repeatedly into a dense chaotic region]] — shared language: graph, single
- [[knowledge/wiki/pages/philosophical texts phenomenology of spirit|philosophical texts phenomenology of spirit]] — shared language: click, drag, theme
- [[knowledge/wiki/images/red abstract looping line drawing on graph paper 83281a52|red abstract looping line drawing on graph paper]] — shared language: graph
<!-- vault-crosslinks:end -->
