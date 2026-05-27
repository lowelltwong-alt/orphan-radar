from __future__ import annotations

import networkx as nx
from sklearn.metrics.pairwise import cosine_similarity

from orphan_radar.core.models import NoteRecord, OrphanRecord
from orphan_radar.core.settings import RadarSettings


def meaningful_tags(note: NoteRecord, settings: RadarSettings) -> set[str]:
    return {t for t in note.tags if t not in settings.generic_terms and t not in settings.ignore_tags}


def is_excluded(note: NoteRecord, settings: RadarSettings) -> bool:
    if note.is_generated_output:
        return True
    if set(note.folder_path.split('/')) & settings.excluded_folders:
        return True
    if note.tags & settings.ignore_tags:
        return True
    if note.metadata.get('orphan_radar', '').lower() == 'ignore':
        return True
    return False


def compute_local_coherence(note_id: str, graph: nx.DiGraph, tfidf_matrix) -> float:
    if note_id not in graph:
        return 0.0
    idx = graph.nodes[note_id]['index']
    neighbors = list(graph.predecessors(note_id)) + list(graph.successors(note_id))
    if not neighbors:
        return 0.0
    vals = []
    for n in neighbors:
        vals.append(float(cosine_similarity(tfidf_matrix[idx], tfidf_matrix[graph.nodes[n]['index']])[0, 0]))
    return sum(vals) / len(vals) if vals else 0.0


def has_only_generic_links(note: NoteRecord, graph: nx.DiGraph, settings: RadarSettings) -> bool:
    linked = note.resolved_links | note.backlinks
    if not linked:
        return False
    for target in linked:
        title_tokens = graph.nodes[target].get('title_tokens', []) if target in graph else []
        if any(t not in settings.generic_terms for t in title_tokens):
            return False
    return True


def classify_note(note: NoteRecord, graph: nx.DiGraph, tfidf_matrix, settings: RadarSettings) -> OrphanRecord:
    outgoing = graph.out_degree(note.note_id) if note.note_id in graph else 0
    incoming = graph.in_degree(note.note_id) if note.note_id in graph else 0
    local_coherence = compute_local_coherence(note.note_id, graph, tfidf_matrix)
    reasons: list[str] = []

    if is_excluded(note, settings):
        reasons.append('ignored by generated-output, folder, tag, or metadata rule')
        orphan_type = 'intentional'
    elif outgoing == 0 and incoming == 0:
        reasons.extend(['no outgoing links', 'no backlinks'])
        orphan_type = 'hard'
    elif (
        outgoing <= settings.weak_edge_threshold
        and incoming <= settings.weak_edge_threshold
        and (len(meaningful_tags(note, settings)) == 0 or local_coherence < settings.weak_orphan_coherence_threshold)
    ) or has_only_generic_links(note, graph, settings):
        reasons.append('few meaningful graph connections')
        if len(meaningful_tags(note, settings)) == 0:
            reasons.append('no meaningful tags')
        if local_coherence < settings.weak_orphan_coherence_threshold:
            reasons.append('low coherence with current neighbors')
        orphan_type = 'weak'
    else:
        orphan_type = 'connected'

    return OrphanRecord(
        node_id=note.note_id,
        orphan_type=orphan_type,  # type: ignore[arg-type]
        existing_edge_count=outgoing + incoming,
        outgoing_count=outgoing,
        backlink_count=incoming,
        local_coherence=local_coherence,
        reasons=reasons,
    )


def classify_notes(notes: list[NoteRecord], graph: nx.DiGraph, tfidf_matrix, settings: RadarSettings) -> list[OrphanRecord]:
    return [classify_note(note, graph, tfidf_matrix, settings) for note in notes]
