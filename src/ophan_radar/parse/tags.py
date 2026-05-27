from __future__ import annotations

import re

INLINE_TAG_RE = re.compile(r"(?<!\w)#([A-Za-z][A-Za-z0-9_\-/]*)")


def parse_frontmatter(content: str) -> tuple[dict[str, str], str]:
    if not content.startswith('---'):
        return {}, content
    parts = content.split('---', 2)
    if len(parts) < 3:
        return {}, content
    raw = parts[1]
    body = parts[2]
    metadata: dict[str, str] = {}
    for line in raw.splitlines():
        if ':' not in line:
            continue
        key, value = line.split(':', 1)
        metadata[key.strip().lower()] = value.strip()
    return metadata, body.lstrip()


def _split_tag_value(value: str) -> set[str]:
    value = value.strip()
    if value.startswith('[') and value.endswith(']'):
        value = value[1:-1]
    return {x.strip().strip('#').lower() for x in re.split(r"[,\s]+", value) if x.strip()}


def extract_tags(content: str, metadata: dict[str, str] | None = None) -> set[str]:
    tags = {m.group(1).lower() for m in INLINE_TAG_RE.finditer(content or '')}
    metadata = metadata or {}
    for key in ('tag', 'tags'):
        if key in metadata:
            tags |= _split_tag_value(metadata[key])
    return {t for t in tags if t}
