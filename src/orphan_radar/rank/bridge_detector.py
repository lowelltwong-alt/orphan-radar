from __future__ import annotations

from statistics import harmonic_mean
import networkx as nx

from orphan_radar.core.models import BridgeCandidate, NoteRecord
from orphan_radar.core.settings import RadarSettings
from orphan_radar.graph.hub_penalty import clamp
from orphan_radar.parse.tokens import overlap_terms


def intercommunity_density(c1: int, c2: int, communities: dict[int, list[str]], graph: nx.Graph) -> float:
    a = communities.get(c1, [])
    b = communities.get(c2, [])
    if not a or not b:
        return 1.0
    possible = len(a) * len(b)
    edges = 0
    for u in a:
        for v in b:
            if graph.has_edge(u, v):
                edges += 1
    return edges / possible if possible else 1.0


def note_specificity(note: NoteRecord) -> float:
    if not note.content_tokens:
        return 0.0
    unique = len(set(note.content_tokens))
    return clamp(unique / max(len(note.content_tokens), 1))


def suggest_bridge_label(note: NoteRecord) -> str:
    label = note.title
    for prefix in ('Orphan - ', 'Orphan Note - ', 'Orphan: '):
        if label.startswith(prefix):
            label = label[len(prefix):]
    return label.strip() or note.title


def best_target_in_community(orphan: NoteRecord, community_id: int, communities: dict[int, list[str]], notes_by_id: dict[str, NoteRecord]) -> str | None:
    best_id = None
    best_overlap = -1
    for node_id in communities.get(community_id, []):
        if node_id == orphan.note_id:
            continue
        note = notes_by_id[node_id]
        overlap = len(set(orphan.content_tokens + orphan.title_tokens) & set(note.content_tokens + note.title_tokens))
        if overlap > best_overlap:
            best_overlap = overlap
            best_id = node_id
    return best_id


def detect_bridge_candidate(
    orphan: NoteRecord,
    community_scores: dict[int, float],
    communities: dict[int, list[str]],
    graph: nx.Graph,
    notes_by_id: dict[str, NoteRecord],
    settings: RadarSettings,
) -> BridgeCandidate | None:
    ranked = sorted(community_scores.items(), key=lambda x: x[1], reverse=True)
    if len(ranked) < 2:
        return None
    c1, s1 = ranked[0]
    c2, s2 = ranked[1]
    if s1 < settings.bridge_min_community_score or s2 < settings.bridge_min_community_score:
        return None
    if abs(s1 - s2) > settings.bridge_max_score_gap:
        return None
    density = intercommunity_density(c1, c2, communities, graph)
    if density > settings.bridge_max_intercommunity_density:
        return None
    separation = 1 - density
    specificity = note_specificity(orphan)
    balance = 1 - abs(s1 - s2)
    score = harmonic_mean([max(s1, 1e-9), max(s2, 1e-9)]) * separation * specificity * balance
    if score < settings.bridge_min_score:
        return None
    t1 = best_target_in_community(orphan, c1, communities, notes_by_id)
    t2 = best_target_in_community(orphan, c2, communities, notes_by_id)
    suggested_targets = [x for x in [t1, t2] if x]
    shared = []
    for tid in suggested_targets:
        shared.extend(overlap_terms(orphan.content_tokens, notes_by_id[tid].content_tokens, limit=5))
    bridge_id = f"bridge_{abs(hash((orphan.note_id, c1, c2))) % 10**10}"
    return BridgeCandidate(
        bridge_candidate_id=bridge_id,
        orphan_id=orphan.note_id,
        communities=[c1, c2],
        bridge_score=clamp(score),
        suggested_bridge_label=suggest_bridge_label(orphan),
        suggested_targets=suggested_targets,
        evidence=[
            f'affinity to community {c1}: {s1:.3f}',
            f'affinity to community {c2}: {s2:.3f}',
            f'intercommunity density: {density:.3f}',
            'shared bridge terms: ' + ', '.join(sorted(set(shared))[:8]) if shared else 'balanced cross-community signal',
        ],
    )
