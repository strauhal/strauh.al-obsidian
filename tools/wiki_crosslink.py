#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path


VAULT = Path(__file__).resolve().parents[1]
OUTPUT = VAULT / "knowledge" / "output"
REPORT_PATH = OUTPUT / "vault-crosslinks.json"
START = "<!-- vault-crosslinks:start -->"
END = "<!-- vault-crosslinks:end -->"

STOPWORDS = {
    "a", "about", "after", "again", "all", "also", "am", "an", "and", "any",
    "are", "as", "at", "be", "because", "been", "before", "being", "between",
    "both", "but", "by", "can", "could", "did", "do", "does", "doing", "during",
    "each", "for", "from", "further", "had", "has", "have", "having", "he", "her",
    "here", "hers", "herself", "him", "himself", "his", "how", "i", "if", "in",
    "into", "is", "it", "its", "itself", "just", "me", "more", "most", "my",
    "myself", "no", "nor", "not", "now", "of", "off", "on", "once", "only",
    "or", "other", "our", "ours", "ourselves", "out", "over", "own", "same",
    "she", "should", "so", "some", "such", "than", "that", "the", "their",
    "theirs", "them", "themselves", "then", "there", "these", "they", "this",
    "those", "through", "to", "too", "under", "until", "up", "very", "was",
    "we", "were", "what", "when", "where", "which", "while", "who", "whom",
    "why", "will", "with", "would", "you", "your", "yours", "yourself",
    "yourselves", "map", "note", "notes", "generated", "source", "file",
    "original", "path", "unknown", "untitled", "image", "images", "collection",
    "strauhal", "ernest", "true", "false", "undated", "html", "markdown",
    "index", "details", "main", "front",
}

NOISY_TOKEN = re.compile(r"^(?:[a-f0-9]{7,}|\d+|[a-z0-9]{12,})$", re.I)
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
MANAGED_RE = re.compile(
    rf"\n?{re.escape(START)}.*?{re.escape(END)}\n?",
    flags=re.S,
)

FIELD_WEIGHTS = {
    "artist": 2.8,
    "author": 2.8,
    "category": 1.5,
    "collection": 1.3,
    "inferred_year": 0.7,
    "year": 0.7,
}

PRIORITY_TYPES = {
    "concept": 0.34,
    "work": 0.30,
    "person": 0.28,
    "map": 0.24,
    "criticism": 0.24,
    "source": 0.16,
    "book": 0.10,
}


@dataclass
class Note:
    id: int
    path: Path
    relative: str
    title: str
    note_type: str
    text: str
    clean: str
    frontmatter: dict[str, str]
    tokens: Counter[str]
    existing_targets: list[str]
    existing_ids: set[int] = field(default_factory=set)
    weighted: dict[str, float] = field(default_factory=dict)


def visible_markdown() -> list[Path]:
    paths = []
    for path in VAULT.rglob("*.md"):
        relative = path.relative_to(VAULT)
        if any(part.startswith(".") for part in relative.parts):
            continue
        paths.append(path)
    return sorted(paths)


def without_managed(text: str) -> str:
    return MANAGED_RE.sub("\n", text).rstrip() + "\n"


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}
    result = {}
    for line in text[4:end].splitlines():
        if ":" not in line or line.startswith((" ", "\t")):
            continue
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip().strip('"')
    return result


def strip_markup(text: str) -> str:
    text = re.sub(r"^---.*?^---\s*", "", text, flags=re.M | re.S)
    text = re.sub(r"!\[\[[^\]]+\]\]", " ", text)
    text = re.sub(
        r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|([^\]]+))?\]\]",
        lambda match: match.group(2) or match.group(1),
        text,
    )
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"[*_#>|~]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def tokenize(value: str) -> list[str]:
    words = re.findall(r"[a-z][a-z0-9'.-]{1,}", value.lower())
    result = []
    for word in words:
        word = word.strip(".'-")
        if len(word) < 3 or word in STOPWORDS or NOISY_TOKEN.fullmatch(word):
            continue
        result.append(word)
    return result


def normalized(value: str) -> str:
    return " ".join(tokenize(value))


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def infer_type(path: Path, fields: dict[str, str]) -> str:
    explicit = fields.get("type") or fields.get("source_kind")
    if explicit:
        return explicit.lower().strip()
    parts = path.relative_to(VAULT).parts
    if "wiki" in parts:
        index = parts.index("wiki")
        if index + 1 < len(parts) - 1:
            return parts[index + 1].rstrip("s")
    if "archive" in parts:
        return "archive"
    if "private" in parts:
        return "private"
    if "raw" in parts:
        return "raw"
    if "output" in parts:
        return "report"
    return "note"


def build_notes() -> list[Note]:
    notes = []
    for path in visible_markdown():
        text = without_managed(path.read_text(errors="ignore"))
        fields = parse_frontmatter(text)
        title = fields.get("title") or path.stem
        clean = strip_markup(text)
        feature_text = f"{title} {title} {title} {title} {clean[:16000]}"
        metadata = " ".join(
            f"{value} {value}"
            for key, value in fields.items()
            if key in FIELD_WEIGHTS
        )
        counts = Counter(tokenize(f"{feature_text} {metadata}"))
        notes.append(Note(
            id=len(notes),
            path=path,
            relative=path.relative_to(VAULT).as_posix(),
            title=title,
            note_type=infer_type(path, fields),
            text=text,
            clean=clean,
            frontmatter=fields,
            tokens=counts,
            existing_targets=[match.group(1).strip() for match in WIKILINK_RE.finditer(text)],
        ))
    return notes


def build_lookup(notes: list[Note]) -> dict[str, int]:
    lookup: dict[str, int] = {}
    priority: dict[int, int] = {}
    for note in notes:
        score = 3 if "/knowledge/wiki/" in f"/{note.relative}" else 1
        if note.note_type in {"concept", "work", "person", "map"}:
            score += 3
        elif note.note_type == "book":
            score += 2
        priority[note.id] = score
        keys = {
            note.title,
            note.path.stem,
            note.relative.removesuffix(".md"),
        }
        aliases = note.frontmatter.get("aliases", "")
        keys.update(part.strip() for part in re.findall(r"[^,\[\]]+", aliases) if part.strip())
        for key in keys:
            for variant in {key, key.lower(), slug(key)}:
                current = lookup.get(variant)
                if current is None or score > priority[current]:
                    lookup[variant] = note.id
    return lookup


def resolve_existing(notes: list[Note], lookup: dict[str, int]) -> None:
    for note in notes:
        for target in note.existing_targets:
            variants = [
                target,
                target.lower(),
                slug(target),
                Path(target).stem,
                Path(target).stem.lower(),
            ]
            target_id = next((lookup[key] for key in variants if key in lookup), None)
            if target_id is not None and target_id != note.id:
                note.existing_ids.add(target_id)


def weight_terms(notes: list[Note]) -> dict[str, list[tuple[int, float]]]:
    frequency: Counter[str] = Counter()
    for note in notes:
        frequency.update(note.tokens.keys())
    total = len(notes)
    postings: dict[str, list[tuple[int, float]]] = defaultdict(list)
    for note in notes:
        raw = {}
        for term, count in note.tokens.items():
            df = frequency[term]
            if df < 2 or df > 420:
                continue
            idf = math.log((total + 1) / (df + 1)) + 1
            raw[term] = (1 + math.log(count)) * idf
        strongest = dict(sorted(raw.items(), key=lambda item: item[1], reverse=True)[:44])
        norm = math.sqrt(sum(value * value for value in strongest.values())) or 1
        note.weighted = {term: value / norm for term, value in strongest.items()}
        for term, value in note.weighted.items():
            postings[term].append((note.id, value))
    return postings


def title_mentions(
    notes: list[Note],
    lookup: dict[str, int],
) -> tuple[dict[tuple[str, ...], list[int]], dict[str, list[int]]]:
    phrases: dict[tuple[str, ...], list[int]] = defaultdict(list)
    singles: dict[str, list[int]] = defaultdict(list)
    document_frequency: Counter[str] = Counter()
    for note in notes:
        document_frequency.update(note.tokens.keys())
    for note in notes:
        canonical = lookup.get(slug(note.title)) or lookup.get(note.title.lower())
        if canonical is not None and canonical != note.id:
            continue
        title_tokens = tuple(tokenize(note.title))
        if 2 <= len(title_tokens) <= 6:
            phrases[title_tokens].append(note.id)
        elif (
            len(title_tokens) == 1
            and len(title_tokens[0]) >= 5
            and document_frequency[title_tokens[0]] <= 50
        ):
            singles[title_tokens[0]].append(note.id)
    phrases = {
        phrase: ids for phrase, ids in phrases.items()
        if len(ids) <= 3
    }
    return phrases, singles


def add_candidate(
    candidates: dict[int, tuple[float, set[str]]],
    target_id: int,
    score: float,
    reason: str,
) -> None:
    current_score, reasons = candidates.get(target_id, (0.0, set()))
    reasons.add(reason)
    candidates[target_id] = (current_score + score, reasons)


def metadata_candidates(notes: list[Note]) -> dict[tuple[str, str], list[int]]:
    groups: dict[tuple[str, str], list[int]] = defaultdict(list)
    for note in notes:
        for field_name in FIELD_WEIGHTS:
            value = normalized(note.frontmatter.get(field_name, ""))
            if value and value not in {"unknown", "undated"}:
                groups[(field_name, value)].append(note.id)
    return groups


def parent_groups(notes: list[Note]) -> dict[Path, list[int]]:
    groups: dict[Path, list[int]] = defaultdict(list)
    for note in notes:
        groups[note.path.parent].append(note.id)
    return groups


def discovered_for(
    note: Note,
    notes: list[Note],
    postings: dict[str, list[tuple[int, float]]],
    phrase_map: dict[tuple[str, ...], list[int]],
    single_map: dict[str, list[int]],
    metadata_groups: dict[tuple[str, str], list[int]],
    siblings: dict[Path, list[int]],
) -> list[tuple[int, float, str]]:
    candidates: dict[int, tuple[float, set[str]]] = {}

    shared_terms: dict[int, list[tuple[str, float]]] = defaultdict(list)
    for term, own_weight in note.weighted.items():
        for target_id, target_weight in postings.get(term, []):
            if target_id == note.id:
                continue
            contribution = own_weight * target_weight
            shared_terms[target_id].append((term, contribution))
    for target_id, contributions in shared_terms.items():
        contributions.sort(key=lambda item: item[1], reverse=True)
        score = sum(value for _, value in contributions[:10])
        if score < 0.055:
            continue
        terms = ", ".join(term for term, _ in contributions[:3])
        add_candidate(candidates, target_id, score, f"shared language: {terms}")

    for field_name, field_weight in FIELD_WEIGHTS.items():
        value = normalized(note.frontmatter.get(field_name, ""))
        if not value or value in {"unknown", "undated"}:
            continue
        group = metadata_groups.get((field_name, value), [])
        if len(group) > 260 and field_name not in {"artist", "author"}:
            continue
        for target_id in group:
            if target_id != note.id:
                add_candidate(candidates, target_id, field_weight, f"same {field_name}: {value}")

    words = tokenize(note.clean[:16000])
    word_set = set(words)
    for size in range(2, 7):
        for index in range(0, len(words) - size + 1):
            phrase = tuple(words[index:index + size])
            for target_id in phrase_map.get(phrase, []):
                if target_id != note.id:
                    add_candidate(candidates, target_id, 2.4 + size * 0.18, "named in this note")
    for word in word_set:
        targets = single_map.get(word, [])
        if len(targets) == 1 and targets[0] != note.id:
            add_candidate(candidates, targets[0], 1.75, "named in this note")

    for target_id, (score, reasons) in list(candidates.items()):
        target = notes[target_id]
        target_archived = "/archive/" in f"/{target.relative}" or target.relative.startswith("_archive/")
        note_archived = "/archive/" in f"/{note.relative}" or note.relative.startswith("_archive/")
        if target_archived and not note_archived:
            del candidates[target_id]
            continue
        score += PRIORITY_TYPES.get(target.note_type, 0)
        if target.note_type == note.note_type and target.note_type in {"image", "archive"}:
            score *= 0.92
        if target_id in note.existing_ids:
            score *= 0.25
        candidates[target_id] = (score, reasons)

    ranked = []
    for target_id, (score, reasons) in candidates.items():
        if target_id in note.existing_ids:
            continue
        reason = sorted(reasons, key=lambda value: (not value.startswith("same "), value))[0]
        ranked.append((target_id, score, reason))
    ranked.sort(key=lambda item: (-item[1], notes[item[0]].title.lower()))

    limit = 8
    if note.note_type in {"image", "archive", "anchor", "redirect"}:
        limit = 5
    elif note.note_type in {"collection", "artist"}:
        limit = 6
    selected = [item for item in ranked if item[1] >= 0.07][:limit]

    if len(selected) < min(3, limit):
        same_parent = [
            notes[other_id] for other_id in siblings[note.path.parent]
            if other_id != note.id
            and other_id not in note.existing_ids
            and all(other_id != item[0] for item in selected)
        ]
        same_parent.sort(key=lambda other: abs(other.id - note.id))
        for other in same_parent:
            selected.append((other.id, 0.01, "nearby note in the same source series"))
            if len(selected) >= min(3, limit):
                break
    return selected


def link_for(note: Note) -> str:
    target = note.relative.removesuffix(".md")
    label = note.title.replace("|", "-").replace("]", ")")
    return f"[[{target}|{label}]]"


def write_blocks(
    notes: list[Note],
    discoveries: dict[int, list[tuple[int, float, str]]],
) -> None:
    for note in notes:
        lines = [
            START,
            "## Discovered Connections",
            "",
        ]
        for target_id, score, reason in discoveries[note.id]:
            target = notes[target_id]
            lines.append(f"- {link_for(target)} — {reason}")
        if not discoveries[note.id]:
            lines.append("- [[knowledge/wiki/Home|strauh.al Knowledge Base]] — vault home")
        lines.append(END)
        block = "\n".join(lines)
        clean = without_managed(note.path.read_text(errors="ignore")).rstrip()
        note.path.write_text(f"{clean}\n\n{block}\n")


def connection_report(
    notes: list[Note],
    discoveries: dict[int, list[tuple[int, float, str]]],
) -> dict:
    directed_existing = sum(len(note.existing_ids) for note in notes)
    directed_discovered = sum(len(items) for items in discoveries.values())
    edges: set[tuple[int, int]] = set()
    per_file = {}
    for note in notes:
        targets = set(note.existing_ids)
        targets.update(item[0] for item in discoveries[note.id])
        for target_id in targets:
            edges.add(tuple(sorted((note.id, target_id))))
        per_file[note.relative] = {
            "title": note.title,
            "type": note.note_type,
            "existingOutbound": len(note.existing_ids),
            "discoveredOutbound": len(discoveries[note.id]),
            "totalOutbound": len(targets),
        }
    by_type: dict[str, dict[str, int]] = defaultdict(lambda: {
        "files": 0,
        "existingOutbound": 0,
        "discoveredOutbound": 0,
    })
    for note in notes:
        row = by_type[note.note_type]
        row["files"] += 1
        row["existingOutbound"] += len(note.existing_ids)
        row["discoveredOutbound"] += len(discoveries[note.id])
    return {
        "generated": dt.datetime.now().isoformat(timespec="seconds"),
        "markdownFiles": len(notes),
        "existingDirectedLinks": directed_existing,
        "discoveredDirectedLinks": directed_discovered,
        "totalDirectedLinks": directed_existing + directed_discovered,
        "uniqueConnectedPairs": len(edges),
        "filesWithDiscoveredLinks": sum(bool(discoveries[note.id]) for note in notes),
        "minimumDiscoveredLinks": min(len(discoveries[note.id]) for note in notes),
        "maximumDiscoveredLinks": max(len(discoveries[note.id]) for note in notes),
        "byType": dict(sorted(by_type.items())),
        "perFile": per_file,
    }


def main() -> None:
    notes = build_notes()
    lookup = build_lookup(notes)
    resolve_existing(notes, lookup)
    postings = weight_terms(notes)
    phrase_map, single_map = title_mentions(notes, lookup)
    metadata_groups = metadata_candidates(notes)
    siblings = parent_groups(notes)
    discoveries = {
        note.id: discovered_for(
            note,
            notes,
            postings,
            phrase_map,
            single_map,
            metadata_groups,
            siblings,
        )
        for note in notes
    }
    write_blocks(notes, discoveries)
    report = connection_report(notes, discoveries)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(
        "Cross-linked "
        f"{report['markdownFiles']} Markdown files with "
        f"{report['discoveredDirectedLinks']} discovered links; "
        f"{report['uniqueConnectedPairs']} unique connected pairs total."
    )


if __name__ == "__main__":
    main()
