from __future__ import annotations

import re
from pathlib import Path

WIKI_LINK_RE = re.compile(r"(?<!!)\[\[([^\]]+)\]\]")
MD_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def normalize_link_target(raw: str) -> str:
    target = raw.strip()
    if '|' in target:
        target = target.split('|', 1)[0]
    if '#' in target:
        target = target.split('#', 1)[0]
    target = target.strip().strip('/')
    if target.lower().endswith('.md') or target.lower().endswith('.txt'):
        target = target.rsplit('.', 1)[0]
    return target.strip()


def normalize_title_key(value: str) -> str:
    value = Path(value).stem if any(sep in value for sep in ['/', '\\']) else value
    return re.sub(r"\s+", " ", value.strip().lower())


def extract_wiki_links(content: str) -> set[str]:
    links = set()
    for match in WIKI_LINK_RE.findall(content or ''):
        target = normalize_link_target(match)
        if target:
            links.add(target)
    return links


def extract_markdown_file_links(content: str) -> set[str]:
    links = set()
    for match in MD_LINK_RE.findall(content or ''):
        if match.startswith(('http://', 'https://', 'mailto:')):
            continue
        suffix = Path(match).suffix.lower()
        if suffix in {'.md', '.txt'}:
            target = normalize_link_target(match)
            if target:
                links.add(target)
    return links
