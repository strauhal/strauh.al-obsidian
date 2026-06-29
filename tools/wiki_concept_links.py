#!/usr/bin/env python3
"""Wire concept notes down into the archive — by filename.

For each curated concept, scan every image and book note and link the ones whose
*filename* reliably signals the concept (color works -> Synesthesia, religious art
-> Art Fills the God-Shaped Hole, trains -> Trainpilled, …). Junk filenames
(IMG_1234, hashes, "error api request", "PDF document") are skipped. The links are
written into a managed `<!-- archive-links -->` block in each concept note, so the
pass is idempotent and re-runs as the archive grows. Every emitted target is
verified to resolve, so the lint stays at zero broken links.
"""
from __future__ import annotations

import re
from pathlib import Path


VAULT = Path(__file__).resolve().parents[1]
WIKI = VAULT / "knowledge" / "wiki"
CONCEPTS = WIKI / "concepts"
IMAGES = WIKI / "images"
BOOKS = WIKI / "books"

IMG_PER_CONCEPT = 60
BOOK_PER_CONCEPT = 40

START = "<!-- archive-links:start -->"
END = "<!-- archive-links:end -->"

# Filenames that are camera/counter/id noise, not descriptive titles.
_JUNK_PREFIX = re.compile(
    r"^(img|dsc|dscn|pxl|p\d|gif\d?|dcim|screenshot|screen shot|photo|fb|received|"
    r"tumblr|gd|image|original|thumbnail|file|pasted|untitled\b(?!.*\bby\b))",
    re.I,
)
_JUNK_SUBSTR = re.compile(
    r"error|api request|could not retrieve|jpeg image|pdf document|fulltext|"
    r"contentserver|^\d+$|^[0-9a-f]{12,}$|status \d", re.I,
)


def reliable(title: str) -> bool:
    t = title.strip()
    words = re.findall(r"[a-zA-Z]{3,}", t)
    if len(words) < 2:
        return False
    if _JUNK_SUBSTR.search(t):
        return False
    if _JUNK_PREFIX.match(t) and " by " not in t.lower():
        return False
    # reject titles that are mostly digits/hex
    alpha = sum(c.isalpha() for c in t)
    return alpha >= max(6, len(t) * 0.4)


# Concept title -> keyword signals matched against archive filenames.
KEYWORDS: dict[str, list[str]] = {
    "Latent Space": ["gan", "stylegan", "latent", "interpolat*", "neural net", "vqvae", "vq-vae", "diffusion", "deepdream", "deep dream", "embedding", "generative"],
    "Interpolating the Instruction Set": ["interpolat*", "latent", "gan", "vqvae", "diffusion", "morph", "transition", "in-between", "stylegan"],
    "Human-Machine Tug of War": ["gan", "pix2pix", "ai generated", "ai-generated", "generative", "stable diffusion", "midjourney", "dall", "deepdream"],
    "AI Slop": ["midjourney", "stable diffusion", "dall-e", "ai generated", "ai-generated", "ai slop", "slop", "deepfake", "upscaled", "prompt"],
    "Synesthesia": ["color", "colour", "chromatic", "spectrum", "rainbow", "scriabin", "kandinsky", "synesth*", "prismatic", "iridescent", "color study", "colour study", "hue"],
    "Dead Architecture": ["architecture", "building", "ruin", "brutalis*", "concrete", "facade", "tower", "construction", "demolition", "scaffold", "edifice", "manhattan bridge", "skyscraper"],
    "Trainpilled": ["train", "trains", "railroad", "railway", "locomotive", "subway", "tram", "monorail", "boxcar", "freight train", "train station", "elevated train", "el train", "amtrak", "metra", "tokaido", "rail "],
    "The Flâneur as Web Surfer": ["arcade", "street", "city", "boulevard", "promenade", "crowd", "sidewalk", "cityscape", "urban", "passage", "flaneur", "flâneur", "shop", "cafe", "café", "metropolis", "pedestrian"],
    "Art Fills the God-Shaped Hole": ["god", "saint", "angel", "church", "cathedral", "religious", "icon", "madonna", "christ", "jesus", "buddha", "sacred", "altar", "prayer", "crucifix", "halo", "temple", "virgin", "biblical", "apostle", "heaven", "divine", "witch", "devil", "demon", "judgment", "prophet", "annunciation", "pieta", "nativity", "saul", "francis", "gospel", "holy"],
    "Memory and Preservation": ["old photo", "oldphotos", "vintage", "memorial", "sepia", "daguerreotype", "tintype", "heirloom", "archival", "faded photograph", "family photo"],
    "Autofiction": ["self-portrait", "self portrait", "selfie", "diary", "journal", "autobiograph*", "confession"],
    "Amor Fati": ["nietzsche", "zarathustra", "stoic", "memento mori", "eternal return", "marcus aurelius", "vanitas", "amor fati"],
    "Post-Irony": ["meme", "greentext", "4chan", "copypasta", "wojak", "pepe", "shitpost", "ironic", "demotivational"],
    "Spontaneity and Elegance": ["sketch", "gesture", "brushstroke", "line drawing", "calligraph*", "doodle", "loose drawing", "improvis*", "sumi", "continuous line"],
    "Transmitting My Neural Signals by Hand": ["drawing", "ink", "vellum", "handwriting", "notation", "pencil", "charcoal", "pen and", "graphite", "scribble", "hand-drawn", "hand drawn"],
    "The Tedium of the Art Is the Goal": ["study", "etude", "exercise", "practice", "repetition", "iteration", "wip", "process", "studies"],
    "The Attention Economy": ["tiktok", "instagram", "twitter", "advertis*", "billboard", "attention", "algorithm", "influencer", "clickbait", "feed", "scrolling", "commercial"],
    "The Internet as Confidant": ["internet", "forum", "online", "discord", "reddit", "blog", "website", "webpage", "chatroom", "myspace", "web art"],
    "The Oedipal Screen": ["screen", "monitor", "television", " tv ", "vr ", "virtual reality", "computer", "crt", "projector", "display", "cathode", "windows 9", "macintosh", "desktop"],
    "The Spatial Web": ["atlas", "diagram", "grid", "network", "topolog*", "lattice", "schematic", "blueprint", "isometric", "wireframe", "map of", "3d "],
    "To Render Myself Unnecessary": ["teacher", "teaching", "classroom", "lesson", "pupil", "pedagog*", "tutorial", "instruction", "lecture", "chalkboard", "blackboard"],
    "The Archive as Consciousness": ["archive", "catalogue", "catalog", "index", "database", "repository", "filing", "card catalog"],
    "Reading Like a Computer": ["attention span", "distracted", "deep work", "shallows", "amusing ourselves", "scattered minds", "adhd", "attention deficit", "focus"],
    "Rebuilding from the Bottom": ["ruin", "rebuild", "phoenix", "ashes", "reconstruct*", "debris", "wreck", "rebirth", "resurrect*", "fractured", "broken"],
    "Atomization": ["atomis*", "atomiz*", "lonel*", "isolat*", "alienat*", "solitude", "alone", "houellebecq", "capitalist realism", "crowd"],
}


def title_of_image(path: Path) -> str:
    return re.sub(r" [0-9a-f]{8}$", "", path.stem)


def fm_title(text: str, fallback: str) -> str:
    m = re.search(r"^title:\s*(.+)$", text, re.M)
    return (m.group(1).strip().strip('"') if m else fallback)


def matchers():
    """A keyword ending in '*' is a stem (prefix match, e.g. 'interpolat*').
    A plain single word matches whole-word only (so 'gan' doesn't hit 'gandalf').
    Anything with spaces/hyphens is a substring phrase."""
    out = {}
    for concept, kws in KEYWORDS.items():
        parts = []
        for kw in kws:
            kw = kw.lower()
            if kw.endswith("*"):
                parts.append(r"\b" + re.escape(kw[:-1]))
            elif re.fullmatch(r"[a-z]+", kw):
                parts.append(r"\b" + re.escape(kw) + r"\b")
            else:
                parts.append(re.escape(kw))
        out[concept] = re.compile("|".join(parts))
    return out


def scan():
    M = matchers()
    hits: dict[str, dict[str, list]] = {c: {"img": [], "book": []} for c in KEYWORDS}

    for p in IMAGES.glob("*.md"):
        title = title_of_image(p)
        if not reliable(title):
            continue
        low = title.lower()
        for concept, rx in M.items():
            found = rx.findall(low)
            if found:
                hits[concept]["img"].append((len(set(found)), p.stem, title))

    for p in BOOKS.glob("*.md"):
        text = p.read_text(errors="ignore")
        title = fm_title(text, p.stem)
        if not reliable(title):
            continue
        low = title.lower()
        for concept, rx in M.items():
            found = rx.findall(low)
            if found:
                hits[concept]["book"].append((len(set(found)), p.stem, title))
    return hits


def render_block(img: list, book: list) -> str:
    img = sorted(img, key=lambda x: (-x[0], x[2]))
    book = sorted(book, key=lambda x: (-x[0], x[2]))
    n_img, n_book = len(img), len(book)
    lines = [START, "## In the archive", "",
             "*Images and books connected to this idea by filename (auto-generated).*", ""]
    if img:
        shown = img[:IMG_PER_CONCEPT]
        links = " · ".join(f"[[{stem}|{title}]]" for _, stem, title in shown)
        extra = f" …and {n_img - len(shown)} more" if n_img > len(shown) else ""
        lines += [f"**Images ({n_img}).** {links}{extra}", ""]
    if book:
        shown = book[:BOOK_PER_CONCEPT]
        links = " · ".join(f"[[{stem}|{title}]]" for _, stem, title in shown)
        extra = f" …and {n_book - len(shown)} more" if n_book > len(shown) else ""
        lines += [f"**Books ({n_book}).** {links}{extra}", ""]
    lines.append(END)
    return "\n".join(lines)


def write_block(concept: str, block: str) -> bool:
    path = CONCEPTS / f"{concept}.md"
    if not path.exists():
        return False
    text = path.read_text()
    if START in text and END in text:
        new = re.sub(re.escape(START) + r".*?" + re.escape(END), block, text, flags=re.S)
    else:
        # insert before any vault-crosslinks block, else append
        anchor = "<!-- vault-crosslinks:start -->"
        if anchor in text:
            new = text.replace(anchor, block + "\n\n" + anchor, 1)
        else:
            new = text.rstrip() + "\n\n" + block + "\n"
    if new != text:
        path.write_text(new)
        return True
    return False


def main():
    hits = scan()
    changed = 0
    total_img = total_book = 0
    for concept in KEYWORDS:
        img, book = hits[concept]["img"], hits[concept]["book"]
        if not img and not book:
            continue
        total_img += len(img)
        total_book += len(book)
        if write_block(concept, render_block(img, book)):
            changed += 1
        print(f"  {concept}: {len(img)} images, {len(book)} books")
    print(f"Wired {changed} concepts; {total_img} image links, {total_book} book links.")


if __name__ == "__main__":
    main()
