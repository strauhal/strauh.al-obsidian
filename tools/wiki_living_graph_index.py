#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path


VAULT = Path(__file__).resolve().parents[1]
KNOWLEDGE = VAULT / "knowledge"
WIKI = KNOWLEDGE / "wiki"
PRIVATE = KNOWLEDGE / "private"
OUTPUT = KNOWLEDGE / "output"
INDEX_PATH = OUTPUT / "living-graph-index.json"

STOPWORDS = {
    "a", "about", "after", "again", "all", "also", "am", "an", "and", "any",
    "are", "as", "at", "be", "because", "been", "before", "being", "between",
    "both", "but", "by", "can", "could", "did", "do", "does", "doing", "during",
    "each", "few", "for", "from", "further", "had", "has", "have", "having",
    "he", "her", "here", "hers", "herself", "him", "himself", "his", "how",
    "i", "if", "in", "into", "is", "it", "its", "itself", "just", "me", "more",
    "most", "my", "myself", "no", "nor", "not", "now", "of", "off", "on",
    "once", "only", "or", "other", "our", "ours", "ourselves", "out", "over",
    "own", "same", "she", "should", "so", "some", "such", "than", "that", "the",
    "their", "theirs", "them", "themselves", "then", "there", "these", "they",
    "this", "those", "through", "to", "too", "under", "until", "up", "very",
    "was", "we", "were", "what", "when", "where", "which", "while", "who",
    "whom", "why", "will", "with", "would", "you", "your", "yours", "yourself",
    "yourselves", "ernest", "strauhal", "map", "generated", "note", "notes",
}

TYPE_COLORS = {
    "concept": "#4dbf9f",
    "work": "#f59f63",
    "person": "#ef6f6c",
    "map": "#a98bd4",
    "book": "#72a7cf",
    "reading": "#72a7cf",
    "music": "#e7c45b",
    "movie": "#df77a8",
    "dream": "#9884c9",
    "image": "#7d9287",
    "criticism": "#d58e62",
    "private-correspondence": "#9b7c7c",
}


def frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}
    fields: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip().strip('"')
    return fields


def strip_markup(text: str) -> str:
    text = re.sub(r"^---.*?^---\s*", "", text, flags=re.M | re.S)
    text = re.sub(r"!\[\[([^\]]+)\]\]", " ", text)
    text = re.sub(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|([^\]]+))?\]\]", lambda m: m.group(2) or m.group(1), text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"[*_#>|~-]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def tokens(value: str) -> list[str]:
    words = re.findall(r"[a-z0-9][a-z0-9'.-]{1,}", value.lower())
    return [word.strip(".'-") for word in words if word not in STOPWORDS and len(word.strip(".'-")) > 1]


def wikilinks(text: str) -> list[str]:
    return [
        match.group(1).strip()
        for match in re.finditer(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]", text)
        if "/" not in match.group(1)
    ]


def image_embed(text: str) -> str:
    match = re.search(r"!\[\[([^\]|]+\.(?:png|jpe?g|gif|webp))(?:\|[^\]]+)?\]\]", text, re.I)
    if match:
        return match.group(1)
    match = re.search(r"!\[[^\]]*\]\(([^)]+\.(?:png|jpe?g|gif|webp))\)", text, re.I)
    return match.group(1) if match else ""


def note_paths() -> list[tuple[Path, bool]]:
    paths = [(path, False) for path in WIKI.rglob("*.md")]
    if PRIVATE.exists():
        paths += [(path, True) for path in PRIVATE.rglob("*.md")]
    return sorted(paths, key=lambda item: str(item[0]))


def build() -> dict:
    raw_docs: list[dict] = []
    title_to_id: dict[str, int] = {}
    document_frequency: Counter[str] = Counter()

    for path, is_private in note_paths():
        text = path.read_text(errors="ignore")
        fm = frontmatter(text)
        title = fm.get("title") or path.stem
        note_type = fm.get("type") or path.parent.name.rstrip("s") or "note"
        clean = strip_markup(text)
        token_counts = Counter(tokens(f"{title} {title} {clean[:7000]}"))
        for token in token_counts:
            document_frequency[token] += 1
        doc_id = len(raw_docs)
        relative = path.relative_to(VAULT).as_posix()
        title_to_id.setdefault(title.lower(), doc_id)
        title_to_id.setdefault(path.stem.lower(), doc_id)
        raw_docs.append({
            "id": doc_id,
            "title": title,
            "path": relative,
            "type": note_type,
            "private": is_private or fm.get("private", "").lower() == "true",
            "excerpt": clean[:900],
            "links_raw": wikilinks(text),
            "image": image_embed(text),
            "counts": token_counts,
        })

    total = max(len(raw_docs), 1)
    docs: list[dict] = []
    for doc in raw_docs:
        weighted = []
        for token, count in doc["counts"].items():
            idf = math.log((total + 1) / (document_frequency[token] + 1)) + 1
            score = (1 + math.log(count)) * idf
            weighted.append((token, round(score, 3)))
        weighted.sort(key=lambda item: item[1], reverse=True)
        links = []
        for target in doc["links_raw"]:
            target_id = title_to_id.get(target.lower())
            if target_id is not None and target_id != doc["id"]:
                links.append(target_id)
        docs.append({
            "id": doc["id"],
            "title": doc["title"],
            "path": doc["path"],
            "type": doc["type"],
            "private": doc["private"],
            "excerpt": doc["excerpt"],
            "image": doc["image"],
            "links": list(dict.fromkeys(links))[:80],
            "terms": weighted[:72],
            "color": TYPE_COLORS.get(doc["type"], "#8c969f"),
        })

    backlinks: dict[int, list[int]] = defaultdict(list)
    for doc in docs:
        for target in doc["links"]:
            backlinks[target].append(doc["id"])
    for doc in docs:
        doc["backlinks"] = backlinks.get(doc["id"], [])[:80]

    return {
        "version": 1,
        "generated": dt.datetime.now().isoformat(timespec="seconds"),
        "noteCount": len(docs),
        "docs": docs,
    }


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    payload = build()
    INDEX_PATH.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    size_mb = INDEX_PATH.stat().st_size / 1024 / 1024
    print(f"Built Living Graph index for {payload['noteCount']} notes ({size_mb:.1f} MB).")


if __name__ == "__main__":
    main()
