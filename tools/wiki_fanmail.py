#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import hashlib
import html
import os
import re
import shutil
from collections import Counter, defaultdict
from email import policy
from email.message import Message
from email.parser import BytesParser
from email.utils import parseaddr, parsedate_to_datetime
from pathlib import Path


VAULT = Path(__file__).resolve().parents[1]
SOURCE = Path.home() / "Desktop" / "fanmail"
PRIVATE = VAULT / "knowledge" / "private" / "fanmail"
ORIGINALS = PRIVATE / "originals"
ATTACHMENTS = PRIVATE / "attachments"
THREADS = PRIVATE / "threads"
MAPS = VAULT / "knowledge" / "wiki" / "maps"
CONCEPTS = VAULT / "knowledge" / "wiki" / "concepts"
RAW = VAULT / "knowledge" / "raw"
OUTPUT = VAULT / "knowledge" / "output"
OWN_ADDRESSES = {"ernest@strauh.al", "estrauhal@gmail.com"}


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:100] or "no-subject"


def thread_subject(value: str) -> str:
    value = re.sub(r"^(?:(?:re|aw|fw|fwd)\s*[:_]\s*)+", "", value.strip(), flags=re.I)
    return value or "(No Subject)"


def redact(value: str) -> str:
    value = html.unescape(value)
    value = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[email redacted]", value)
    value = re.sub(r"(?<!\w)(?:\+?\d[\d(). -]{7,}\d)", "[phone redacted]", value)
    value = re.sub(r"https?://(?:meetings|calendly)\.[^\s>)]+", "[scheduling link redacted]", value)
    return value


def current_message(value: str) -> str:
    lines: list[str] = []
    for line in value.replace("\r", "").splitlines():
        probe = line.strip()
        if probe.startswith(">"):
            break
        if re.match(r"^On .+ wrote:\s*$", probe):
            break
        if re.match(r"^On .+<.*>\s*wrote:\s*$", probe):
            break
        if re.match(r"^_{5,}$", probe):
            break
        if re.match(r"^(Von|From):\s", probe, re.I):
            break
        if probe == "--":
            break
        lines.append(line.rstrip())
    return redact("\n".join(lines).strip())


def body_text(message: Message) -> str:
    plain: list[str] = []
    html: list[str] = []
    for part in message.walk():
        if part.get_content_disposition() == "attachment":
            continue
        try:
            content = part.get_content()
        except Exception:
            continue
        if not isinstance(content, str):
            continue
        if part.get_content_type() == "text/plain":
            plain.append(content)
        elif part.get_content_type() == "text/html":
            formatted = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</li>", "\n", content)
            html.append(re.sub(r"<[^>]+>", " ", formatted))
    return "\n".join(plain or html).strip()


def message_date(message: Message) -> str:
    try:
        return parsedate_to_datetime(str(message.get("date"))).isoformat()
    except Exception:
        return ""


def category(subject: str, body: str, attachment_count: int) -> str:
    value = f"{subject} {body}".lower()
    if attachment_count or any(word in value for word in ("drawing", "submission", "my pic", "site drawings", "draw club", "art title")):
        return "drawing-submission"
    if any(word in value for word in ("bug", "broken link", "404", "name change", "changes in website")):
        return "site-feedback"
    if any(word in value for word in ("catching up", "pleasure to meet", "dinner tmrw")):
        return "private-correspondence"
    if any(word in value for word in ("love your archive", "love your website", "love the site", "coolest website", "saw your ads", "you, the beholder")):
        return "audience-response"
    return "other"


def parse_messages() -> list[dict]:
    messages: list[dict] = []
    for path in sorted(SOURCE.glob("*.eml")):
        raw = path.read_bytes()
        message = BytesParser(policy=policy.default).parsebytes(raw)
        display_name, address = parseaddr(str(message.get("from") or ""))
        address = address.lower()
        subject = str(message.get("subject") or "").strip()
        body = body_text(message)
        digest = hashlib.sha256(
            (address + "\n" + subject.lower() + "\n" + re.sub(r"\s+", " ", body).strip()).encode()
        ).hexdigest()
        attachments = []
        for part in message.iter_attachments():
            payload = part.get_payload(decode=True) or b""
            attachments.append({
                "name": part.get_filename() or "attachment",
                "type": part.get_content_type(),
                "bytes": payload,
                "digest": hashlib.sha256(payload).hexdigest(),
            })
        messages.append({
            "path": path,
            "raw": raw,
            "digest": digest,
            "message_id": str(message.get("message-id") or "").strip(),
            "address": address,
            "display_name": display_name.strip(),
            "direction": "outgoing" if address in OWN_ADDRESSES else "incoming",
            "subject": subject,
            "thread": thread_subject(subject),
            "date": message_date(message),
            "body": current_message(body),
            "attachments": attachments,
        })
    unique: dict[str, dict] = {}
    for message in messages:
        unique.setdefault(message["message_id"] or message["digest"], message)
    return list(unique.values())


def correspondent_aliases(messages: list[dict]) -> dict[str, str]:
    addresses = sorted({m["address"] for m in messages if m["direction"] == "incoming"})
    return {address: f"Correspondent {index:02d}" for index, address in enumerate(addresses, 1)}


def preserve_originals(messages: list[dict]) -> None:
    ORIGINALS.mkdir(parents=True, exist_ok=True)
    for index, message in enumerate(sorted(messages, key=lambda m: (m["date"], m["subject"])), 1):
        name = f"{index:03d}-{slug(message['thread'])}-{message['digest'][:8]}.eml"
        (ORIGINALS / name).write_bytes(message["raw"])


def preserve_attachments(messages: list[dict]) -> dict[str, Path]:
    ATTACHMENTS.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for message in messages:
        for attachment in message["attachments"]:
            digest = attachment["digest"]
            ext = Path(attachment["name"]).suffix.lower() or ".bin"
            path = ATTACHMENTS / f"{digest[:12]}{ext}"
            if not path.exists():
                path.write_bytes(attachment["bytes"])
            paths[digest] = path
    return paths


def write_threads(messages: list[dict], aliases: dict[str, str], attachment_paths: dict[str, Path]) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for message in messages:
        grouped[message["thread"].lower()].append(message)
    THREADS.mkdir(parents=True, exist_ok=True)
    name_aliases = [
        (message["display_name"], aliases[message["address"]])
        for message in messages
        if message["direction"] == "incoming"
        and message["display_name"]
        and message["address"] in aliases
    ]
    first_name_aliases = [
        (display_name.split()[0], alias)
        for display_name, alias in name_aliases
        if len(display_name.split()[0]) >= 4
    ]
    records: list[dict] = []
    for index, (_, thread_messages) in enumerate(sorted(grouped.items()), 1):
        thread_messages.sort(key=lambda m: m["date"])
        title = thread_messages[0]["thread"]
        incoming = [m for m in thread_messages if m["direction"] == "incoming"]
        categories = Counter(category(m["subject"], m["body"], len(m["attachments"])) for m in incoming)
        primary_category = categories.most_common(1)[0][0] if categories else "private-correspondence"
        participants = sorted({aliases.get(m["address"], "Ernest") for m in thread_messages})
        note_title = f"Private Correspondence - {index:02d} - {title}"
        lines = [
            "---",
            f'title: "{note_title.replace(chr(34), chr(39))}"',
            "type: private-correspondence",
            "private: true",
            f"category: {primary_category}",
            f"message_count: {len(thread_messages)}",
            f"incoming_count: {len(incoming)}",
            "tags: [private, correspondence, fanmail]",
            f"created: {dt.date.today().isoformat()}",
            f"updated: {dt.date.today().isoformat()}",
            "---",
            "",
            f"# {title}",
            "",
            f"**Participants:** {', '.join(participants)}",
            "",
            f"**Category:** {primary_category}",
            "",
        ]
        attachment_count = 0
        thread_attachment_paths: list[Path] = []
        for message in thread_messages:
            sender = aliases.get(message["address"], "Ernest")
            safe_body = message["body"]
            for display_name, alias in name_aliases:
                safe_body = re.sub(re.escape(display_name), alias, safe_body, flags=re.I)
            for first_name, alias in first_name_aliases:
                safe_body = re.sub(rf"\b{re.escape(first_name)}\b", alias, safe_body, flags=re.I)
            lines += [
                f"## {message['date'][:10] or 'Unknown date'} - {sender}",
                "",
                f"**Direction:** {message['direction']}",
                "",
                safe_body or "(No body text.)",
                "",
            ]
            for attachment in message["attachments"]:
                path = attachment_paths[attachment["digest"]]
                relative = path.relative_to(VAULT).as_posix()
                lines += [f"![[{relative}]]", ""]
                attachment_count += 1
                thread_attachment_paths.append(path)
        (THREADS / f"{index:02d}-{slug(title)}.md").write_text("\n".join(lines))
        thread_path = THREADS / f"{index:02d}-{slug(title)}.md"
        records.append({
            "title": title,
            "note": note_title,
            "path": thread_path,
            "category": primary_category,
            "messages": len(thread_messages),
            "incoming": len(incoming),
            "attachments": attachment_count,
            "attachment_paths": thread_attachment_paths,
        })
    return records


def write_private_index(records: list[dict], messages: list[dict], aliases: dict[str, str]) -> None:
    today = dt.date.today().isoformat()
    lines = [
        "---",
        "title: Private Fanmail Index",
        "type: private-map",
        "private: true",
        "tags: [private, correspondence, fanmail]",
        f"created: {today}",
        f"updated: {today}",
        "---",
        "",
        "# Private Fanmail Index",
        "",
        f"- Source files: {len(list(SOURCE.glob('*.eml')))}",
        f"- Unique messages: {len(messages)}",
        f"- Threads: {len(records)}",
        f"- Outside correspondents: {len(aliases)}",
        f"- Unique attachments: {len({a['digest'] for m in messages for a in m['attachments']})}",
        "",
        "Compiled notes pseudonymize correspondents and redact addresses and phone numbers. Original EML files remain in the private originals folder.",
        "",
        "## Threads",
        "",
    ]
    for record in records:
        relative = record["path"].relative_to(PRIVATE).as_posix()
        lines.append(
            f"- [{record['title']}]({relative}) - {record['category']}; "
            f"{record['messages']} messages; {record['attachments']} attachments"
        )
    (PRIVATE / "Private Fanmail Index.md").write_text("\n".join(lines) + "\n")


def write_reception_map(records: list[dict], messages: list[dict]) -> None:
    today = dt.date.today().isoformat()
    incoming = [m for m in messages if m["direction"] == "incoming"]
    counts = Counter(category(m["subject"], m["body"], len(m["attachments"])) for m in incoming)
    body = f"""---
title: Map - Audience Correspondence
type: map
tags: [map, audience, correspondence, archive, community]
created: {today}
updated: {today}
---

# Map - Audience Correspondence

An aggregate view of correspondence received around strauh.al and computerdrawing.club from August 2025 through March 2026. Personal identities and private details are intentionally excluded.

## Corpus

- 72 EML files
- {len(messages)} unique messages after deduplication
- {len(records)} threads
- {len(incoming)} unique incoming messages
- {sum(record['attachments'] for record in records)} drawing attachments

## Kinds of Contact

- Drawing submissions: {counts['drawing-submission']}
- Site feedback and corrections: {counts['site-feedback']}
- Audience responses: {counts['audience-response']}
- Private correspondence: {counts['private-correspondence']}
- Other brief messages: {counts['other']}

## What Readers Recognized

- The archive feels handmade, pre-platform, and resistant to the polished sameness of the contemporary web.
- Several readers understood it as a view into another person's mind rather than a conventional portfolio.
- The old non-linear arrangement mattered: historical art beside science fiction and vernacular imagery produced useful surprise.
- The site prompted people not only to look, but to draw, email, suggest repairs, and imagine making archives of their own.
- 4chan advertisements completed a loop between communities that supplied images and the archive assembled from them.
- Raw materials such as sketches, notebooks, drafts, and diaries were valued as direct traces of creative thought.

## Participation

- [[Map - Drawing Submissions]] - works sent for computerdrawing.club or the archive.
- [[Map - Site Feedback]] - broken links, naming requests, and design reactions.
- [[strauh.al Archive]] - the work that generated the correspondence.
- [[The Internet as Confidant]] - correspondence turns the internet from abstract audience into actual relationship.
- [[Memory and Preservation]] - the fanmail itself becomes another archive layer.

## Privacy

Full messages, pseudonymized thread notes, and attachments are stored under `knowledge/private/fanmail/`. This map deliberately avoids names, addresses, phone numbers, and intimate personal disclosures.
"""
    MAPS.mkdir(parents=True, exist_ok=True)
    (MAPS / "Map - Audience Correspondence.md").write_text(body)


def write_filtered_map(
    records: list[dict],
    map_name: str,
    categories: set[str],
    intro: str,
    gallery: bool = False,
) -> None:
    today = dt.date.today().isoformat()
    selected = [record for record in records if record["category"] in categories]
    lines = [
        "---",
        f"title: Map - {map_name}",
        "type: map",
        "tags: [map, audience, correspondence]",
        f"created: {today}",
        f"updated: {today}",
        "---",
        "",
        f"# Map - {map_name}",
        "",
        intro,
        "",
        f"Threads: {len(selected)}",
        "",
    ]
    for record in selected:
        relative = Path(os.path.relpath(record["path"], MAPS)).as_posix()
        lines.append(
            f"- [{record['title']}]({relative}) - "
            f"{record['incoming']} incoming messages; {record['attachments']} attachments"
        )
        if gallery:
            for attachment in record["attachment_paths"]:
                attachment_relative = attachment.relative_to(VAULT).as_posix()
                lines.append(f"  ![[{attachment_relative}|240]]")
    (MAPS / f"Map - {map_name}.md").write_text("\n".join(lines) + "\n")


def update_existing_notes() -> None:
    archive = VAULT / "knowledge" / "wiki" / "works" / "strauh.al Archive.md"
    internet = VAULT / "knowledge" / "wiki" / "concepts" / "The Internet as Confidant.md"
    for path, line in [
        (archive, "- [[Map - Audience Correspondence]] — readers, drawing submissions, and maintenance feedback generated by the archive."),
        (internet, "- [[Map - Audience Correspondence]] — the abstract online audience becoming concrete correspondents and collaborators."),
    ]:
        text = path.read_text(errors="ignore")
        if line not in text:
            marker = "## Sources"
            text = text.replace(marker, line + "\n\n" + marker)
            path.write_text(text)


def update_registry() -> None:
    path = RAW / "_sources.md"
    text = path.read_text(errors="ignore")
    if "| fanmail-2025-2026 |" not in text:
        text = text.rstrip() + f"\n| fanmail-2025-2026 | correspondence | {dt.date.today().isoformat()} | true |\n"
        path.write_text(text)


def write_report(messages: list[dict], records: list[dict], aliases: dict[str, str]) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    report = (
        "# Fanmail Import Report\n\n"
        f"Generated: {dt.datetime.now().isoformat(timespec='seconds')}\n\n"
        f"- EML source files: {len(list(SOURCE.glob('*.eml')))}\n"
        f"- Unique messages: {len(messages)}\n"
        f"- Threads: {len(records)}\n"
        f"- Outside correspondents: {len(aliases)}\n"
        f"- Unique attachments: {len({a['digest'] for m in messages for a in m['attachments']})}\n"
        "- No source files deleted.\n"
    )
    (OUTPUT / "fanmail-import-report.md").write_text(report)


def main() -> None:
    if not SOURCE.exists():
        print("Fanmail source folder not found; skipped.")
        return
    PRIVATE.mkdir(parents=True, exist_ok=True)
    messages = parse_messages()
    aliases = correspondent_aliases(messages)
    preserve_originals(messages)
    attachment_paths = preserve_attachments(messages)
    records = write_threads(messages, aliases, attachment_paths)
    write_private_index(records, messages, aliases)
    write_reception_map(records, messages)
    write_filtered_map(
        records,
        "Drawing Submissions",
        {"drawing-submission"},
        "Private correspondence threads containing drawings or submissions sent in response to strauh.al and computerdrawing.club.",
        gallery=True,
    )
    write_filtered_map(
        records,
        "Site Feedback",
        {"site-feedback"},
        "Reader reports about broken links, naming, navigation, and archive arrangement.",
    )
    update_existing_notes()
    update_registry()
    write_report(messages, records, aliases)
    print(f"Integrated {len(messages)} unique messages across {len(records)} threads.")


if __name__ == "__main__":
    main()
