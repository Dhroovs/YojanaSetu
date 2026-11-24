"""Offline documentation checks. No API calls, secrets, or database mutation."""

import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import unquote, urlsplit

from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parents[2]
PARSER = MarkdownIt("commonmark").enable("table")


def slug(text):
    text = re.sub(r"<[^>]+>", "", text).lower().replace("`", "")
    return re.sub(r"[^\w\- ]", "", text).replace(" ", "-")


def headings(path):
    result, seen = set(), {}
    tokens = PARSER.parse(path.read_text(encoding="utf-8"))
    for index, token in enumerate(tokens):
        if token.type == "heading_open":
            value = slug(tokens[index + 1].content)
            count = seen.get(value, 0)
            seen[value] = count + 1
            result.add(value + (f"-{count}" if count else ""))
    return result


def check():
    paths = [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md"))]
    paths += sorted((ROOT / "presentations").glob("*.md"))
    failures, external, diagrams = [], set(), []
    links_checked = 0
    for path in paths:
        text = path.read_text(encoding="utf-8")
        tokens = PARSER.parse(text)
        targets = []
        for token in tokens:
            if token.type == "fence" and token.info.strip() == "mermaid":
                diagrams.append({"file": str(path.relative_to(ROOT)), "source": token.content})
            for child in token.children or []:
                if child.type in {"link_open", "image"}:
                    targets.append(child.attrGet("href") or child.attrGet("src"))
            if token.type in {"html_block", "inline"}:
                targets += re.findall(r'(?:src|href)="([^"]+)"', token.content)
        for target in targets:
            if not target:
                continue
            url = urlsplit(target)
            if url.scheme in {"http", "https"}:
                external.add(target)
                continue
            if url.scheme or target.startswith("//"):
                continue
            links_checked += 1
            resolved = (path.parent / unquote(url.path)).resolve() if url.path else path
            if not resolved.is_relative_to(ROOT) or not resolved.exists():
                failures.append(f"{path.relative_to(ROOT)}: missing local target {target}")
            elif url.fragment and resolved.suffix == ".md":
                if unquote(url.fragment) not in headings(resolved):
                    failures.append(f"{path.relative_to(ROOT)}: missing heading {target}")
            elif url.fragment.startswith("L") and resolved.is_file():
                match = re.fullmatch(r"L(\d+)(?:-L\d+)?", url.fragment)
                if match and int(match[1]) > len(resolved.read_text(encoding="utf-8").splitlines()):
                    failures.append(f"{path.relative_to(ROOT)}: source line outside file {target}")
    for svg in (ROOT / "docs" / "assets").rglob("*.svg"):
        ET.parse(svg)
    interview = (ROOT / "docs/INTERVIEW_GUIDE.md").read_text(encoding="utf-8")
    questions = re.findall(r"^### Q\d+\. (.+)$", interview, re.M)
    chapters = re.findall(
        r"^## Chapter \d+:", (ROOT / "docs/PROJECT_WALKTHROUGH.md").read_text(), re.M
    )
    slides = re.findall(
        r"^## Slide \d+:", (ROOT / "docs/PROJECT_PRESENTATION.md").read_text(), re.M
    )
    if len(questions) < 100 or len(questions) != len(set(questions)):
        failures.append("Interview bank must have at least100 unique questions")
    if len(chapters) != 20 or len(slides) != 22:
        failures.append("Walkthrough/presentation chapter count differs from20/22")
    report = {
        "markdown_files": len(paths),
        "local_links_checked": links_checked,
        "questions": len(questions),
        "chapters": len(chapters),
        "slides": len(slides),
        "mermaid_blocks": len(diagrams),
        "failures": failures,
        "external_urls": sorted(external),
    }
    output = ROOT / "artifacts"
    output.mkdir(exist_ok=True)
    (output / "documentation-check.json").write_text(json.dumps(report, indent=2))
    (output / "mermaid-blocks.json").write_text(json.dumps(diagrams))
    print(json.dumps({k: v for k, v in report.items() if k != "external_urls"}, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(check())
