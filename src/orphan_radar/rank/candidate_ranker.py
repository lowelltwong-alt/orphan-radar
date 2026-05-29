from __future__ import annotations

import networkx as nx
from sklearn.metrics.pairwise import cosine_similarity

from orphan_radar.core.models import CandidateEdge, EvidencePacket, NoteRecord
from orphan_radar.core.settings import RadarSettings
from orphan_radar.graph.hub_penalty import compute_hub_metrics, clamp
from orphan_radar.parse.tokens import jaccard, overlap_terms
from orphan_radar.rank.information_gain import candidate_information_gain


def confidence_label(score: float) -> str:
    if score >= 0.50:
        return 'strong'
    if score >= 0.25:
        return 'plausible'
    if score >= 0.18:
        return 'weak-reviewable'
    return 'low'


def folder_proximity(source: NoteRecord, target: NoteRecord) -> float:
    if not source.folder_path or not target.folder_path:
        return 0.0
    if source.folder_path == target.folder_path:
        return 1.0
    a = source.folder_path.split('/')
    b = target.folder_path.split('/')
    shared = 0
    for x, y in zip(a, b):
        if x == y:
            shared += 1
        else:
            break
    return shared / max(len(a), len(b), 1)


def local_authority(node_id: str, graph: nx.Graph, candidate_community: list[str]) -> float:
    if node_id not in graph:
        return 0.0
    degrees = {node: graph.degree(node) for node in candidate_community if node in graph}
    max_degree = max(degrees.values()) if degrees else 0
    degree_score = graph.degree(node_id) / max_degree if max_degree else 0.0
    pageranks = [float(graph.nodes[n].get('pagerank', 0.0)) for n in candidate_community if n in graph]
    max_pr = max(pageranks) if pageranks else 0.0
    pr_score = float(graph.nodes[node_id].get('pagerank', 0.0)) / max_pr if max_pr else 0.0
    return clamp(0.5 * degree_score + 0.5 * pr_score)


def length_regularizer(note: NoteRecord, settings: RadarSettings) -> float:
    if note.word_count >= settings.min_word_count_for_full_score:
        return 1.0
    return 0.65 + 0.35 * (note.word_count / max(settings.min_word_count_for_full_score, 1))


def score_candidate(
    source: NoteRecord,
    target: NoteRecord,
    target_community_id: int | None,
    communities: dict[int, list[str]],
    graph: nx.Graph,
    notes_by_id: dict[str, NoteRecord],
    tfidf_matrix,
    vectorizer,
    node_to_community: dict[str, int],
    settings: RadarSettings,
    rank: int = 0,
    community_scores: dict[int, float] | None = None,
) -> tuple[CandidateEdge, EvidencePacket]:
    s_idx = graph.nodes[source.note_id]['index']
    t_idx = graph.nodes[target.note_id]['index']
    title_similarity = jaccard(source.title_tokens, target.title_tokens)
    content_similarity = float(cosine_similarity(tfidf_matrix[s_idx], tfidf_matrix[t_idx])[0, 0])
    tag_similarity = jaccard(source.tags - settings.generic_terms, target.tags - settings.generic_terms)
    folder = folder_proximity(source, target)
    members = communities.get(target_community_id, list(graph.nodes)) if target_community_id is not None else list(graph.nodes)
    authority = local_authority(target.note_id, graph, members)
    hub = compute_hub_metrics(target.note_id, graph, notes_by_id, tfidf_matrix, vectorizer, node_to_community, settings)
    specificity = hub.specificity
    route_coherence = 1.0 if target_community_id is not None and node_to_community.get(target.note_id) == target_community_id else 0.0
    pre_information_signal = clamp(
        0.30 * title_similarity
        + 0.35 * content_similarity
        + 0.15 * tag_similarity
        + 0.10 * folder
        + 0.10 * specificity
    )
    information = candidate_information_gain(
        community_scores,
        target_community_id,
        pre_information_signal,
        settings.entropy_temperature,
        settings.information_gain_boost,
    )

    raw_score = (
        settings.title_similarity * title_similarity
        + settings.content_similarity * content_similarity
        + settings.tag_similarity * tag_similarity
        + settings.folder_proximity * folder
        + settings.local_authority * authority
        + settings.specificity * specificity
        + settings.route_coherence * route_coherence
        + settings.information_gain * information.information_gain
        - settings.hub_penalty * hub.hub_penalty
    )
    score = clamp(raw_score * length_regularizer(source, settings))

    shared_terms = overlap_terms(source.content_tokens + source.title_tokens, target.content_tokens + target.title_tokens)
    shared_tags = sorted((source.tags - settings.generic_terms) & (target.tags - settings.generic_terms))
    reasons = []
    if shared_terms:
        reasons.append('shared terms: ' + ', '.join(shared_terms[:8]))
    if shared_tags:
        reasons.append('shared tags: ' + ', '.join(shared_tags[:8]))
    if folder > 0:
        reasons.append('folder proximity signal')
    if authority > 0.4:
        reasons.append('target has local graph authority')
    if information.information_gain > 0.05:
        reasons.append('link reduces community assignment uncertainty')
    if hub.hub_penalty < 0.35:
        reasons.append('target is a specific authority, not a generic hub')
    else:
        reasons.append('generic hub penalty applied')

    candidate_id = f"cand_{abs(hash((source.note_id, target.note_id, target_community_id))) % 10**10}"
    evidence_id = f"ev_{abs(hash(candidate_id)) % 10**10}"
    metrics = {
        'title_similarity': title_similarity,
        'content_similarity': content_similarity,
        'tag_similarity': tag_similarity,
        'folder_proximity': folder,
        'local_authority': authority,
        'specificity': specificity,
        'route_coherence': route_coherence,
        'information_gain': information.information_gain,
        'community_entropy_before': information.entropy_before,
        'community_entropy_after': information.entropy_after,
        'candidate_entropy_boost': information.candidate_boost,
        'hub_penalty': hub.hub_penalty,
        'score': score,
    }
    edge = CandidateEdge(
        candidate_edge_id=candidate_id,
        source_id=source.note_id,
        target_id=target.note_id,
        score=score,
        rank=rank,
        target_community_id=target_community_id,
        candidate_type='direct',
        confidence_label=confidence_label(score),
        reasons=reasons,
        metrics=metrics,
        evidence_id=evidence_id,
    )
    evidence = EvidencePacket(
        evidence_packet_id=evidence_id,
        candidate_edge_id=candidate_id,
        source_id=source.note_id,
        target_id=target.note_id,
        shared_terms=shared_terms,
        shared_tags=shared_tags,
        route=[str(target_community_id) if target_community_id is not None else 'unknown', target.title],
        metrics=metrics,
        explanation='; '.join(reasons) if reasons else 'local graph/text signals passed minimum threshold',
    )
    return edge, evidence


def collect_candidates(
    source: NoteRecord,
    candidate_community_ids: list[int],
    communities: dict[int, list[str]],
    notes_by_id: dict[str, NoteRecord],
) -> list[NoteRecord]:
    ids: set[str] = set()
    for cid in candidate_community_ids:
        ids |= set(communities.get(cid, []))
    ids.discard(source.note_id)
    return [notes_by_id[i] for i in sorted(ids) if i in notes_by_id and not notes_by_id[i].is_generated_output]


def passes_quality_gate(edge: CandidateEdge, evidence: EvidencePacket, settings: RadarSettings) -> bool:
    evidence_count = int(bool(evidence.shared_terms)) + int(bool(evidence.shared_tags))
    if edge.metrics.get('folder_proximity', 0.0) > 0:
        evidence_count += 1
    return edge.score >= settings.min_candidate_score and evidence_count >= settings.min_evidence_signals
