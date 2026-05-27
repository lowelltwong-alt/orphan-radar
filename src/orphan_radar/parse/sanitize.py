from __future__ import annotations

import re

# Fenced code blocks: ``` ... ``` or ~~~ ... ~~~ (optionally with a language tag).
_FENCED_RE = re.compile(r"(^|\n)([ \t]*)(`{3,}|~{3,})[^\n]*\n.*?(?:\n[ \t]*\3[ \t]*(?=\n|$)|$)", re.DOTALL)
# Inline code spans: `code` (single backtick pairs, not spanning blank lines).
_INLINE_RE = re.compile(r"`[^`\n]+`")


def strip_code(content: str) -> str:
    """Blank out fenced and inline code so link/tag regexes don't read from code.

    Code regions are replaced with whitespace (newlines preserved for fenced
    blocks) rather than deleted, so surrounding prose keeps its line structure
    and the tag lookbehind ``(?<!\\w)`` still behaves at line starts.

    Known limitation: 4-space indented code blocks are not stripped, since doing
    so safely would require distinguishing them from indented prose/list content.
    """
    if not content:
        return content

    def _blank_fenced(match: re.Match[str]) -> str:
        lead = match.group(1)  # preserved leading newline (or empty at start)
        # Replace the body with newlines to keep line counts roughly stable.
        return lead + "\n" * match.group(0).count("\n")

    without_fenced = _FENCED_RE.sub(_blank_fenced, content)
    return _INLINE_RE.sub(lambda m: " " * len(m.group(0)), without_fenced)
