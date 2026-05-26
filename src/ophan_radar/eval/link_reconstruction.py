from __future__ import annotations

import random
import re
from dataclasses import dataclass
import networkx as nx

from orphan_radar.core.models import NoteRecord


@dataclass
class LinkReconstructionEval:
    eligible_edges: int
    hidden_edges: int
    recall_at_1: float = 0.0
    recall_at_3: float = 0.0
    recall_at_5: float = 0.0
    mean_reciprocal_rank: float = 0.0
    low_confidence_reason: str | None = None


def select_eligible_edges(graph: nx.DiGraph) -> list[tuple[str, str]]:
    edges = []
    for u, v in graph.edges:
        u_title = graph.nodes[u].get('title', '').lower()
        v_title = graph.nodes[v].get('title', '').lower()
        if 'orphan radar review' in u_title or 'orphan radar review' in v_title:
            continue
        edges.append((u, v))
    return edges


def sample_holdout_edges(edges: list[tuple[str, str]], ratio: float = 0.10, seed: int = 42) -> list[tuple[str, str]]:
    if not edges:
        return []
    rng = random.Random(seed)
    k = max(1, int(len(edges) * ratio))
    return rng.sample(edges, min(k, len(edges)))


def mask_hidden_link_text(note: NoteRecord, target_title: str) -> NoteRecord:
    # Remove direct wiki mentions of the hidden target to prevent leakage.
    escaped = re.escape(target_title)
    content = re.sub(r"\[\[" + escaped + r"(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]", "[hidden-link]", note.content, flags=re.IGNORECASE)
    content = re.sub(escaped, "hidden target", content, flags=re.IGNORECASE)
    clone = NoteRecord(**{**note.__dict__, 'content': content, 'search_text': f"{note.title}\n{content}"})
    return clone


def make_eval_summary(graph: nx.DiGraph, holdout_ratio: float = 0.10) -> LinkReconstructionEval:
    eligible = select_eligible_edges(graph)
    hidden = sample_holdout_edges(eligible, ratio=holdout_ratio)
    if len(eligible) < 3:
        return LinkReconstructionEval(
            eligible_edges=len(eligible),
            hidden_edges=len(hidden),
            low_confidence_reason='Too few eligible links for meaningful reconstruction eval.'
        )
    return LinkReconstructionEval(eligible_edges=len(eligible), hidden_edges=len(hidden))
