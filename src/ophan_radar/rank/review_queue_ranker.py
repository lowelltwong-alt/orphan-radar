from __future__ import annotations

from orphan_radar.core.models import BridgeCandidate, CandidateEdge, NoteRecord, OrphanRecord, ReviewQueueItem
from orphan_radar.core.settings import RadarSettings


def uncertainty(score: float, settings: RadarSettings) -> float:
    return 1 - min(1.0, abs(score - settings.acceptance_boundary) / max(settings.boundary_window, 1e-9))


def impact(edge: CandidateEdge, orphans: dict[str, OrphanRecord]) -> float:
    orphan = orphans.get(edge.source_id)
    orphan_priority = 1.0 if orphan and orphan.orphan_type == 'hard' else 0.75
    return 0.35 * orphan_priority + 0.35 * edge.metrics.get('specificity', 0.0) + 0.30 * edge.metrics.get('local_authority', 0.0)


def edge_queue_score(edge: CandidateEdge, orphans: dict[str, OrphanRecord], settings: RadarSettings) -> float:
    quick_win = edge.score * max(0.2, 1 - edge.metrics.get('hub_penalty', 0.0))
    learning = uncertainty(edge.score, settings) * impact(edge, orphans)
    return 0.45 * quick_win + 0.35 * learning + 0.20 * impact(edge, orphans)


def take(items: list, n: int):
    return items[:max(0, n)]


def build_review_queue(
    candidate_edges: list[CandidateEdge],
    bridge_candidates: list[BridgeCandidate],
    notes_by_id: dict[str, NoteRecord],
    orphan_records: list[OrphanRecord],
    settings: RadarSettings,
) -> list[ReviewQueueItem]:
    orphans = {o.node_id: o for o in orphan_records}
    strong = sorted([e for e in candidate_edges if e.score >= settings.strong_candidate_threshold], key=lambda e: e.score, reverse=True)
    boundary = sorted(candidate_edges, key=lambda e: uncertainty(e.score, settings) * impact(e, orphans), reverse=True)
    other = sorted(candidate_edges, key=lambda e: edge_queue_score(e, orphans, settings), reverse=True)

    quota = settings.queue_size
    selected: list[CandidateEdge] = []
    selected.extend(take(strong, int(quota * 0.40)))
    selected_ids = {e.candidate_edge_id for e in selected}
    selected.extend([e for e in take(boundary, int(quota * 0.30) + 5) if e.candidate_edge_id not in selected_ids][:int(quota * 0.30)])
    selected_ids = {e.candidate_edge_id for e in selected}
    selected.extend([e for e in other if e.candidate_edge_id not in selected_ids][:max(0, quota - len(selected))])

    items: list[ReviewQueueItem] = []
    for edge in selected:
        orphan = orphans.get(edge.source_id)
        track = 'cleanup' if orphan and orphan.orphan_type == 'hard' else 'structural_gap'
        src = notes_by_id[edge.source_id]
        tgt = notes_by_id[edge.target_id]
        items.append(ReviewQueueItem(
            item_id=edge.candidate_edge_id,
            track=track,  # type: ignore[arg-type]
            priority_score=edge_queue_score(edge, orphans, settings),
            source_id=edge.source_id,
            target_id=edge.target_id,
            source_title=src.title,
            target_title=tgt.title,
            explanation='; '.join(edge.reasons),
            payload={'score': edge.score, 'confidence': edge.confidence_label, 'candidate_type': edge.candidate_type},
        ))

    # Cap bridge items; mark them separately.
    for bridge in sorted(bridge_candidates, key=lambda b: b.bridge_score, reverse=True)[:max(1, int(quota * 0.20))]:
        src = notes_by_id[bridge.orphan_id]
        items.append(ReviewQueueItem(
            item_id=bridge.bridge_candidate_id,
            track='bridge',
            priority_score=bridge.bridge_score,
            source_id=bridge.orphan_id,
            target_id=None,
            source_title=src.title,
            target_title=None,
            explanation=f"May bridge communities {bridge.communities}; suggested bridge node: {bridge.suggested_bridge_label}",
            payload={'suggested_targets': bridge.suggested_targets, 'evidence': bridge.evidence},
        ))

    items.sort(key=lambda x: x.priority_score, reverse=True)
    return items[:quota]
