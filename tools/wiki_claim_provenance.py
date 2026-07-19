#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import re
from pathlib import Path


VAULT = Path(__file__).resolve().parents[1]
WIKI = VAULT / "knowledge" / "wiki"
OUTPUT = VAULT / "knowledge" / "output"
START = "<!-- claim:start -->"
END = "<!-- claim:end -->"
REQUIRED = (
    "Source type",
    "Claim date",
    "Confidence",
    "Evidence",
    "Contradictions",
    "Retrospective editing",
    "Derivation",
)
ALLOWED_CONFIDENCE = {"high", "moderate", "low"}


def frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        return ""
    end = text.find("\n---\n", 4)
    return text[4:end] if end != -1 else ""


def uses_schema(text: str) -> bool:
    return bool(re.search(r'^claim_schema:\s*["\']?1["\']?\s*$', frontmatter(text), re.M))


def field(block: str, name: str) -> str:
    match = re.search(rf"^- \*\*{re.escape(name)}:\*\*\s*(.+)$", block, re.M)
    return match.group(1).strip() if match else ""


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    files = []
    claims = 0
    errors: list[str] = []

    for path in sorted(WIKI.rglob("*.md")):
        text = path.read_text(errors="ignore")
        if not uses_schema(text):
            continue
        files.append(path)
        blocks = re.findall(
            rf"^{re.escape(START)}\s*$(.*?)^{re.escape(END)}\s*$",
            text,
            flags=re.S | re.M,
        )
        relative = path.relative_to(VAULT).as_posix()
        if not blocks:
            errors.append(f"`{relative}`: schema enabled but no claim blocks found")
            continue
        for index, block in enumerate(blocks, 1):
            claims += 1
            for name in REQUIRED:
                if not field(block, name):
                    errors.append(f"`{relative}` claim {index}: missing {name}")
            date = field(block, "Claim date")
            try:
                dt.date.fromisoformat(date)
            except ValueError:
                errors.append(f"`{relative}` claim {index}: invalid Claim date `{date}`")
            confidence = field(block, "Confidence").lower()
            if confidence not in ALLOWED_CONFIDENCE:
                errors.append(
                    f"`{relative}` claim {index}: Confidence must be high, moderate, or low"
                )

    report = "# Claim Provenance Report\n\n"
    report += f"Generated: {dt.datetime.now().isoformat(timespec='seconds')}\n\n"
    report += "## Summary\n\n"
    report += f"- Schema-enabled notes: {len(files)}\n"
    report += f"- Claims checked: {claims}\n"
    report += f"- Provenance errors: {len(errors)}\n\n"
    report += "## Errors\n\n"
    report += "\n".join(f"- {error}" for error in errors) or "- None"
    report += "\n"
    (OUTPUT / "claim-provenance-report.md").write_text(report)
    print(report)
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
