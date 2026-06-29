#!/usr/bin/env python3
"""Health-check the second-brain wiki. Zero dependencies.

Scope: validates the CURATED tiers (wiki/people, wiki/concepts, wiki/works) plus the
root hubs, where the strict frontmatter/link conventions apply. Wikilinks are resolved
against the ENTIRE vault (so curated links to the automated archive tier resolve).

Checks: broken [[links]], frontmatter validity, orphans, duplicate titles,
uncompiled sources. Writes knowledge/output/lint-report.md and prints a summary.

Usage:
  python3 scripts/wiki_lint.py
  python3 scripts/wiki_lint.py --fix   # add missing ISO `updated` dates
"""
import argparse
import datetime
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WIKI = os.path.join(ROOT, "knowledge", "wiki")
RAW = os.path.join(ROOT, "knowledge", "raw")
CURATED = [os.path.join(WIKI, d) for d in ("people", "concepts", "works")]
ROOT_HUBS = [os.path.join(WIKI, "Image Archive.md")]
INDEX = os.path.join(WIKI, "_index.md")
OUT = os.path.join(ROOT, "knowledge", "output", "lint-report.md")
REQUIRED = ["title", "type", "created", "updated", "sources"]
LINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")


def fm_block(text):
    m = re.search(r"^---\n(.*?)\n---\n", text, re.S)
    return m.group(1) if m else ""


def fm_get(fm, key):
    m = re.search(rf"^{key}:\s*(.+)$", fm, re.M)
    return m.group(1).strip() if m else None


def curated_files():
    for base in CURATED:
        if not os.path.isdir(base):
            continue
        for n in sorted(os.listdir(base)):
            if n.endswith(".md") and not n.startswith("_"):
                yield os.path.join(base, n)
    for p in ROOT_HUBS:
        if os.path.exists(p):
            yield p


def all_vault_targets():
    """Every linkable name in the vault: basenames + aliases (lowercased)."""
    targets = set()
    scan = [WIKI, RAW]
    for base in scan:
        for dp, _, files in os.walk(base):
            for n in files:
                if not n.endswith(".md"):
                    continue
                targets.add(os.path.splitext(n)[0].lower())
                with open(os.path.join(dp, n), encoding="utf-8", errors="replace") as f:
                    fm = fm_block(f.read())
                al = fm_get(fm, "aliases") or ""
                for a in re.findall(r"[^,\[\]]+", al.strip("[] ")):
                    a = a.strip().strip('"').strip("'")
                    if a:
                        targets.add(a.lower())
    for n in os.listdir(ROOT):
        if n.endswith(".md"):
            targets.add(os.path.splitext(n)[0].lower())
    return targets


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fix", action="store_true")
    args = ap.parse_args()
    today = datetime.date.today().isoformat()

    data, dup, missing_fm = {}, [], []
    seen_titles = {}
    for path in curated_files():
        with open(path, encoding="utf-8", errors="replace") as f:
            text = f.read()
        fm = fm_block(text)
        body = text[text.find("---", 3) + 4:] if fm else text
        title = fm_get(fm, "title") or os.path.splitext(os.path.basename(path))[0]
        data[path] = (title, fm, body)
        key = title.lower()
        if key in seen_titles:
            dup.append((title, seen_titles[key], path))
        seen_titles[key] = path
        miss = [k for k in REQUIRED if not fm_get(fm, k)]
        if miss:
            missing_fm.append((os.path.relpath(path, ROOT), miss))

    targets = all_vault_targets()

    broken, inbound = [], {p: 0 for p in data}
    curated_by_name = {t.lower(): p for p, (t, _, _) in data.items()}
    for path, (title, fm, body) in data.items():
        for tgt in LINK_RE.findall(body):
            k = tgt.strip().lower()
            if k not in targets:
                broken.append((os.path.relpath(path, ROOT), tgt.strip()))
            if k in curated_by_name:
                inbound[curated_by_name[k]] += 1

    index_text = open(INDEX, encoding="utf-8", errors="replace").read() if os.path.exists(INDEX) else ""
    indexed = {x.lower() for x in LINK_RE.findall(index_text)}
    orphans = [
        os.path.relpath(p, ROOT)
        for p, (t, _, _) in data.items()
        if inbound.get(p, 0) == 0 and t.lower() not in indexed
    ]

    uncompiled = []
    if os.path.isdir(RAW):
        for n in sorted(os.listdir(RAW)):
            if n.endswith(".md") and not n.startswith("_"):
                with open(os.path.join(RAW, n), encoding="utf-8", errors="replace") as f:
                    if re.search(r"^compiled:\s*false\s*$", f.read(), re.M):
                        uncompiled.append(n)

    fixed = 0
    if args.fix:
        for path, (title, fm, body) in data.items():
            if not fm_get(fm, "updated"):
                t = open(path, encoding="utf-8").read().replace("\n---\n", f"\nupdated: {today}\n---\n", 1)
                open(path, "w", encoding="utf-8").write(t)
                fixed += 1

    def section(title, items, fmt):
        if not items:
            return f"## {title}\n\n✓ clean\n\n"
        return f"## {title}\n\n" + "".join(f"- {fmt(i)}\n" for i in items) + "\n"

    rep = [f"# wiki-lint report — {today}\n",
           f"_Scope: {len(data)} curated notes (people/concepts/works + hubs). "
           f"Links resolved against the full vault._\n"]
    rep.append(section("Broken links", broken, lambda x: f"`{x[0]}` → `[[{x[1]}]]`"))
    rep.append(section("Missing frontmatter", missing_fm, lambda x: f"`{x[0]}` missing: {', '.join(x[1])}"))
    rep.append(section("Orphan pages", orphans, lambda x: f"`{x}`"))
    rep.append(section("Duplicate titles", dup, lambda x: f"'{x[0]}' in two files"))
    rep.append(section("Uncompiled sources", uncompiled, lambda x: f"`{x}` (run wiki-compile)"))
    total = len(broken) + len(missing_fm) + len(orphans) + len(dup)
    rep.append(f"**{total} issues across 5 checks ({fixed} auto-fixed). {len(data)} curated notes.**\n")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write("\n".join(rep))
    print("\n".join(rep))
    print(f"report → {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
