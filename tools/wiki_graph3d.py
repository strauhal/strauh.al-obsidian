#!/usr/bin/env python3
"""Build a self-contained 3D view of the vault — a spiky orb of the mind.

Renders every note as a node in a WebGL force graph (vasturiano's
3d-force-graph, the engine the "3D Graph" Obsidian plugin also uses), with
*designed* spherical coordinates rather than a random physics blob:

- RADIUS from center = abstraction. Ideas sit at the dense core; each tier out
  is more raw, with the image archive forming the outer shell. You fly from the
  bright idea-core outward to the material.
- DIRECTION = cluster. Each collection / artist / book-shelf gets its own
  direction on the sphere, and its members string outward along it — so the
  archive erupts into spikes (a sea-urchin), not a flat disk.
- Node hue = what kind of thing it is (concepts gold, people red, images teal…).
- Link hue = the color of its more-central endpoint, so every connection glows
  with the color of the idea or hub it serves.

Output is one self-contained HTML file (data embedded, library from CDN) so it
opens with a double-click. Trackpad: drag = rotate, two-finger drag = pan,
pinch / two-finger scroll = zoom, click a node = fly to it.
"""
from __future__ import annotations

import json
import math
import re
import zlib
from pathlib import Path


VAULT = Path(__file__).resolve().parents[1]
WIKI = VAULT / "knowledge" / "wiki"
OUTPUT = VAULT / "knowledge" / "output"

PALETTE = {
    "concepts": "#FFD60A", "works": "#FF7A00", "people": "#FF2D55",
    "artists": "#FF5FA2", "maps": "#E248FF", "dreams": "#9B5DE5",
    "books": "#2D9BFF", "pages": "#1FD3EC", "anchors": "#5D6BFF",
    "images": "#16C79A", "collections": "#4CC93F", "culture": "#B6E020",
    "life": "#E9E3D5", "sources": "#FFA94D", "chatgpt": "#22D3EE",
}

# Radius from center (abstraction) + node size + rank (0 = most central/abstract).
TIER = {
    "concepts":    {"r": 130,  "size": 12,  "rank": 0},
    "maps":        {"r": 250,  "size": 6,   "rank": 1},
    "works":       {"r": 270,  "size": 6,   "rank": 2},
    "sources":     {"r": 290,  "size": 5,   "rank": 2},
    "people":      {"r": 350,  "size": 5,   "rank": 3},
    "life":        {"r": 330,  "size": 7,   "rank": 3},
    "dreams":      {"r": 340,  "size": 4,   "rank": 4},
    "chatgpt":     {"r": 500,  "size": 3,   "rank": 5},
    "culture":     {"r": 470,  "size": 3,   "rank": 5},
    "books":       {"r": 580,  "size": 3,   "rank": 6},
    "pages":       {"r": 700,  "size": 3,   "rank": 7},
    "anchors":     {"r": 900,  "size": 2,   "rank": 8},
    "collections": {"r": 850,  "size": 4,   "rank": 9},
    "artists":     {"r": 1060, "size": 2,   "rank": 10},
    "images":      {"r": 1260, "size": 1.7, "rank": 11},
}
DEFAULT_TIER = {"r": 500, "size": 3, "rank": 6}

# These groups radiate outward as spikes (direction = their cluster).
SPIKE = {"images", "collections", "artists", "anchors"}
LINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


def frac(seed: str) -> float:
    return (zlib.crc32(seed.encode("utf-8")) % 1000000) / 1000000.0


def unit_from_key(key: str):
    """A stable, ~uniform point on the unit sphere from a string key."""
    u = frac("dirA:" + key)
    v = frac("dirB:" + key)
    theta = 2 * math.pi * u
    phi = math.acos(2 * v - 1)
    s = math.sin(phi)
    return [s * math.cos(theta), math.cos(phi), s * math.sin(theta)]


def perturb(d, scale: float, seed: str):
    x = d[0] + scale * (frac("px" + seed) - 0.5)
    y = d[1] + scale * (frac("py" + seed) - 0.5)
    z = d[2] + scale * (frac("pz" + seed) - 0.5)
    m = math.sqrt(x * x + y * y + z * z) or 1.0
    return [x / m, y / m, z / m]


def frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    return text[3:end] if end != -1 else ""


def field(block: str, key: str) -> str:
    m = re.search(rf"^{key}:\s*(.+)$", block, re.M)
    return m.group(1).strip().strip('"') if m else ""


def link_targets(text: str) -> list[str]:
    out = []
    for raw in LINK_RE.findall(text):
        target = raw.split("|", 1)[0].split("#", 1)[0].strip()
        if target:
            out.append(target)
    return out


def build():
    notes = sorted(WIKI.rglob("*.md"))
    resolve: dict[str, str] = {}
    meta: dict[str, dict] = {}
    raw_links: dict[str, list[str]] = {}
    for path in notes:
        text = path.read_text(errors="ignore")
        block = frontmatter(text)
        title = field(block, "title") or path.stem
        group = path.parent.name if path.parent != WIKI else "maps"
        meta[title] = {"group": group, "category": field(block, "category")}
        for key in {title, path.stem}:
            resolve.setdefault(key, title)
        for alias in re.findall(r"[^,\[\]]+", field(block, "aliases").strip("[]")):
            alias = alias.strip().strip('"')
            if alias:
                resolve.setdefault(alias, title)
        raw_links[title] = link_targets(text)

    adj: dict[str, set[str]] = {t: set() for t in meta}
    links = []
    seen_pairs = set()
    for src, targets in raw_links.items():
        for t in targets:
            dst = resolve.get(t)
            if not dst or dst == src or dst not in meta:
                continue
            adj[src].add(dst)
            adj[dst].add(src)
            key = tuple(sorted((src, dst)))
            if key not in seen_pairs:
                seen_pairs.add(key)
                links.append({"source": src, "target": dst})

    def cluster_key(title: str) -> str:
        group = meta[title]["group"]
        if group == "images":
            for n in adj[title]:
                if n.startswith("Collection - "):
                    return n
            return "images-misc"
        if group == "collections":
            return title
        if group == "artists":
            return title
        if group == "books":
            return "shelf-" + (meta[title]["category"] or "misc")
        return "core-" + title

    nodes = []
    for title, m in meta.items():
        group = m["group"]
        tier = TIER.get(group, DEFAULT_TIER)
        deg = len(adj[title])
        if group in SPIKE:
            d = perturb(unit_from_key(cluster_key(title)), 0.12, title)
            spread = 0.62 + 0.62 * frac("rad" + title)  # elongate spikes
        else:
            d = unit_from_key(title)  # fill the core ball
            spread = 0.75 + 0.45 * frac("rad" + title)
        r = tier["r"] * spread
        x, y, z = d[0] * r, d[1] * r, d[2] * r
        size = tier["size"] * (1 + min(deg, 30) / 30 * 1.6)
        nodes.append({
            "id": title, "group": group, "rank": tier["rank"], "deg": deg,
            "val": round(size, 2),
            "x": round(x, 1), "y": round(y, 1), "z": round(z, 1),
            "fx": round(x, 1), "fy": round(y, 1), "fz": round(z, 1),
        })

    data = {"nodes": nodes, "links": links}
    html = TEMPLATE.replace("__DATA__", json.dumps(data, ensure_ascii=False))
    html = html.replace("__PALETTE__", json.dumps(PALETTE))
    OUTPUT.mkdir(parents=True, exist_ok=True)
    out = OUTPUT / "graph-3d.html"
    out.write_text(html, encoding="utf-8")
    rmax = max(math.sqrt(n["x"]**2 + n["y"]**2 + n["z"]**2) for n in nodes)
    print(f"3D orb: {len(nodes)} nodes, {len(links)} links -> {out}")
    print(f"  radius 0..{rmax:.0f} (ideas at core, archive spikes on the shell)")
    return out


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>strauh.al — 3D map of the mind</title>
<style>
  html,body{margin:0;height:100%;background:#08080b;color:#e8e6dd;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;overflow:hidden}
  #graph{position:fixed;inset:0}
  .panel{position:fixed;z-index:10;background:rgba(16,16,20,.82);backdrop-filter:blur(8px);border:1px solid rgba(255,255,255,.08);border-radius:12px;padding:12px 14px}
  #legend{top:16px;left:16px;max-width:214px}
  #legend h1{font-size:14px;font-weight:600;margin:0 0 2px}
  #legend p{font-size:11px;color:#8c8a80;margin:0 0 10px;line-height:1.45}
  .row{display:flex;align-items:center;gap:8px;font-size:12px;padding:3px 4px;border-radius:6px;cursor:pointer;user-select:none}
  .row:hover{background:rgba(255,255,255,.06)}
  .row.off{opacity:.32}
  .dot{width:11px;height:11px;border-radius:50%;flex:none}
  .row .n{margin-left:auto;color:#7c7a71;font-variant-numeric:tabular-nums}
  #controls{top:16px;right:16px;display:flex;flex-direction:column;gap:8px;width:188px}
  #controls input,#controls button{font:inherit;font-size:12px;color:#e8e6dd;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.12);border-radius:8px;padding:7px 9px;outline:none}
  #controls input::placeholder{color:#76746b}
  #controls button{cursor:pointer;text-align:left}
  #controls button:hover{background:rgba(255,255,255,.12)}
  #help{bottom:16px;left:16px;font-size:11px;color:#9b9a90;line-height:1.6;max-width:340px}
  #help b{color:#d8d6cd;font-weight:600}
</style>
</head>
<body>
<div id="graph"></div>
<div id="legend" class="panel">
  <h1>map of the mind</h1>
  <p>A spiky orb: <b style="color:#FFD60A">ideas</b> at the core, the archive spiking out to the shell. Radius = abstraction, direction = cluster. Click a row to toggle a layer.</p>
  <div id="rows"></div>
</div>
<div id="controls" class="panel">
  <input id="search" placeholder="find a note…" autocomplete="off">
  <button id="ideas">◓ Ideas core only</button>
  <button id="all">● Show everything</button>
  <button id="links">⌇ Links: curated</button>
  <button id="reset">⟲ Reset camera</button>
  <button id="spin">⏵ Auto-spin: off</button>
</div>
<div id="help" class="panel">
  <b>drag</b> to rotate · <b>two-finger drag</b> (or right-drag) to pan · <b>pinch / two-finger scroll</b> to zoom · <b>click</b> a node to fly to it
</div>
<script src="https://cdn.jsdelivr.net/npm/3d-force-graph@1/dist/3d-force-graph.min.js"></script>
<script>
const DATA = __DATA__;
const PALETTE = __PALETTE__;
const ARCHIVE = new Set(["images","collections","artists","anchors","pages"]);
const hidden = new Set();
let linkMode = 1;   // 0 off, 1 curated, 2 all
let spinning = false;

const byId = {}; DATA.nodes.forEach(n => byId[n.id] = n);
const groups = {}; DATA.nodes.forEach(n => groups[n.group] = (groups[n.group]||0)+1);
const node = l => (typeof l === "object" ? l : byId[l]);

const Graph = ForceGraph3D({ controlType: "orbit" })(document.getElementById("graph"))
  .graphData(DATA)
  .backgroundColor("#08080b")
  .nodeRelativeSize(1)
  .nodeVal("val")
  .nodeColor(n => PALETTE[n.group] || "#888888")
  .nodeOpacity(1)
  .nodeResolution(8)
  .nodeLabel(n => '<div style="color:#fff;font-size:12px">'+n.id+' &nbsp;<span style="color:'+(PALETTE[n.group]||"#aaa")+'">'+n.group+'</span></div>')
  .nodeVisibility(n => !hidden.has(n.group))
  .linkColor(l => { const s=node(l.source), t=node(l.target); const c=(s.rank<=t.rank?s:t); return PALETTE[c.group]||"#9aa"; })
  .linkOpacity(0.34)
  .linkWidth(0.6)
  .linkVisibility(l => {
     if(linkMode===0) return false;
     const s=node(l.source), t=node(l.target);
     if(!s||!t||hidden.has(s.group)||hidden.has(t.group)) return false;
     if(linkMode===2) return true;
     return !ARCHIVE.has(s.group) && !ARCHIVE.has(t.group);
  })
  .enableNodeDrag(false)
  .cooldownTicks(0).warmupTicks(0);

Graph.d3Force("charge", null);
Graph.d3Force("link", null);
Graph.d3Force("center", null);

const home = { x: 0, y: 120, z: 3100 };
Graph.cameraPosition(home, { x:0, y:0, z:0 }, 0);

Graph.onNodeClick(n => {
  const d = 200, r = 1 + d / Math.max(1, Math.hypot(n.x, n.y, n.z));
  Graph.cameraPosition({ x: n.x*r, y: n.y*r, z: n.z*r }, n, 1400);
});

const rows = document.getElementById("rows");
Object.keys(PALETTE).filter(g => groups[g]).forEach(g => {
  const row = document.createElement("div");
  row.className = "row";
  row.dataset.g = g;
  row.innerHTML = '<span class="dot" style="background:'+PALETTE[g]+'"></span>'+g+'<span class="n">'+groups[g]+'</span>';
  row.onclick = () => { hidden.has(g)?hidden.delete(g):hidden.add(g); row.classList.toggle("off"); refresh(); };
  rows.appendChild(row);
});
function syncRows(){ document.querySelectorAll(".row").forEach(r => r.classList.toggle("off", hidden.has(r.dataset.g))); }
function refresh(){ Graph.nodeVisibility(Graph.nodeVisibility()).linkVisibility(Graph.linkVisibility()); }

document.getElementById("ideas").onclick = () => {
  hidden.clear(); ["images","collections","artists","anchors","pages","books","culture"].forEach(g => hidden.add(g));
  syncRows(); refresh();
};
document.getElementById("all").onclick = () => { hidden.clear(); syncRows(); refresh(); };
document.getElementById("links").onclick = e => {
  linkMode = (linkMode+1)%3; e.target.textContent = "⌇ Links: " + ["off","curated","all"][linkMode]; refresh();
};
document.getElementById("reset").onclick = () => Graph.cameraPosition(home, { x:0,y:0,z:0 }, 900);
document.getElementById("spin").onclick = e => { spinning=!spinning; e.target.textContent = "⏵ Auto-spin: " + (spinning?"on":"off"); };
document.getElementById("search").addEventListener("keydown", e => {
  if(e.key!=="Enter") return;
  const q = e.target.value.trim().toLowerCase(); if(!q) return;
  const hit = DATA.nodes.find(n => n.id.toLowerCase().includes(q));
  if(hit){ const r=1+240/Math.max(1,Math.hypot(hit.x,hit.y,hit.z)); Graph.cameraPosition({x:hit.x*r,y:hit.y*r,z:hit.z*r}, hit, 1400); }
});

let angle = 0;
setInterval(() => {
  if(!spinning) return;
  angle += 0.0016;
  const R = 3100;
  Graph.cameraPosition({ x: R*Math.sin(angle), y: 120, z: R*Math.cos(angle) });
}, 30);

addEventListener("resize", () => Graph.width(innerWidth).height(innerHeight));
</script>
</body>
</html>
"""


if __name__ == "__main__":
    build()
