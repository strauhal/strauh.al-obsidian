#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import json
import math
import re
import sqlite3
import struct
import subprocess
import sys
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any


VAULT = Path(__file__).resolve().parents[1]
KNOWLEDGE = VAULT / "knowledge"
WIKI = KNOWLEDGE / "wiki"
OUTPUT = KNOWLEDGE / "output"
SETTINGS_PATH = KNOWLEDGE / "raw" / "ollama-settings.json"
LIVING_INDEX = OUTPUT / "living-graph-index.json"
SEMANTIC_DB = OUTPUT / "semantic-memory.sqlite"
STATE_PATH = OUTPUT / "ollama-intelligence-state.json"
IMAGE_REPORT = OUTPUT / "image-intelligence-report.md"
CRITIC_REPORT = OUTPUT / "connection-critic.md"
EVOLUTION_REPORT = OUTPUT / "Evolution of Ernest's Thinking.md"
CONSTELLATION_REPORT = OUTPUT / "constellation-build-report.md"
MANAGED_RE = re.compile(
    r"\n?<!-- vault-crosslinks:start -->.*?<!-- vault-crosslinks:end -->\n?",
    re.S,
)
LINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|([^\]]+))?\]\]")
STOPWORDS = {
    "the", "and", "for", "that", "with", "this", "from", "into", "about", "what",
    "where", "when", "which", "while", "have", "has", "had", "were", "was", "are",
    "you", "your", "their", "they", "them", "his", "her", "its", "not", "but",
    "can", "could", "would", "should", "just", "more", "most", "some", "than",
}


def settings() -> dict[str, Any]:
    defaults = {
        "generation_model": "gemma4:latest",
        "interactive_model": "gemma4:e2b-it-qat",
        "embedding_model": "embeddinggemma",
        "ollama_url": "http://127.0.0.1:11434",
        "context_tokens": 16384,
        "semantic_candidates": 48,
        "rerank_candidates": 24,
        "graph_results": 30,
        "include_private": False,
        "nightly_image_batch": 12,
        "nightly_critic_batch": 40,
    }
    if SETTINGS_PATH.exists():
        defaults.update(json.loads(SETTINGS_PATH.read_text()))
    return defaults


def api(path: str, payload: dict[str, Any], timeout: int = 180) -> dict[str, Any]:
    cfg = settings()
    request = urllib.request.Request(
        cfg["ollama_url"].rstrip("/") + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read())
    except urllib.error.URLError as error:
        raise RuntimeError(
            "Ollama is unavailable. Open Ollama.app and try again."
        ) from error


def embed(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    return api("/api/embed", {
        "model": settings()["embedding_model"],
        "input": texts,
        "truncate": True,
        "options": {"num_ctx": 4096},
    }, timeout=300)["embeddings"]


def generate(
    prompt: str,
    *,
    schema: dict[str, Any] | None = None,
    images: list[str] | None = None,
    temperature: float = 0.15,
    num_predict: int = 1200,
    model: str | None = None,
) -> Any:
    cfg = settings()
    payload: dict[str, Any] = {
        "model": model or cfg["generation_model"],
        "prompt": prompt,
        "stream": False,
        "think": False,
        "keep_alive": "10m",
        "options": {
            "temperature": temperature,
            "num_ctx": cfg["context_tokens"],
            "num_predict": num_predict,
        },
    }
    if schema:
        payload["format"] = schema
        payload["prompt"] = (
            "Return one valid JSON object matching the supplied schema. "
            "Use double-quoted JSON keys and strings, with no markdown or commentary.\n\n"
            + prompt
        )
    if images:
        payload["images"] = images
    response = api("/api/generate", payload, timeout=600)["response"].strip()
    if not schema:
        return response
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        repair_payload = dict(payload)
        repair_payload["prompt"] = (
            "Repair the following malformed output into one valid JSON object matching "
            "the supplied schema. Preserve its meaning, use double quotes, and output "
            "nothing except JSON.\n\nMALFORMED OUTPUT:\n" + response
        )
        repair_payload["options"] = dict(payload["options"])
        repair_payload["options"]["temperature"] = 0
        repaired = api("/api/generate", repair_payload, timeout=600)["response"].strip()
        return json.loads(repaired)


def state() -> dict[str, Any]:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {"images": {}, "critic": {}, "last_nightly": ""}


def save_state(value: dict[str, Any]) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(value, ensure_ascii=False, indent=2))


def clean_text(text: str) -> str:
    text = MANAGED_RE.sub("\n", text)
    text = re.sub(r"^---.*?^---\s*", "", text, flags=re.M | re.S)
    text = re.sub(r"!\[\[[^\]]+\]\]", " ", text)
    text = LINK_RE.sub(lambda match: match.group(2) or match.group(1), text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"[#*_>`~]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_generated_links(text: str) -> str:
    paired = re.compile(r"\[\[([^\[\]]+)\],\s*\[([^\[\]]+)\]\]")
    while paired.search(text):
        text = paired.sub(r"[[\1]], [[\2]]", text)
    return text


def fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode(errors="ignore")).hexdigest()


def pack_vector(vector: list[float]) -> bytes:
    return struct.pack(f"<{len(vector)}f", *vector)


def unpack_vector(blob: bytes) -> tuple[float, ...]:
    return struct.unpack(f"<{len(blob) // 4}f", blob)


def semantic_connection() -> sqlite3.Connection:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(SEMANTIC_DB)
    connection.row_factory = sqlite3.Row
    connection.execute("""
        create table if not exists embeddings (
            path text primary key,
            title text not null,
            type text not null,
            private integer not null,
            hash text not null,
            excerpt text not null,
            vector blob not null,
            magnitude real not null,
            updated text not null
        )
    """)
    return connection


def index_documents() -> list[dict[str, Any]]:
    payload = json.loads(LIVING_INDEX.read_text())
    documents = []
    for doc in payload.get("docs", []):
        path = VAULT / doc["path"]
        if not path.exists():
            continue
        text = clean_text(path.read_text(errors="ignore"))
        material = f"{doc['title']}\nType: {doc['type']}\n{text[:5200]}"
        documents.append({
            "path": doc["path"],
            "title": doc["title"],
            "type": doc["type"],
            "private": bool(doc.get("private")),
            "excerpt": text[:1400],
            "material": material,
            "hash": fingerprint(material),
        })
    return documents


def build_semantic_index(batch_size: int = 48) -> dict[str, int]:
    docs = index_documents()
    with semantic_connection() as connection:
        known = {
            row["path"]: row["hash"]
            for row in connection.execute("select path, hash from embeddings")
        }
        changed = [doc for doc in docs if known.get(doc["path"]) != doc["hash"]]
        valid = {doc["path"] for doc in docs}
        removed = [path for path in known if path not in valid]
        for path in removed:
            connection.execute("delete from embeddings where path = ?", (path,))
        completed = 0
        for offset in range(0, len(changed), batch_size):
            batch = changed[offset:offset + batch_size]
            vectors = embed([doc["material"] for doc in batch])
            now = dt.datetime.now().isoformat(timespec="seconds")
            rows = []
            for doc, vector in zip(batch, vectors):
                magnitude = math.sqrt(sum(value * value for value in vector)) or 1
                rows.append((
                    doc["path"], doc["title"], doc["type"], int(doc["private"]),
                    doc["hash"], doc["excerpt"], pack_vector(vector), magnitude, now,
                ))
            connection.executemany("""
                insert into embeddings
                (path, title, type, private, hash, excerpt, vector, magnitude, updated)
                values (?, ?, ?, ?, ?, ?, ?, ?, ?)
                on conflict(path) do update set
                    title=excluded.title, type=excluded.type, private=excluded.private,
                    hash=excluded.hash, excerpt=excluded.excerpt,
                    vector=excluded.vector, magnitude=excluded.magnitude,
                    updated=excluded.updated
            """, rows)
            connection.commit()
            completed += len(batch)
            print(f"Embedded {completed}/{len(changed)} changed notes.", file=sys.stderr)
    return {"documents": len(docs), "embedded": len(changed), "removed": len(removed)}


def terms(value: str) -> set[str]:
    return {
        word for word in re.findall(r"[a-z0-9][a-z0-9'.-]{2,}", value.lower())
        if word not in STOPWORDS
    }


def semantic_search(query: str, limit: int = 30) -> list[dict[str, Any]]:
    cfg = settings()
    query_vector = embed([query])[0]
    query_magnitude = math.sqrt(sum(value * value for value in query_vector)) or 1
    query_terms = terms(query)
    visual_query = bool(query_terms & {
        "image", "images", "photo", "photograph", "drawing", "visual", "painting",
    })
    reading_query = bool(query_terms & {
        "book", "books", "reading", "author", "essay", "paper",
    })
    rows = []
    with semantic_connection() as connection:
        sql = "select * from embeddings"
        parameters: tuple[Any, ...] = ()
        if not cfg["include_private"]:
            sql += " where private = ?"
            parameters = (0,)
        for row in connection.execute(sql, parameters):
            vector = unpack_vector(row["vector"])
            cosine = sum(a * b for a, b in zip(query_vector, vector))
            cosine /= query_magnitude * row["magnitude"]
            title_terms = terms(row["title"])
            excerpt_terms = terms(row["excerpt"])
            lexical = (
                len(query_terms & title_terms) * 0.08
                + len(query_terms & excerpt_terms) * 0.012
            )
            type_bonus = {
                "concept": 0.105, "work": 0.1, "map": 0.035,
                "person": 0.04, "criticism": 0.065,
                "book": 0.015 if reading_query else -0.045,
                "image": 0.02 if visual_query else -0.055,
            }.get(row["type"], 0)
            rows.append({
                "path": row["path"],
                "title": row["title"],
                "type": row["type"],
                "excerpt": row["excerpt"],
                "semantic": round(cosine, 5),
                "score": cosine * 0.82 + lexical + type_bonus,
            })
    rows.sort(key=lambda item: item["score"], reverse=True)
    return rows[:limit]


def interpret_query(query: str) -> dict[str, Any]:
    schema = {
        "type": "object",
        "properties": {
            "interpreted_query": {"type": "string"},
            "concepts": {"type": "array", "items": {"type": "string"}},
            "people": {"type": "array", "items": {"type": "string"}},
            "works": {"type": "array", "items": {"type": "string"}},
            "visual_intent": {"type": "boolean"},
            "reading_intent": {"type": "boolean"},
        },
        "required": [
            "interpreted_query", "concepts", "people", "works",
            "visual_intent", "reading_intent",
        ],
    }
    return generate(
        "Interpret this spoken request for a personal art-and-ideas knowledge vault. "
        "Expand metaphors into likely concepts without answering the request. "
        "Be conservative and retain the user's words. The people and works fields must "
        "contain only likely proper names or titles already implied by the request; use "
        "empty arrays instead of frameworks or invented examples. Set visual_intent or "
        "reading_intent true only when the user explicitly asks for images or readings.\n\n"
        f"Request: {query}",
        schema=schema,
        num_predict=420,
        model=settings()["interactive_model"],
    )


def rerank(query: str, candidates: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    schema = {
        "type": "object",
        "properties": {
            "results": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "reason": {"type": "string"},
                    },
                    "required": ["path", "reason"],
                },
            }
        },
        "required": ["results"],
    }
    compact = [
        {
            "path": item["path"],
            "title": item["title"],
            "type": item["type"],
            "excerpt": item["excerpt"][:440],
        }
        for item in candidates
    ]
    response = generate(
        "Rerank these candidate notes for the user's request. Select only supplied paths. "
        "Prefer conceptually explanatory notes plus a few concrete works or sources. "
        f"Return at most {limit} results.\n\n"
        f"Request: {query}\n\nCandidates:\n{json.dumps(compact, ensure_ascii=False)}",
        schema=schema,
        num_predict=900,
        model=settings()["interactive_model"],
    )
    by_path = {item["path"]: item for item in candidates}
    ranked = []
    for item in response["results"]:
        if item["path"] in by_path:
            combined = dict(by_path[item["path"]])
            combined["reason"] = item["reason"]
            ranked.append(combined)
    used = {item["path"] for item in ranked}
    ranked.extend(item for item in candidates if item["path"] not in used)
    return ranked[:limit]


def smart_retrieve(
    query: str,
    limit: int | None = None,
    use_gemma: bool = True,
    use_rerank: bool = True,
) -> dict[str, Any]:
    cfg = settings()
    limit = limit or cfg["graph_results"]
    interpretation = {"interpreted_query": query, "concepts": [], "people": [], "works": []}
    expanded = query
    if use_gemma and use_rerank:
        try:
            interpretation = interpret_query(query)
            expanded = " ".join([
                query,
                interpretation["interpreted_query"],
                *interpretation["concepts"],
                *interpretation["people"],
                *interpretation["works"],
            ])
        except Exception as error:
            print(f"Gemma interpretation unavailable: {error}", file=sys.stderr)
    candidates = semantic_search(expanded, cfg["semantic_candidates"])
    if use_gemma:
        try:
            candidates = rerank(
                query,
                candidates[:cfg["rerank_candidates"]],
                limit,
            )
        except Exception as error:
            print(f"Gemma reranking unavailable: {error}", file=sys.stderr)
    return {
        "query": query,
        "interpretation": interpretation,
        "results": candidates[:limit],
    }


def cited_answer(question: str) -> Path:
    retrieval = smart_retrieve(question, limit=14)
    sources = retrieval["results"]
    context = "\n\n".join(
        f"SOURCE {index + 1}: [[{item['path'].removesuffix('.md')}|{item['title']}]]\n"
        f"{item['excerpt'][:1200]}"
        for index, item in enumerate(sources)
    )
    answer = generate(
        "Answer the question using only the supplied vault sources. Every substantive "
        "claim must carry an Obsidian wikilink citation copied exactly from the source "
        "header. If evidence is incomplete, say so. End with a short 'Open Questions' "
        "section.\n\n"
        f"Question: {question}\n\n{context}",
        temperature=0.2,
        num_predict=2600,
    )
    answer = normalize_generated_links(answer)
    timestamp = dt.datetime.now().strftime("%Y-%m-%d %H%M%S")
    path = OUTPUT / "answers" / f"{timestamp} - Vault Answer.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\n"
        f'title: "Vault Answer - {question[:80].replace(chr(34), chr(39))}"\n'
        "type: vault-answer\n"
        f"created: {dt.date.today().isoformat()}\n"
        f'model: "{settings()["generation_model"]}"\n'
        "---\n\n"
        f"# {question}\n\n{answer}\n\n"
        "## Retrieved Sources\n\n"
        + "\n".join(
            f"- [[{item['path'].removesuffix('.md')}|{item['title']}]]"
            for item in sources
        )
        + "\n"
    )
    return path


def parse_discovered(path: Path) -> list[tuple[str, str]]:
    text = path.read_text(errors="ignore")
    match = re.search(
        r"<!-- vault-crosslinks:start -->(.*?)<!-- vault-crosslinks:end -->",
        text,
        re.S,
    )
    if not match:
        return []
    results = []
    for line in match.group(1).splitlines():
        link = LINK_RE.search(line)
        if link and " — " in line:
            results.append((link.group(1), line.split(" — ", 1)[1].strip()))
    return results


def connection_critic(limit: int | None = None) -> Path:
    cfg = settings()
    limit = limit or cfg["nightly_critic_batch"]
    current = state()
    queue = []
    for path in sorted(WIKI.rglob("*.md")):
        discovered = parse_discovered(path)
        if not discovered:
            continue
        digest = fingerprint(path.read_text(errors="ignore"))
        if current["critic"].get(str(path.relative_to(VAULT))) == digest:
            continue
        source_excerpt = clean_text(path.read_text(errors="ignore"))[:850]
        for target, reason in discovered[:4]:
            target_path = VAULT / f"{target}.md"
            if not target_path.exists():
                continue
            queue.append({
                "source_path": str(path.relative_to(VAULT)),
                "source_title": path.stem,
                "source_excerpt": source_excerpt,
                "target_path": f"{target}.md",
                "target_title": target_path.stem,
                "target_excerpt": clean_text(target_path.read_text(errors="ignore"))[:650],
                "automatic_reason": reason,
            })
            if len(queue) >= limit:
                break
        if len(queue) >= limit:
            break
    schema = {
        "type": "object",
        "properties": {
            "reviews": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "source_path": {"type": "string"},
                        "target_path": {"type": "string"},
                        "decision": {"type": "string", "enum": ["keep", "reject", "uncertain"]},
                        "confidence": {"type": "number"},
                        "relationship": {"type": "string"},
                        "rationale": {"type": "string"},
                        "intermediary_concept": {"type": "string"},
                    },
                    "required": [
                        "source_path", "target_path", "decision", "confidence",
                        "relationship", "rationale", "intermediary_concept",
                    ],
                },
            }
        },
        "required": ["reviews"],
    }
    if queue:
        result = generate(
            "Audit proposed links in a personal knowledge vault. Reject generic shared "
            "vocabulary and accidental filename matches. Keep relationships that would "
            "help a thoughtful reader navigate ideas, influences, works, or evidence.\n\n"
            + json.dumps(queue, ensure_ascii=False),
            schema=schema,
            num_predict=2200,
        )
        reviews = result["reviews"]
    else:
        reviews = []
    lines = [
        "# Connection Critic",
        "",
        f"Generated: {dt.datetime.now().isoformat(timespec='seconds')}",
        "",
        "| Decision | Confidence | Source | Target | Relationship | Rationale |",
        "| --- | ---: | --- | --- | --- | --- |",
    ]
    for review in reviews:
        lines.append(
            f"| {review['decision']} | {review['confidence']:.2f} | "
            f"`{review['source_path']}` | `{review['target_path']}` | "
            f"{review['relationship']} | {review['rationale']} |"
        )
        source_path = VAULT / review["source_path"]
        if source_path.exists():
            current["critic"][review["source_path"]] = fingerprint(
                source_path.read_text(errors="ignore")
            )
    CRITIC_REPORT.write_text("\n".join(lines) + "\n")
    save_state(current)
    return CRITIC_REPORT


def build_constellations() -> list[Path]:
    candidates = []
    for folder in ["concepts", "works", "people", "culture", "dreams", "maps"]:
        folder_paths = [
            path for path in sorted((WIKI / folder).glob("*.md"))
            if not path.name.startswith("Constellation - ")
        ][:16]
        for path in folder_paths:
            text = clean_text(path.read_text(errors="ignore"))
            candidates.append({
                "path": str(path.relative_to(VAULT)),
                "title": path.stem,
                "kind": folder.rstrip("s"),
                "excerpt": text[:300],
            })
    schema = {
        "type": "object",
        "properties": {
            "constellations": {
                "type": "array",
                "minItems": 5,
                "maxItems": 5,
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "thesis": {"type": "string"},
                        "paths": {
                            "type": "array",
                            "minItems": 6,
                            "maxItems": 12,
                            "items": {"type": "string"},
                        },
                        "questions": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["title", "thesis", "paths", "questions"],
                },
            }
        },
        "required": ["constellations"],
    }
    result = generate(
        "Create exactly 5 useful, non-obvious cross-domain knowledge maps from this personal art, "
        "music, technology, dream, and philosophy vault. Copy paths exactly from the "
        "supplied candidate objects; never invent a path or a general-knowledge topic. "
        "Do not discuss stars, astronomy, or named star patterns. Each map should join "
        "at least three different kinds of note and "
        "have 6-12 paths. Avoid generic categories.\n\n"
        + json.dumps(candidates, ensure_ascii=False),
        schema=schema,
        num_predict=2600,
    )
    valid = {item["path"] for item in candidates}
    written = []
    report = ["# Constellation Build Report", ""]
    for constellation in result["constellations"]:
        title = re.sub(r"[/\\:*?\"<>|]+", " ", constellation["title"]).strip()
        path = WIKI / "maps" / f"Constellation - {title}.md"
        paths = [item for item in constellation["paths"] if item in valid]
        if len(paths) < 3:
            report.append(f"- Rejected `{title}`: fewer than three valid vault paths.")
            continue
        links = []
        by_path = {item["path"]: item["title"] for item in candidates}
        for target in paths:
            links.append(f"- [[{target.removesuffix('.md')}|{by_path[target]}]]")
        body = (
            "---\n"
            f'title: "Constellation - {title}"\n'
            "type: map\n"
            "tags: [map, constellation, gemma]\n"
            f"updated: {dt.date.today().isoformat()}\n"
            f'model: "{settings()["generation_model"]}"\n'
            "---\n\n"
            f"# {title}\n\n{constellation['thesis']}\n\n"
            "## Notes\n\n" + "\n".join(links) + "\n\n"
            "## Questions\n\n"
            + "\n".join(f"- {question}" for question in constellation["questions"])
            + "\n"
        )
        path.write_text(body)
        written.append(path)
        report.append(f"- [[{path.relative_to(VAULT).as_posix().removesuffix('.md')}|{title}]]")
    CONSTELLATION_REPORT.write_text("\n".join(report) + "\n")
    return written


def evolution_report() -> Path:
    material = []
    diary_path = KNOWLEDGE / "raw" / "diary.md"
    if diary_path.exists():
        text = MANAGED_RE.sub("\n", diary_path.read_text(errors="ignore"))
        date_re = re.compile(
            r"(?im)^(?:january|february|march|april|may|june|july|august|"
            r"september|october|november|december)\s+\d{1,2}(?:st|nd|rd|th)?"
            r",?\s+20\d{2}\s*$"
        )
        matches = list(date_re.finditer(text))
        entries = [
            text[match.start():(matches[index + 1].start() if index + 1 < len(matches) else len(text))]
            for index, match in enumerate(matches)
        ]
        selected_indexes = set(range(0, len(entries), max(1, len(entries) // 20)))
        theme_re = re.compile(
            r"\b(ai|artificial intelligence|authorship|internet|screen|voice|"
            r"attention|tiktok|memory|archive|death|die|love|married|marriage|"
            r"god|spiritual|control|artist|art|music|recovery|therapy)\b",
            re.I,
        )
        selected_indexes.update(
            index for index, entry in enumerate(entries) if theme_re.search(entry)
        )
        for index in sorted(selected_indexes)[:34]:
            material.append(
                "SOURCE [[knowledge/raw/diary|diary]]\n"
                + clean_text(entries[index])[:1250]
            )
    ideas_path = KNOWLEDGE / "raw" / "ideas-sketchbook.md"
    if ideas_path.exists():
        ideas = [
            line.strip() for line in ideas_path.read_text(errors="ignore").splitlines()
            if len(line.strip()) > 30
        ]
        sampled = ideas[::max(1, len(ideas) // 30)][:30]
        material.append(
            "SOURCE [[knowledge/raw/ideas-sketchbook|ideas-sketchbook]]\n"
            + "\n".join(sampled)
        )
    answer = generate(
        "Trace changes, contradictions, and recurring returns in this artist's thinking. "
        "Organize chronologically where dates permit. Distinguish evidence from inference. "
        "Cite every section with the exact supplied Obsidian source link. Focus on AI and "
        "authorship, preservation, internet identity, artistic control, mortality, love, "
        "spirituality, and attention.\n\n" + "\n\n".join(material)[:60000],
        temperature=0.2,
        num_predict=3600,
    )
    EVOLUTION_REPORT.write_text(
        "---\n"
        "title: Evolution of Ernest's Thinking\n"
        "type: analysis\n"
        "tags: [analysis, evolution, contradictions, gemma]\n"
        f"updated: {dt.date.today().isoformat()}\n"
        f'model: "{settings()["generation_model"]}"\n'
        "---\n\n"
        "# Evolution of Ernest's Thinking\n\n"
        + answer + "\n"
    )
    return EVOLUTION_REPORT


def resolve_image_path(note_path: Path) -> Path | None:
    text = note_path.read_text(errors="ignore")
    match = re.search(r"source_file:\s*\"([^\"]+)\"", text)
    if match:
        source = Path(match.group(1))
        if source.exists():
            return source
    match = re.search(r"!\[\[([^\]|]+\.(?:png|jpe?g|webp))", text, re.I)
    if match:
        source = VAULT / match.group(1)
        if source.exists():
            return source
    return None


def enrich_images(limit: int | None = None) -> Path:
    cfg = settings()
    limit = limit or cfg["nightly_image_batch"]
    current = state()
    queue = []
    for note_path in sorted((WIKI / "images").glob("*.md")):
        image_path = resolve_image_path(note_path)
        if not image_path:
            continue
        digest = fingerprint(
            f"{note_path.stat().st_mtime_ns}:{image_path.stat().st_mtime_ns}:{image_path.stat().st_size}"
        )
        relative = str(note_path.relative_to(VAULT))
        if current["images"].get(relative) == digest:
            continue
        queue.append((note_path, image_path, digest))
        if len(queue) >= limit:
            break
    schema = {
        "type": "object",
        "properties": {
            "subjects": {"type": "array", "items": {"type": "string"}},
            "motifs": {"type": "array", "items": {"type": "string"}},
            "medium": {"type": "string"},
            "period": {"type": "string"},
            "colors": {"type": "array", "items": {"type": "string"}},
            "visible_text": {"type": "string"},
            "artist_candidates": {"type": "array", "items": {"type": "string"}},
            "concepts": {"type": "array", "items": {"type": "string"}},
            "description": {"type": "string"},
        },
        "required": [
            "subjects", "motifs", "medium", "period", "colors", "visible_text",
            "artist_candidates", "concepts", "description",
        ],
    }
    lines = ["# Image Intelligence Report", ""]
    for index, (note_path, image_path, digest) in enumerate(queue, 1):
        encoded = base64.b64encode(image_path.read_bytes()).decode()
        result = generate(
            "Analyze this image for a personal visual knowledge archive. Be descriptive "
            "and conservative; artist_candidates must be empty unless visual evidence is "
            "meaningful. Concepts should be useful cross-linking ideas, not generic nouns.",
            schema=schema,
            images=[encoded],
            num_predict=1000,
        )
        sidecar = note_path.with_name(note_path.stem + " - Visual Analysis.md")
        sidecar.write_text(
            "---\n"
            f'title: "Visual Analysis - {note_path.stem.replace(chr(34), chr(39))}"\n'
            "type: image-analysis\n"
            "tags: [image-analysis, gemma, visual-archive]\n"
            f"updated: {dt.date.today().isoformat()}\n"
            f'model: "{cfg["generation_model"]}"\n'
            "---\n\n"
            f"# Visual Analysis - {note_path.stem}\n\n"
            f"Source: [[{note_path.relative_to(VAULT).as_posix().removesuffix('.md')}|{note_path.stem}]]\n\n"
            f"{result['description']}\n\n"
            f"- **Subjects:** {', '.join(result['subjects']) or 'Unclear'}\n"
            f"- **Motifs:** {', '.join(result['motifs']) or 'Unclear'}\n"
            f"- **Medium:** {result['medium']}\n"
            f"- **Period:** {result['period']}\n"
            f"- **Colors:** {', '.join(result['colors'])}\n"
            f"- **Visible text:** {result['visible_text'] or 'None'}\n"
            f"- **Artist candidates:** {', '.join(result['artist_candidates']) or 'None'}\n"
            f"- **Concepts:** {', '.join(result['concepts'])}\n"
        )
        current["images"][str(note_path.relative_to(VAULT))] = digest
        lines.append(f"- {index}. [[{sidecar.relative_to(VAULT).as_posix().removesuffix('.md')}|{sidecar.stem}]]")
        save_state(current)
    IMAGE_REPORT.write_text("\n".join(lines) + "\n")
    return IMAGE_REPORT


def nightly() -> None:
    build_semantic_index()
    critic = connection_critic()
    constellations = build_constellations()
    evolution = evolution_report()
    images = enrich_images()
    current = state()
    current["last_nightly"] = dt.datetime.now().isoformat(timespec="seconds")
    save_state(current)
    for script in [
        "tools/wiki_crosslink.py",
        "tools/wiki_living_graph_index.py",
        "tools/wiki_search.py",
        "tools/wiki_lint.py",
    ]:
        subprocess.run([sys.executable, script], cwd=VAULT, check=True)
    build_semantic_index()
    print(f"Critic: {critic.relative_to(VAULT)}")
    print(f"Constellations: {len(constellations)}")
    print(f"Evolution: {evolution.relative_to(VAULT)}")
    print(f"Images: {images.relative_to(VAULT)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Local Ollama intelligence for the strauh.al vault")
    subparsers = parser.add_subparsers(dest="command", required=True)
    index_parser = subparsers.add_parser("index")
    index_parser.add_argument("--batch-size", type=int, default=48)
    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("query")
    search_parser.add_argument("--limit", type=int, default=20)
    search_parser.add_argument("--no-gemma", action="store_true")
    graph_parser = subparsers.add_parser("graph")
    graph_parser.add_argument("query")
    graph_parser.add_argument("--limit", type=int, default=None)
    graph_parser.add_argument("--no-gemma", action="store_true")
    answer_parser = subparsers.add_parser("answer")
    answer_parser.add_argument("question")
    critic_parser = subparsers.add_parser("critic")
    critic_parser.add_argument("--limit", type=int, default=None)
    subparsers.add_parser("constellations")
    subparsers.add_parser("evolution")
    image_parser = subparsers.add_parser("images")
    image_parser.add_argument("--limit", type=int, default=None)
    subparsers.add_parser("nightly")
    args = parser.parse_args()

    if args.command == "index":
        print(json.dumps(build_semantic_index(args.batch_size), indent=2))
    elif args.command in {"search", "graph"}:
        result = smart_retrieve(
            args.query,
            limit=args.limit,
            use_gemma=not getattr(args, "no_gemma", False),
            use_rerank=args.command != "graph",
        )
        print(json.dumps(result, ensure_ascii=False))
    elif args.command == "answer":
        print(cited_answer(args.question))
    elif args.command == "critic":
        print(connection_critic(args.limit))
    elif args.command == "constellations":
        for path in build_constellations():
            print(path)
    elif args.command == "evolution":
        print(evolution_report())
    elif args.command == "images":
        print(enrich_images(args.limit))
    elif args.command == "nightly":
        nightly()


if __name__ == "__main__":
    main()
