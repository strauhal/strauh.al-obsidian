#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import zipfile
from pathlib import Path
from typing import Any


VAULT = Path(__file__).resolve().parents[1]
RAW_ROOT = VAULT / "knowledge" / "raw" / "chatgpt"
CHAT_ROOT = VAULT / "knowledge" / "wiki" / "chatgpt"
MAPS = VAULT / "knowledge" / "wiki" / "maps"
OUTPUT = VAULT / "knowledge" / "output"
STATE = OUTPUT / "chatgpt-import-state.json"
DOWNLOAD_DIRS = [
    Path.home() / "Downloads",
    Path.home() / "Library" / "Mobile Documents" / "com~apple~CloudDocs" / "Downloads",
]


def slug(value: str, fallback: str = "untitled") -> str:
    result = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return result[:120] or fallback


def yaml_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def timestamp(value: Any) -> str:
    try:
        return dt.datetime.fromtimestamp(float(value), tz=dt.timezone.utc).isoformat()
    except (TypeError, ValueError, OSError):
        return ""


def content_text(message: dict[str, Any]) -> str:
    content = message.get("content") or {}
    parts = content.get("parts") or []
    rendered: list[str] = []
    for part in parts:
        if isinstance(part, str):
            rendered.append(part)
        elif isinstance(part, dict):
            text = part.get("text") or part.get("content")
            if isinstance(text, str):
                rendered.append(text)
    if not rendered and isinstance(content.get("text"), str):
        rendered.append(content["text"])
    return "\n\n".join(piece.strip() for piece in rendered if piece.strip())


def ordered_messages(conversation: dict[str, Any]) -> list[dict[str, Any]]:
    mapping = conversation.get("mapping") or {}
    messages: list[tuple[float, dict[str, Any]]] = []
    for node in mapping.values():
        message = (node or {}).get("message")
        if not isinstance(message, dict):
            continue
        text = content_text(message)
        if not text:
            continue
        created = message.get("create_time") or 0
        messages.append((float(created or 0), message))
    messages.sort(key=lambda item: item[0])
    return [message for _, message in messages]


def extract_archive(source: Path) -> tuple[Path, Path | None]:
    if source.is_dir():
        conversations = source / "conversations.json"
        return conversations, source
    if source.suffix.lower() == ".json":
        return source, source.parent
    if source.suffix.lower() != ".zip":
        raise ValueError("Expected a ChatGPT export ZIP, conversations.json, or extracted export folder.")
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    target = RAW_ROOT / "exports" / stamp
    target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(source) as archive:
        archive.extractall(target)
    candidates = list(target.rglob("conversations.json"))
    if not candidates:
        raise ValueError("The export did not contain conversations.json.")
    return candidates[0], target


def archive_contains_conversations(path: Path) -> bool:
    if path.suffix.lower() != ".zip":
        return False
    try:
        with zipfile.ZipFile(path) as archive:
            return any(Path(name).name == "conversations.json" for name in archive.namelist())
    except (OSError, zipfile.BadZipFile):
        return False


def discover_inputs() -> tuple[Path | None, Path | None]:
    exports: list[Path] = []
    memories: list[Path] = []
    for folder in DOWNLOAD_DIRS:
        if not folder.exists():
            continue
        for path in folder.iterdir():
            if path.is_file() and archive_contains_conversations(path):
                exports.append(path)
            if path.is_file() and path.name.lower() in {
                "chatgpt memory summary.txt",
                "chatgpt-memory-summary.txt",
            }:
                memories.append(path)
    export = max(exports, key=lambda path: path.stat().st_mtime) if exports else None
    memory = max(memories, key=lambda path: path.stat().st_mtime) if memories else None
    return export, memory


def fingerprint(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_state() -> dict[str, str]:
    if not STATE.exists():
        return {}
    try:
        value = json.loads(STATE.read_text())
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_state(state: dict[str, str]) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, indent=2) + "\n")


def write_conversation(conversation: dict[str, Any], index: int) -> dict[str, Any]:
    title = (conversation.get("title") or f"Untitled conversation {index}").strip()
    conversation_id = conversation.get("id") or conversation.get("conversation_id") or str(index)
    created = timestamp(conversation.get("create_time"))
    updated = timestamp(conversation.get("update_time"))
    messages = ordered_messages(conversation)
    filename = f"{slug(title)}-{str(conversation_id)[:8]}.md"
    path = CHAT_ROOT / "conversations" / filename
    body = [
        "---",
        f"title: {yaml_quote('ChatGPT - ' + title)}",
        "type: chatgpt-conversation",
        f"conversation_id: {yaml_quote(str(conversation_id))}",
        f"conversation_created: {yaml_quote(created)}",
        f"conversation_updated: {yaml_quote(updated)}",
        f"message_count: {len(messages)}",
        "status: imported",
        "tags: [chatgpt, conversation, imported]",
        f"created: {dt.date.today().isoformat()}",
        f"updated: {dt.date.today().isoformat()}",
        "---",
        "",
        f"# {title}",
        "",
        f"Imported from ChatGPT. Messages: {len(messages)}.",
        "",
    ]
    user_text: list[str] = []
    assistant_text: list[str] = []
    for message in messages:
        role = ((message.get("author") or {}).get("role") or "unknown").title()
        text = content_text(message)
        if role.lower() == "user":
            user_text.append(text)
        elif role.lower() == "assistant":
            assistant_text.append(text)
        body += [f"## {role}", "", text, ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(body), encoding="utf-8")
    return {
        "title": title,
        "note": f"ChatGPT - {title}",
        "created": created,
        "updated": updated,
        "messages": len(messages),
        "user_text": "\n".join(user_text),
        "assistant_text": "\n".join(assistant_text),
    }


def write_index(records: list[dict[str, Any]]) -> None:
    today = dt.date.today().isoformat()
    records.sort(key=lambda item: item["updated"] or item["created"], reverse=True)
    lines = [
        "---",
        "title: Map - ChatGPT Conversations",
        "type: map",
        "tags: [map, chatgpt, conversations]",
        f"created: {today}",
        f"updated: {today}",
        "---",
        "",
        "# Map - ChatGPT Conversations",
        "",
        f"Imported conversations: {len(records)}",
        "",
        "Raw conversational history is preserved here. A chat records what was said; it is not automatically treated as an established fact or permanent memory.",
        "",
        "## Conversations",
        "",
    ]
    for record in records:
        date = (record["created"] or "")[:10]
        suffix = f" - {date}" if date else ""
        lines.append(f"- [[{record['note']}|{record['title']}]]{suffix} ({record['messages']} messages)")
    MAPS.mkdir(parents=True, exist_ok=True)
    (MAPS / "Map - ChatGPT Conversations.md").write_text("\n".join(lines) + "\n")


def memory_candidates(records: list[dict[str, Any]]) -> None:
    patterns = [
        r"\bI (?:am|live|work|teach|make|prefer|like|love|hate|use|have|want|need|believe)\b",
        r"\bmy (?:wife|husband|family|job|work|project|art|music|site|website|computer|home)\b",
        r"\bremember that\b",
    ]
    candidates: list[tuple[str, str]] = []
    for record in records:
        for paragraph in re.split(r"\n\s*\n", record["user_text"]):
            cleaned = re.sub(r"\s+", " ", paragraph).strip()
            if not 20 <= len(cleaned) <= 500:
                continue
            if any(re.search(pattern, cleaned, re.I) for pattern in patterns):
                candidates.append((record["note"], cleaned))
    deduped: list[tuple[str, str]] = []
    seen: set[str] = set()
    for note, text in candidates:
        key = re.sub(r"\W+", "", text.lower())
        if key in seen:
            continue
        seen.add(key)
        deduped.append((note, text))
    today = dt.date.today().isoformat()
    lines = [
        "---",
        "title: ChatGPT Memory Candidates",
        "type: review-queue",
        "status: needs-review",
        "tags: [chatgpt, memory, review]",
        f"created: {today}",
        f"updated: {today}",
        "---",
        "",
        "# ChatGPT Memory Candidates",
        "",
        "Automatically surfaced from Ernest's own messages. These are candidates, not verified facts. Promote only durable, current details into curated notes.",
        "",
    ]
    for note, text in deduped[:1000]:
        lines += [f"- [ ] {text}", f"  - Source: [[{note}]]"]
    (CHAT_ROOT / "Memory Candidates.md").write_text("\n".join(lines) + "\n")


def write_memory_summary(source: Path) -> None:
    text = source.read_text(errors="ignore").strip()
    today = dt.date.today().isoformat()
    RAW_ROOT.mkdir(parents=True, exist_ok=True)
    raw_copy = RAW_ROOT / "memory-summary.txt"
    raw_copy.write_text(text + "\n")
    body = f"""---
title: ChatGPT Memory Summary
type: memory-summary
status: imported
tags: [chatgpt, memory, imported]
source_file: {yaml_quote(str(raw_copy.relative_to(VAULT)))}
created: {today}
updated: {today}
---

# ChatGPT Memory Summary

Imported from ChatGPT's visible memory summary. OpenAI notes that this summary may not contain every detail inferred from past chats.

## Summary

{text}

## Editorial Rule

Treat this as ChatGPT's current synthesis, not as infallible autobiography. Correct stale or inaccurate details in curated notes rather than silently propagating them.
"""
    CHAT_ROOT.mkdir(parents=True, exist_ok=True)
    (CHAT_ROOT / "Memory Summary.md").write_text(body)


def write_hub(records: list[dict[str, Any]] | None = None) -> None:
    today = dt.date.today().isoformat()
    existing = list((CHAT_ROOT / "conversations").glob("*.md"))
    count = len(records) if records else len(existing)
    body = f"""---
title: Map - ChatGPT Memory
type: map
tags: [map, chatgpt, memory, conversations]
created: {today}
updated: {today}
---

# Map - ChatGPT Memory

A provenance-aware bridge between ChatGPT and the strauh.al knowledge base.

## Inputs

- [[Map - ChatGPT Conversations]] - {count} imported conversations.
- [[ChatGPT Memory Summary]] - ChatGPT's current visible synthesis, when supplied.
- [[ChatGPT Memory Candidates]] - first-person details surfaced for human review.
- [[Map - Ernest Creative Profile]] - restrained synthesis linked into the existing wiki.
- [[ChatGPT Memory Review]] - specific or time-sensitive claims awaiting confirmation.

## Trust Model

- Raw chats preserve context and wording.
- Memory candidates remain unchecked until reviewed.
- Curated wiki notes outrank inferred memories when they conflict.
- Sensitive, temporary, speculative, or third-party details should remain in raw history rather than becoming profile facts.

## Workflow

1. Export ChatGPT data and import the ZIP.
2. Paste the current ChatGPT memory summary into a text file and import it.
3. Review memory candidates and promote only durable context.
4. Re-run the normal vault refresh to lint and re-index everything.
"""
    MAPS.mkdir(parents=True, exist_ok=True)
    (MAPS / "Map - ChatGPT Memory.md").write_text(body)


def ensure_placeholders() -> None:
    today = dt.date.today().isoformat()
    CHAT_ROOT.mkdir(parents=True, exist_ok=True)
    MAPS.mkdir(parents=True, exist_ok=True)
    placeholders = {
        MAPS / "Map - ChatGPT Conversations.md": f"""---
title: Map - ChatGPT Conversations
type: map
status: awaiting-export
tags: [map, chatgpt, conversations]
created: {today}
updated: {today}
---

# Map - ChatGPT Conversations

Awaiting a ChatGPT account export. This note will become the chronological conversation index after import.
""",
        CHAT_ROOT / "Memory Candidates.md": f"""---
title: ChatGPT Memory Candidates
type: review-queue
status: awaiting-export
tags: [chatgpt, memory, review]
created: {today}
updated: {today}
---

# ChatGPT Memory Candidates

Awaiting a ChatGPT account export. Candidate facts will require review before promotion into the curated wiki.
""",
        CHAT_ROOT / "Memory Summary.md": f"""---
title: ChatGPT Memory Summary
type: memory-summary
status: awaiting-input
tags: [chatgpt, memory]
created: {today}
updated: {today}
---

# ChatGPT Memory Summary

Awaiting the current visible Memory Summary from ChatGPT Settings > Personalization > Memory.
""",
    }
    for path, body in placeholders.items():
        if not path.exists():
            path.write_text(body)


def write_report(records: list[dict[str, Any]], export_root: Path | None) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    report = [
        "# ChatGPT Import Report",
        "",
        f"Generated: {dt.datetime.now().isoformat(timespec='seconds')}",
        "",
        f"- Conversations imported: {len(records)}",
        f"- Messages imported: {sum(record['messages'] for record in records)}",
        f"- Export archive retained at: `{export_root}`" if export_root else "- Source was an existing JSON file.",
        "",
    ]
    (OUTPUT / "chatgpt-import-report.md").write_text("\n".join(report))


def main() -> None:
    parser = argparse.ArgumentParser(description="Import ChatGPT history and memory into Obsidian.")
    parser.add_argument("source", nargs="?", type=Path, help="ChatGPT export ZIP/folder/conversations.json")
    parser.add_argument("--memory-summary", type=Path, help="Text file copied from ChatGPT Memory Summary")
    args = parser.parse_args()
    CHAT_ROOT.mkdir(parents=True, exist_ok=True)
    ensure_placeholders()
    state = load_state()
    if not args.source and not args.memory_summary:
        args.source, args.memory_summary = discover_inputs()
    records: list[dict[str, Any]] = []
    export_root: Path | None = None
    if args.source:
        source = args.source.expanduser()
        source_fingerprint = fingerprint(source) if source.is_file() else str(source.stat().st_mtime)
        if state.get("export_fingerprint") != source_fingerprint:
            conversations_path, export_root = extract_archive(source)
            data = json.loads(conversations_path.read_text(errors="ignore"))
            if not isinstance(data, list):
                raise ValueError("conversations.json must contain a list.")
            records = [write_conversation(item, index) for index, item in enumerate(data, 1)]
            write_index(records)
            memory_candidates(records)
            write_report(records, export_root)
            state["export_fingerprint"] = source_fingerprint
            state["export_source"] = str(source)
    if args.memory_summary:
        memory_source = args.memory_summary.expanduser()
        memory_fingerprint = fingerprint(memory_source)
        if state.get("memory_fingerprint") != memory_fingerprint:
            write_memory_summary(memory_source)
            state["memory_fingerprint"] = memory_fingerprint
            state["memory_source"] = str(memory_source)
    save_state(state)
    write_hub(records)
    if not args.source and not args.memory_summary:
        print("Importer installed. Supply a ChatGPT export ZIP and/or --memory-summary file.")
    else:
        print(f"Imported {len(records)} ChatGPT conversations.")


if __name__ == "__main__":
    main()
