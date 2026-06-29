#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import urllib.parse
import zlib
from pathlib import Path


VAULT = Path(__file__).resolve().parents[1]
INDEX = VAULT / "knowledge" / "output" / "living-graph-index.json"
OUTPUT = VAULT / "knowledge" / "output" / "browser-graph.html"

PALETTE = {
    "concept": "#d7263d",
    "work": "#f46036",
    "person": "#1b998b",
    "map": "#6a4c93",
    "dream": "#8f2d56",
    "criticism": "#495057",
    "culture": "#ffbe0b",
    "book": "#2f6b4f",
    "page": "#8aa399",
    "image": "#c8c6bf",
    "artist": "#ff7a90",
    "collection": "#7999a8",
    "anchor": "#a4a4a4",
    "other": "#6c757d",
}

MODE_TYPES = {
    "core": {"concept", "work", "person", "map", "dream", "criticism"},
    "culture": {"concept", "work", "person", "map", "dream", "criticism", "culture"},
    "library": {"concept", "work", "person", "map", "criticism", "book"},
    "archive": {"concept", "work", "person", "map", "image", "artist", "collection", "page"},
}

CENTERS = {
    "concept": (-180, -70),
    "work": (30, 120),
    "person": (210, -70),
    "map": (0, -235),
    "dream": (-270, 170),
    "criticism": (270, 175),
    "culture": (-560, -250),
    "book": (560, -250),
    "page": (-675, 110),
    "image": (0, 650),
    "artist": (690, 120),
    "collection": (-575, 450),
    "anchor": (0, -560),
    "other": (0, 0),
}

REGIONS = {
    "core": {"label": "Core Wiki", "x": 0, "y": -20, "rx": 410, "ry": 360},
    "culture": {"label": "Culture", "x": -560, "y": -250, "rx": 230, "ry": 210},
    "library": {"label": "Library", "x": 560, "y": -250, "rx": 230, "ry": 210},
    "pages": {"label": "Pages", "x": -675, "y": 110, "rx": 190, "ry": 185},
    "artists": {"label": "Artists", "x": 690, "y": 120, "rx": 265, "ry": 255},
    "collections": {"label": "Collections", "x": -575, "y": 450, "rx": 230, "ry": 200},
    "archive": {"label": "Image Archive", "x": 0, "y": 650, "rx": 690, "ry": 360},
}

IMAGE_SUBCENTERS = {
    "artists": (-470, 610),
    "1900s": (-210, 690),
    "2000s": (60, 720),
    "2010s": (300, 650),
    "2020s": (505, 540),
    "other": (0, 520),
}


def frac(seed: str) -> float:
    return (zlib.crc32(seed.encode("utf-8")) % 1_000_000) / 1_000_000


def normalized_type(value: str) -> str:
    value = (value or "other").lower()
    aliases = {
        "concepts": "concept",
        "works": "work",
        "people": "person",
        "maps": "map",
        "dreams": "dream",
        "books": "book",
        "images": "image",
        "artists": "artist",
        "collections": "collection",
        "pages": "page",
        "anchors": "anchor",
        "music": "culture",
        "movie": "culture",
        "reading": "culture",
        "source-index": "criticism",
        "memory-summary": "criticism",
        "wiki": "map",
        "index": "map",
    }
    return aliases.get(value, value if value in PALETTE else "other")


def image_bucket(doc: dict) -> str:
    image = (doc.get("image") or doc.get("path") or "").lower()
    for bucket in ("artists", "1900s", "2000s", "2010s", "2020s"):
        if f"/{bucket}/" in image:
            return bucket
    return "other"


def node_center(doc: dict, kind: str) -> tuple[float, float]:
    if kind == "image":
        return IMAGE_SUBCENTERS[image_bucket(doc)]
    return CENTERS[kind]


def build() -> Path:
    payload = json.loads(INDEX.read_text())
    source_docs = payload.get("docs", [])
    kept = [doc for doc in source_docs if not doc.get("private")]
    old_to_new = {doc["id"]: index for index, doc in enumerate(kept)}

    nodes = []
    for index, doc in enumerate(kept):
        kind = normalized_type(doc.get("type", "other"))
        cx, cy = node_center(doc, kind)
        angle = frac("angle:" + doc["path"]) * math.tau
        radius = 28 + (125 if kind == "image" else 170) * math.sqrt(frac("radius:" + doc["path"]))
        degree = len(doc.get("links", [])) + len(doc.get("backlinks", []))
        nodes.append({
            "i": index,
            "t": doc["title"],
            "p": doc["path"],
            "k": kind,
            "b": image_bucket(doc) if kind == "image" else kind,
            "x": round(cx + math.cos(angle) * radius, 2),
            "y": round(cy + math.sin(angle) * radius, 2),
            "d": degree,
            "e": doc.get("excerpt", "")[:360],
            "u": "obsidian://open?vault=obsidian&file="
                 + urllib.parse.quote(doc["path"].removesuffix(".md"), safe=""),
        })

    edges = []
    seen = set()
    for doc in kept:
        source = old_to_new[doc["id"]]
        for old_target in doc.get("links", []):
            target = old_to_new.get(old_target)
            if target is None or target == source:
                continue
            pair = (min(source, target), max(source, target))
            if pair not in seen:
                seen.add(pair)
                edges.append(pair)

    data = {
        "nodes": nodes,
        "edges": edges,
        "palette": PALETTE,
        "modes": {key: sorted(value) for key, value in MODE_TYPES.items()},
        "regions": REGIONS,
        "imageBuckets": IMAGE_SUBCENTERS,
    }
    OUTPUT.write_text(
        TEMPLATE.replace("__GRAPH_DATA__", json.dumps(data, ensure_ascii=False)),
        encoding="utf-8",
    )
    print(f"Browser graph: {len(nodes)} nodes, {len(edges)} edges -> {OUTPUT}")
    return OUTPUT


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>strauh.al knowledge graph</title>
<style>
:root{color-scheme:light;--paper:#f7f7f4;--ink:#171717;--muted:#6d6d68;--line:#d8d8d2;--panel:rgba(250,250,247,.94);--accent:#e63946}
*{box-sizing:border-box}
html,body{margin:0;width:100%;height:100%;overflow:hidden;background:var(--paper);color:var(--ink);font-family:Inter,ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;letter-spacing:0}
canvas{position:fixed;inset:0;width:100%;height:100%;cursor:grab}
canvas.dragging{cursor:grabbing}
.toolbar{position:fixed;z-index:5;top:14px;left:14px;right:14px;height:46px;display:flex;align-items:center;gap:10px;padding:6px 8px;background:var(--panel);border:1px solid var(--line);border-radius:7px;backdrop-filter:blur(12px)}
.brand{font-weight:700;font-size:14px;padding:0 7px;white-space:nowrap}
.brand span{font-weight:400;color:var(--muted)}
.modes{display:flex;align-items:center;border:1px solid var(--line);border-radius:5px;overflow:hidden}
button,input{font:inherit;letter-spacing:0}
button{height:30px;border:0;border-right:1px solid var(--line);background:transparent;color:var(--muted);padding:0 10px;cursor:pointer}
button:last-child{border-right:0}
button:hover{background:#ededE8;color:var(--ink)}
button.active{background:var(--ink);color:white}
.search{margin-left:auto;width:min(330px,34vw);height:32px;border:1px solid var(--line);border-radius:5px;background:white;padding:0 10px;outline:none;color:var(--ink)}
.search:focus{border-color:#888}
.icon-button{width:32px;padding:0;font-size:17px;border:1px solid var(--line);border-radius:5px}
.status{position:fixed;z-index:4;left:15px;bottom:14px;padding:8px 10px;background:var(--panel);border:1px solid var(--line);border-radius:6px;color:var(--muted);font-size:12px;pointer-events:none}
.legend{position:fixed;z-index:4;left:14px;top:72px;width:150px;padding:9px;background:var(--panel);border:1px solid var(--line);border-radius:7px}
.legend-row{height:25px;display:flex;align-items:center;gap:8px;font-size:12px;color:var(--muted);cursor:pointer;padding:0 4px}
.legend-row:hover{background:#ededE8;color:var(--ink)}
.legend-row.off{opacity:.28}
.swatch{width:9px;height:9px;border-radius:50%}
.count{margin-left:auto;font-variant-numeric:tabular-nums;color:#999}
.detail{position:fixed;z-index:6;right:14px;top:72px;width:310px;max-height:calc(100vh - 88px);overflow:auto;background:var(--panel);border:1px solid var(--line);border-radius:7px;padding:16px;transform:translateX(calc(100% + 24px));transition:transform .18s ease}
.detail.open{transform:translateX(0)}
.detail h2{font-size:19px;line-height:1.2;margin:0 28px 6px 0}
.detail .kind{font-size:11px;text-transform:uppercase;color:var(--accent);font-weight:700}
.detail p{font-size:13px;line-height:1.55;color:#474743}
.detail .path{font-size:11px;color:#888;word-break:break-all}
.detail a{display:inline-flex;align-items:center;height:32px;padding:0 10px;border-radius:5px;background:var(--ink);color:white;text-decoration:none;font-size:12px}
.close{position:absolute;right:8px;top:8px;width:28px;border:0;font-size:18px}
@media(max-width:760px){.toolbar{height:auto;flex-wrap:wrap}.brand{width:100%}.search{order:3;width:100%;margin-left:0}.legend{top:180px}.detail{top:180px;width:calc(100vw - 28px);max-height:calc(100vh - 194px)}}
</style>
</head>
<body>
<canvas id="graph"></canvas>
<header class="toolbar">
  <div class="brand">strauh.al <span>knowledge graph</span></div>
  <div class="modes" id="modes"></div>
  <input class="search" id="search" placeholder="Search notes, ideas, people, works…" autocomplete="off">
  <button class="icon-button" id="labels" title="Toggle labels">T</button>
  <button class="icon-button" id="center" title="Center graph">⌂</button>
</header>
<aside class="legend" id="legend"></aside>
<aside class="detail" id="detail">
  <button class="close" id="close" title="Close">×</button>
  <div class="kind" id="detail-kind"></div>
  <h2 id="detail-title"></h2>
  <p id="detail-excerpt"></p>
  <p class="path" id="detail-path"></p>
  <a id="detail-open" href="#">Open in Obsidian</a>
</aside>
<div class="status" id="status"></div>
<script>
const DATA=__GRAPH_DATA__;
const canvas=document.getElementById("graph"),ctx=canvas.getContext("2d");
const modeButtons=document.getElementById("modes"),legend=document.getElementById("legend"),status=document.getElementById("status");
const search=document.getElementById("search"),detail=document.getElementById("detail");
let width=0,height=0,dpr=1,mode="core",scale=.72,panX=0,panY=0,drag=null,hover=-1,selected=-1,labels=false;
const hidden=new Set(),screen=new Array(DATA.nodes.length),adj=DATA.nodes.map(()=>[]);
DATA.edges.forEach(([a,b])=>{adj[a].push(b);adj[b].push(a)});
const modeNames={core:"Core",culture:"Culture",library:"Library",archive:"Archive",all:"Atlas"};
const modeOrder=["core","culture","library","archive","all"];
for(const key of modeOrder){const b=document.createElement("button");b.textContent=modeNames[key];b.onclick=()=>setMode(key);b.dataset.mode=key;modeButtons.appendChild(b)}
function allowedKinds(){return mode==="all"?new Set(Object.keys(DATA.palette)):new Set(DATA.modes[mode])}
function visible(n){return allowedKinds().has(n.k)&&!hidden.has(n.k)&&matches(n)}
function matches(n){const q=search.value.trim().toLowerCase();return !q||n.t.toLowerCase().includes(q)||n.e.toLowerCase().includes(q)}
function resize(){dpr=Math.min(devicePixelRatio||1,2);width=innerWidth;height=innerHeight;canvas.width=width*dpr;canvas.height=height*dpr;canvas.style.width=width+"px";canvas.style.height=height+"px";ctx.setTransform(dpr,0,0,dpr,0,0);draw()}
function worldToScreen(n){return{x:(n.x+panX)*scale+width/2,y:(n.y+panY)*scale+height/2}}
function rebuildLegend(){legend.innerHTML="";const kinds={};DATA.nodes.forEach(n=>{if(allowedKinds().has(n.k))kinds[n.k]=(kinds[n.k]||0)+1});Object.keys(kinds).sort().forEach(k=>{const row=document.createElement("div");row.className="legend-row"+(hidden.has(k)?" off":"");row.innerHTML=`<span class="swatch" style="background:${DATA.palette[k]}"></span><span>${k}</span><span class="count">${kinds[k]}</span>`;row.onclick=()=>{hidden.has(k)?hidden.delete(k):hidden.add(k);rebuildLegend();draw()};legend.appendChild(row)})}
function setMode(next){mode=next;hidden.clear();document.querySelectorAll("[data-mode]").forEach(b=>b.classList.toggle("active",b.dataset.mode===mode));rebuildLegend();fit();draw()}
function fit(){const nodes=DATA.nodes.filter(visible);if(!nodes.length)return;let minX=Infinity,maxX=-Infinity,minY=Infinity,maxY=-Infinity;nodes.forEach(n=>{minX=Math.min(minX,n.x);maxX=Math.max(maxX,n.x);minY=Math.min(minY,n.y);maxY=Math.max(maxY,n.y)});const sideSpace=width<760?30:220,topSpace=width<760?250:150;scale=Math.min((width-sideSpace)/(maxX-minX+120),(height-topSpace)/(maxY-minY+120));scale=Math.max(.08,Math.min(scale,1.8));panX=-(minX+maxX)/2;panY=-(minY+maxY)/2+(width<760?90/scale:0)}
function drawRegions(){const kinds=allowedKinds();Object.values(DATA.regions).forEach(r=>{let show=false;if(r.label==="Image Archive")show=kinds.has("image");else if(r.label==="Artists")show=kinds.has("artist");else if(r.label==="Library")show=kinds.has("book");else if(r.label==="Culture")show=kinds.has("culture");else if(r.label==="Pages")show=kinds.has("page");else if(r.label==="Collections")show=kinds.has("collection");else show=["concept","work","person","map","dream","criticism"].some(k=>kinds.has(k));if(!show)return;const p={x:(r.x+panX)*scale+width/2,y:(r.y+panY)*scale+height/2},rx=r.rx*scale,ry=r.ry*scale;ctx.beginPath();ctx.ellipse(p.x,p.y,rx,ry,0,0,Math.PI*2);ctx.fillStyle="rgba(255,255,255,.42)";ctx.fill();ctx.strokeStyle="rgba(30,30,28,.075)";ctx.lineWidth=1;ctx.stroke();if(scale>.18){ctx.font="700 12px Inter, sans-serif";ctx.fillStyle="rgba(30,30,28,.34)";ctx.fillText(r.label,p.x-rx+14,p.y-ry+22)}})}
function nodeRadius(n){const base=n.k==="image"?1.45:n.k==="artist"?1.9:2.4;const cap=n.k==="image"?4.2:9;return Math.max(1.25,Math.min(cap,base+Math.log2(n.d+1)*.72))*Math.max(.72,Math.min(1.18,scale))}
function draw(){ctx.clearRect(0,0,width,height);ctx.fillStyle="#f7f7f4";ctx.fillRect(0,0,width,height);drawRegions();const visibleSet=new Set();let count=0,edgeCount=0,drawnEdges=0;DATA.nodes.forEach(n=>{if(visible(n)){visibleSet.add(n.i);screen[n.i]=worldToScreen(n);count++}});ctx.lineWidth=.52;DATA.edges.forEach(([a,b])=>{if(!visibleSet.has(a)||!visibleSet.has(b))return;edgeCount++;const A=screen[a],B=screen[b],na=DATA.nodes[a],nb=DATA.nodes[b],archiveEdge=na.k==="image"||nb.k==="image",artistArchive=archiveEdge&&(na.k==="artist"||nb.k==="artist");if(archiveEdge&&selected!==a&&selected!==b&&hover!==a&&hover!==b){const keep=((a*1103515245+b*12345)>>>0)%100;if(keep>(artistArchive?7:13))return}drawnEdges++;ctx.beginPath();ctx.strokeStyle=archiveEdge?"rgba(50,50,48,.026)":"rgba(50,50,48,.12)";ctx.moveTo(A.x,A.y);ctx.lineTo(B.x,B.y);ctx.stroke()});DATA.nodes.forEach(n=>{if(!visibleSet.has(n.i))return;const p=screen[n.i],r=nodeRadius(n);ctx.beginPath();ctx.arc(p.x,p.y,r,0,Math.PI*2);ctx.fillStyle=DATA.palette[n.k]||DATA.palette.other;ctx.globalAlpha=n.i===hover||n.i===selected?1:(n.k==="image"?.42:n.k==="anchor"?.5:.9);ctx.fill();if(n.i===hover||n.i===selected){ctx.globalAlpha=1;ctx.lineWidth=2;ctx.strokeStyle="#171717";ctx.stroke()}ctx.globalAlpha=1;if((n.i===hover||n.i===selected||(labels&&n.d>20&&n.k!=="image"))&&scale>.35){ctx.font="12px Inter, sans-serif";ctx.fillStyle="#171717";ctx.fillText(n.t,p.x+r+4,p.y+4)}});status.textContent=`${count.toLocaleString()} notes · ${edgeCount.toLocaleString()} connections · ${drawnEdges.toLocaleString()} drawn · drag to pan · scroll to zoom`}
function hit(x,y){let best=-1,dist=14;DATA.nodes.forEach(n=>{if(!visible(n)||!screen[n.i])return;const p=screen[n.i],d=Math.hypot(p.x-x,p.y-y);if(d<dist){dist=d;best=n.i}});return best}
canvas.onpointerdown=e=>{drag={x:e.clientX,y:e.clientY,px:panX,py:panY};canvas.classList.add("dragging");canvas.setPointerCapture(e.pointerId)}
canvas.onpointermove=e=>{if(drag){panX=drag.px+(e.clientX-drag.x)/scale;panY=drag.py+(e.clientY-drag.y)/scale;draw();return}hover=hit(e.clientX,e.clientY);draw()}
canvas.onpointerup=e=>{if(drag&&Math.hypot(e.clientX-drag.x,e.clientY-drag.y)<5){selected=hit(e.clientX,e.clientY);showDetail(selected)}drag=null;canvas.classList.remove("dragging")}
canvas.onwheel=e=>{e.preventDefault();const beforeX=(e.clientX-width/2)/scale-panX,beforeY=(e.clientY-height/2)/scale-panY;scale*=Math.exp(-e.deltaY*.001);scale=Math.max(.05,Math.min(4,scale));panX=(e.clientX-width/2)/scale-beforeX;panY=(e.clientY-height/2)/scale-beforeY;draw()}
function showDetail(i){if(i<0){detail.classList.remove("open");return}const n=DATA.nodes[i];document.getElementById("detail-kind").textContent=`${n.k} · ${n.d} connections`;document.getElementById("detail-title").textContent=n.t;document.getElementById("detail-excerpt").textContent=n.e||"No excerpt available.";document.getElementById("detail-path").textContent=n.p;document.getElementById("detail-open").href=n.u;detail.classList.add("open")}
document.getElementById("close").onclick=()=>{selected=-1;detail.classList.remove("open");draw()}
document.getElementById("center").onclick=()=>{fit();draw()}
document.getElementById("labels").onclick=e=>{labels=!labels;e.currentTarget.classList.toggle("active",labels);draw()}
search.oninput=()=>{selected=-1;detail.classList.remove("open");draw()}
search.onkeydown=e=>{if(e.key!=="Enter")return;const q=search.value.trim().toLowerCase(),n=DATA.nodes.find(n=>visible(n)&&n.t.toLowerCase().includes(q));if(!n)return;selected=n.i;panX=-n.x;panY=-n.y;scale=Math.max(scale,1.2);requestAnimationFrame(()=>{showDetail(n.i);draw()})}
addEventListener("resize",resize);resize();setMode("all");
</script>
</body>
</html>"""


if __name__ == "__main__":
    build()
