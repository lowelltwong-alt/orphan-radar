from __future__ import annotations

import re

STOPWORDS = {
    'the','and','or','a','an','of','to','in','for','on','with','by','is','are','was','were',
    'be','this','that','it','as','from','at','into','not','no','yes','but','if','then','than',
    'note','orphan','notes','file','markdown','md'
}

TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9_\-]{1,}")


def normalize_token(token: str) -> str:
    token = token.lower().strip('-_')
    if len(token) > 4 and token.endswith('s'):
        token = token[:-1]
    return token


def tokenize(text: str, *, generic_terms: set[str] | None = None) -> list[str]:
    generic_terms = generic_terms or set()
    tokens: list[str] = []
    for raw in TOKEN_RE.findall(text or ''):
        token = normalize_token(raw)
        if len(token) < 2 or token in STOPWORDS or token in generic_terms:
            continue
        tokens.append(token)
    return tokens


def jaccard(a: set[str] | list[str], b: set[str] | list[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def overlap_terms(a: list[str], b: list[str], limit: int = 12) -> list[str]:
    seen = []
    bset = set(b)
    for term in a:
        if term in bset and term not in seen:
            seen.append(term)
        if len(seen) >= limit:
            break
    return seen
