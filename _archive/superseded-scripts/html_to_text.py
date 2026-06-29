#!/usr/bin/env python3
"""Extract readable text from a strauh.al HTML page.

Keeps headings, paragraphs, line breaks, list items and embedded hrefs; drops
<style>/<script>/<head> chrome. Zero dependencies (stdlib HTMLParser).

Usage: python3 scripts/html_to_text.py path/to/page.html
"""
import sys
from html.parser import HTMLParser
from html import unescape


BLOCK = {"p", "div", "br", "h1", "h2", "h3", "h4", "li", "tr", "blockquote", "section"}
SKIP = {"style", "script"}  # containers whose inner text we drop (they have close tags)


class Extractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.skip_depth = 0
        self.in_body = False  # ignore everything in <head>

    def handle_starttag(self, tag, attrs):
        if tag == "body":
            self.in_body = True
        if tag in SKIP:
            self.skip_depth += 1
        if not self.in_body or self.skip_depth:
            return
        if tag in BLOCK:
            self.out.append("\n")
        if tag == "a":
            href = dict(attrs).get("href", "")
            if href and not href.startswith("#"):
                self.out.append(f" {href} ")

    def handle_endtag(self, tag):
        if tag in SKIP and self.skip_depth:
            self.skip_depth -= 1
        if self.in_body and not self.skip_depth and tag in BLOCK:
            self.out.append("\n")

    def handle_comment(self, data):
        # strauh.al stores some real content inside HTML comments; keep text-only ones.
        if not self.in_body:
            return
        inner = data.strip()
        if inner and "<" not in inner and ">" not in inner:
            self.out.append("\n" + inner + "\n")

    def handle_data(self, data):
        if not self.in_body or self.skip_depth:
            return
        text = data.strip()
        if text:
            self.out.append(text + " ")


def extract(html: str) -> str:
    p = Extractor()
    p.feed(html)
    raw = unescape("".join(p.out))
    lines = [ln.strip() for ln in raw.splitlines()]
    cleaned, blank = [], 0
    for ln in lines:
        if not ln:
            blank += 1
            if blank <= 1:
                cleaned.append("")
        else:
            blank = 0
            cleaned.append(ln)
    return "\n".join(cleaned).strip() + "\n"


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    with open(sys.argv[1], encoding="utf-8", errors="replace") as f:
        sys.stdout.write(extract(f.read()))


if __name__ == "__main__":
    main()
