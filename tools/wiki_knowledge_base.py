#!/usr/bin/env python3
"""Wire the knowledge-base bookmark pages into the graph.

Each `knowledge_base/*.html` page is a flat list of external bookmarks. This pass
reads every hyperlink, decides which concepts / people / books each one touches
(by its link text and url), and writes a managed `<!-- kb-links -->` block into the
matching compiled page note — grouping the bookmarks under the [[nodes]] they
connect to. The page thereby joins the idea graph: a philosophy bookmark about the
panopticon links to [[The Oedipal Screen]], a Baudrillard article to [[AI Slop]],
an artist to their [[person]] node, a book reference to the [[book]] note.

Runs after wiki_compile (which regenerates the page bodies). Idempotent; every
emitted [[target]] is verified to resolve, so the lint stays at zero broken links.
"""
from __future__ import annotations

import html
import re
from pathlib import Path


VAULT = Path(__file__).resolve().parents[1]
WIKI = VAULT / "knowledge" / "wiki"
PAGES = WIKI / "pages"
PEOPLE = WIKI / "people"
BOOKS = WIKI / "books"
ARTISTS = WIKI / "artists"
KB_DIR = Path("/Users/erneststrauhal/GitHub/strauh.al4/knowledge_base")

PER_NODE = 40
START = "<!-- kb-links:start -->"
END = "<!-- kb-links:end -->"

LINK_RE = re.compile(r"<a\s+[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", re.I | re.S)
TAG_RE = re.compile(r"<[^>]+>")

# Concept title -> signals in a bookmark's text/url. '*' = stem (prefix) match;
# a plain word matches whole-word; phrases match as substrings.
CONCEPT_KW: dict[str, list[str]] = {
    "Latent Space": ["latent", "gan", "neural net", "machine learning", "generative adversarial", "stylegan", "interpolat*", "embedding", "rhizome", "deep learning", "deepdream", "computer art", "algorithmic art"],
    "Interpolating the Instruction Set": ["generative", "procedural", "algorithm", "parametric", "instruction set", "recipe", "code as", "interpolat*", "creative coding", "processing", "shader", "demoscene", "pix2pix"],
    "Human-Machine Tug of War": ["cyborg", "human-machine", "automation", "authorship", "collaborat*", "post-human", "posthuman", "tool use"],
    "AI Slop": ["ai art", "ai-generated", "ai generated", "midjourney", "dall-e", "stable diffusion", "deepfake", "generative ai", "chatgpt", "gpt-", "slop", "synthetic media"],
    "Synesthesia": ["synesth*", "color theory", "colour", "scriabin", "kandinsky", "chromesthesia", "sound and color", "sound and colour", "op art", "kinetic art", "color field", "chromatic"],
    "Dead Architecture": ["architecture", "brutalis*", "ruin", "liminal", "backrooms", "dead mall", "decay", "derelict", "urban exploration", "land art", "earthwork", "installation art", "monument"],
    "Trainpilled": ["train", "railroad", "railway", "subway", "transit", "amtrak", "locomotive", "infrastructure"],
    "The Flâneur as Web Surfer": ["flaneur", "flâneur", "arcades project", "psychogeograph*", "situationist", "debord", "dérive", "derive", "wandering", "stroll"],
    "Art Fills the God-Shaped Hole": ["god", "religion", "religious", "sacred", "spiritual", "mysticism", "mystic*", "occult", "alchemy", "gnostic", "buddhis*", "dharma", "transcend*", "enlightenment", "esoteric", "sublime", "kabbal*", "tarot", "meditation", "psychedelic", "sermon", "milinda", "soul", "icon", "byzantine", "altarpiece", "mandala", "devotional", "religious art", "saint", "biblical"],
    "Memory and Preservation": ["memory", "nostalgia", "preservation", "forgetting", "mnemonic", "remembrance", "the past", "archival"],
    "Autofiction": ["autofiction", "memoir", "confessional", "autobiograph*", "diary", "first-person", "knausgaard"],
    "Amor Fati": ["nietzsche", "amor fati", "stoic*", "absurd", "camus", "eternal return", "existential*", "marcus aurelius", "meaninglessness", "nihil*"],
    "Post-Irony": ["irony", "ironic", "post-irony", "vaporwave", "meme", "new sincerity", "metamodern*", "shitpost", "cringe", "copypasta"],
    "Spontaneity and Elegance": ["spontaneity", "improvisation", "wabi", "shibumi", "minimalis*", "calligraph*", "elegance", "sumi-e", "ink painting", "gesture", "zen"],
    "Transmitting My Neural Signals by Hand": ["drawing", "handwriting", "gesture", "notation", "sketch", "draughtsman", "calligraph*"],
    "The Tedium of the Art Is the Goal": ["craft", "process", "discipline", "deliberate practice", "tedium", "repetition", "mastery"],
    "The Attention Economy": ["attention economy", "attention", "dopamine", "addiction", "doomscroll", "algorithm", "tiktok", "social media", "advertising", "panopticon", "surveillance", "distraction", "engagement"],
    "The Internet as Confidant": ["internet", "online", "the web", "forum", "4chan", "reddit", "weblog", "chatroom", "parasocial", "simulacra", "simulation", "hyperreal", "vaporwave", "net art", "web art", "geocities", "newgrounds", "flash animation", "internet art", "digital folklore", "glitch"],
    "The Oedipal Screen": ["oedipus", "oedipal", "anti-oedipus", "freud", "lacan", "psychoanaly*", "virtual reality", "male gaze", "female gaze", "the gaze", "desire", "panopticon", "voyeur*", "scopophil*"],
    "The Spatial Web": ["hypertext", "spatial", "net art", "web art", "knowledge graph", "topology", "memex", "hyperlink", "browser", "webgl", "three.js", "interactive web", "creative coding"],
    "To Render Myself Unnecessary": ["pedagog*", "teaching", "education", "autodidact", "montessori", "learning to"],
    "The Archive as Consciousness": ["memex", "second brain", "zettelkasten", "commonplace book", "externaliz*", "archive of", "database", "personal wiki"],
    "Reading Like a Computer": ["attention span", "the shallows", "deep reading", "skimming", "distract*", "adhd", "tortured genius", "focus"],
    "Rebuilding from the Bottom": ["redemption", "recovery", "breakdown", "burnout", "failure", "rebuild*", "phoenix", "rock bottom"],
    "Atomization": ["atomis*", "atomiz*", "alienation", "loneliness", "isolation", "individualism", "bowling alone", "capitalist realism", "mark fisher", "acid communism", "neoliberal*", "late capitalism", "k-punk"],
}

COMMON = {"still", "carti", "land", "close", "judd", "wood", "power", "brown", "hood", "white"}


def compile_kw(kws):
    parts = []
    for kw in kws:
        kw = kw.lower()
        if kw.endswith("*"):
            parts.append(r"\b" + re.escape(kw[:-1]))
        elif re.fullmatch(r"[a-z]+", kw):
            parts.append(r"\b" + re.escape(kw) + r"\b")
        else:
            parts.append(re.escape(kw))
    return re.compile("|".join(parts))


def fm_title(text: str, fallback: str) -> str:
    m = re.search(r"^title:\s*(.+)$", text, re.M)
    return (m.group(1).strip().strip('"') if m else fallback)


def fm_aliases(text: str) -> list[str]:
    m = re.search(r"^aliases:\s*\[(.*?)\]", text, re.M)
    if not m:
        return []
    return [a.strip().strip('"') for a in m.group(1).split(",") if a.strip()]


def known_targets() -> set[str]:
    known = set()
    for p in WIKI.rglob("*.md"):
        known.add(p.stem)
        t = p.read_text(errors="ignore")
        known.add(fm_title(t, p.stem))
        known.update(fm_aliases(t))
    return known


def people_matcher():
    """name (lowercased) -> person title, for whole-name matching."""
    names = {}
    for p in PEOPLE.glob("*.md"):
        t = p.read_text(errors="ignore")
        title = fm_title(t, p.stem)
        cands = [title] + fm_aliases(t)
        for c in cands:
            cl = c.lower().strip()
            if len(cl) >= 5 and cl not in COMMON:
                names[cl] = title
    return names


def book_matcher():
    """book title (lowercased) -> title, for substring matching on reliable titles."""
    out = {}
    for p in BOOKS.glob("*.md"):
        t = p.read_text(errors="ignore")
        title = fm_title(t, p.stem)
        tl = title.lower().strip()
        words = re.findall(r"[a-z]{3,}", tl)
        if len(words) >= 2 and len(tl) >= 10 and not re.search(r"document|untitled|fulltext|^\d+$", tl):
            out[tl] = title
    return out


def artist_matcher():
    """artist name (lowercased) -> 'Artist - name' title. Filtered to distinctive
    names so a bookmark naming an artist links to that artist's images."""
    out = {}
    for p in ARTISTS.glob("*.md"):
        title = p.stem  # "Artist - <name>"
        name = title[len("Artist - "):].strip().lower() if title.lower().startswith("artist - ") else ""
        words = name.split()
        if not name or name in COMMON:
            continue
        if sum(c.isalpha() for c in name) < 6:
            continue
        if len(words) >= 2 or len(name) >= 7:
            out[name] = title
    return out


def extract_links(htext: str):
    out = []
    for url, raw in LINK_RE.findall(htext):
        text = html.unescape(TAG_RE.sub("", raw)).strip()
        text = re.sub(r"\s+", " ", text)
        low_url = url.lower()
        if not text or len(text) < 2:
            continue
        if "strauh.al" in low_url or "githubusercontent" in low_url or low_url.startswith("mailto"):
            continue
        if text.lower() in {"strauh.al", "knowledge_base", "home", "back"}:
            continue
        # skip junk link text that is a bare url / filename / tracking blob
        if re.match(r"^(https?:|www\.|index\.html|\S+\?\S+)", text, re.I):
            continue
        out.append((text, url))
    return out


def classify(text, url, M, people, books, artists, known):
    hay = (text + " " + url.replace("_", " ").replace("/", " ")).lower()
    nodes = set()
    for concept, rx in M.items():
        if rx.search(hay) and concept in known:
            nodes.add(concept)
    for name, title in people.items():
        if re.search(r"\b" + re.escape(name) + r"\b", hay) and title in known:
            nodes.add(title)
    for tl, title in books.items():
        if tl in hay and title in known:
            nodes.add(title)
    for name, title in artists.items():
        if name in hay:
            nodes.add(title)
    return nodes


def safe_text(t: str) -> str:
    return t.replace("[", "(").replace("]", ")").replace("|", "/").strip()


def render(groups: dict, total: int, connected: int) -> str:
    lines = [START, "## Connections", "",
             f"*Every bookmark on this page wired to the ideas, people, and books it "
             f"touches — {connected} of {total} links connected ({len(groups)} nodes).*", ""]
    for node in sorted(groups, key=lambda n: (-len(groups[n]), n)):
        items = groups[node][:PER_NODE]
        extra = f" …+{len(groups[node]) - len(items)} more" if len(groups[node]) > len(items) else ""
        bms = " · ".join(f"[{safe_text(t)}]({u})" for t, u in items)
        lines.append(f"**[[{node}]]** — {bms}{extra}")
        lines.append("")
    lines.append(END)
    return "\n".join(lines)


def write_block(note: Path, block: str) -> bool:
    text = note.read_text()
    if START in text and END in text:
        new = re.sub(re.escape(START) + r".*?" + re.escape(END), block, text, flags=re.S)
    else:
        anchor = "<!-- vault-crosslinks:start -->"
        if anchor in text:
            new = text.replace(anchor, block + "\n\n" + anchor, 1)
        else:
            new = text.rstrip() + "\n\n" + block + "\n"
    if new != text:
        note.write_text(new)
        return True
    return False


def main():
    known = known_targets()
    M = {c: compile_kw(k) for c, k in CONCEPT_KW.items()}
    people = people_matcher()
    books = book_matcher()
    artists = artist_matcher()

    # map source_relpath -> page note path
    note_by_src = {}
    for p in PAGES.glob("*.md"):
        m = re.search(r'source_relpath:\s*"([^"]+)"', p.read_text(errors="ignore"))
        if m:
            note_by_src[m.group(1)] = p

    grand = 0
    for html_file in sorted(KB_DIR.glob("*.html")):
        src = f"knowledge_base/{html_file.name}"
        note = note_by_src.get(src)
        if not note:
            continue
        links = extract_links(html_file.read_text(errors="ignore"))
        if not links:
            continue
        groups: dict[str, list] = {}
        connected = 0
        for text, url in links:
            nodes = classify(text, url, M, people, books, artists, known)
            if nodes:
                connected += 1
            for n in nodes:
                groups.setdefault(n, []).append((text, url))
        if not groups:
            continue
        write_block(note, render(groups, len(links), connected))
        grand += sum(len(v) for v in groups.values())
        print(f"  {html_file.name}: {len(links)} links, {connected} connected, {len(groups)} nodes")
    print(f"Knowledge base wired: {grand} bookmark→node links.")


if __name__ == "__main__":
    main()
