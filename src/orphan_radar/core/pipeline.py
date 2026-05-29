from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import time

from orphan_radar.core.models import RunSummary, utc_now
from orphan_radar.core.settings import RadarSettings
from orphan_radar.core.world import build_world
from orphan_radar.eval.link_reconstruction import calibrate_weights, make_eval_summary
from orphan_radar.graph.build_graph import build_link_graph
from orphan_radar.graph.communities import build_tfidf
from orphan_radar.ingest.loader import load_notes
from orphan_radar.io.hasher import assert_no_source_mutation, hash_sources
from orphan_radar.io.jsonl import write_json, write_jsonl
from orphan_radar.io.output_writer import OutputWriter
from orphan_radar.rank.bridge_detector import detect_bridge_candidate
from orphan_radar.rank.candidate_ranker import collect_candidates, passes_quality_gate, score_candidate
from orphan_radar.rank.community_router import score_note_to_communities, select_candidate_communities
from orphan_radar.rank.orphan_classifier import classify_notes
from orphan_radar.rank.review_queue_ranker import build_review_queue
from orphan_radar.review.report_writer import render_review_report


def run_scan(source_dir: Path, output_dir: Path, settings: RadarSettings | None = None, *, allow_output_inside_source: bool = False) -> RunSummary:
    started = time.time()
    settings = settings or RadarSettings()
    source_dir = source_dir.resolve()
    output_dir = output_dir.resolve()
    writer = OutputWriter(source_dir, output_dir, allow_inside_source=allow_output_inside_source)

    notes, source_files = load_notes(source_dir, settings)
    initial_hashes = hash_sources(source_files)

    world = build_world(notes, settings)
    notes_by_id = world.notes_by_id
    note_index = world.note_index
    link_graph = world.link_graph
    vectorizer = world.vectorizer
    tfidf_matrix = world.tfidf_matrix
    hybrid_graph = world.hybrid_graph
    communities = world.communities
    node_to_community = world.node_to_community
    centroids = world.centroids

    orphan_records = classify_notes(notes, link_graph, tfidf_matrix, settings)
    reviewable_orphans = [o for o in orphan_records if o.orphan_type in {'hard', 'weak'}]

    candidate_edges = []
    evidence_packets = []
    bridge_candidates = []

    for orphan_record in reviewable_orphans:
        note = notes_by_id[orphan_record.node_id]
        community_scores = score_note_to_communities(note, communities, centroids, tfidf_matrix, note_index, notes_by_id, settings)
        orphan_record.community_scores = community_scores
        orphan_record.assigned_communities = select_candidate_communities(community_scores, top_k=3)

        bridge = detect_bridge_candidate(note, community_scores, communities, hybrid_graph, notes_by_id, settings)
        if bridge:
            orphan_record.bridge_candidate = True
            bridge_candidates.append(bridge)

        candidates = collect_candidates(note, orphan_record.assigned_communities, communities, notes_by_id)
        scored = []
        for target in candidates:
            cid = node_to_community.get(target.note_id)
            edge, evidence = score_candidate(
                note, target, cid, communities, hybrid_graph, notes_by_id, tfidf_matrix,
                vectorizer, node_to_community, settings, community_scores=community_scores
            )
            if passes_quality_gate(edge, evidence, settings):
                scored.append((edge, evidence))
        scored.sort(key=lambda x: x[0].score, reverse=True)
        for rank, (edge, evidence) in enumerate(scored[:settings.max_suggestions_per_orphan], 1):
            edge.rank = rank
            candidate_edges.append(edge)
            evidence_packets.append(evidence)

    review_queue = build_review_queue(candidate_edges, bridge_candidates, notes_by_id, reviewable_orphans, settings)
    summary = RunSummary(
        generated_at=utc_now(),
        source_dir=str(source_dir),
        output_dir=str(output_dir),
        total_notes_scanned=len(notes),
        hard_orphans_found=sum(1 for o in orphan_records if o.orphan_type == 'hard'),
        weak_orphans_found=sum(1 for o in orphan_records if o.orphan_type == 'weak'),
        bridge_candidates_found=len(bridge_candidates),
        candidate_edges_generated=len(candidate_edges),
        review_items_generated=len(review_queue),
        source_files_mutated=False,
        execution_time_seconds=round(time.time() - started, 4),
    )

    # Outputs only, via writer.
    write_json(writer.path('graph.json'), {
        'nodes': [dict(id=n, **hybrid_graph.nodes[n]) for n in hybrid_graph.nodes],
        'edges': [{'source': u, 'target': v, **attrs} for u, v, attrs in hybrid_graph.edges(data=True)]
    })
    write_json(writer.path('communities.json'), {'communities': communities, 'node_to_community': node_to_community})
    write_jsonl(writer.path('orphan_notes.jsonl'), reviewable_orphans)
    write_jsonl(writer.path('candidate_edges.jsonl'), candidate_edges)
    write_jsonl(writer.path('bridge_candidates.jsonl'), bridge_candidates)
    write_jsonl(writer.path('evidence_packets.jsonl'), evidence_packets)
    writer.write_text('review_report.md', render_review_report(review_queue, summary))
    write_json(writer.path('run_summary.json'), summary)

    final_hashes = hash_sources(source_files)
    assert_no_source_mutation(initial_hashes, final_hashes)
    return summary


def run_status(source_dir: Path, settings: RadarSettings | None = None) -> dict:
    settings = settings or RadarSettings()
    notes, source_files = load_notes(source_dir.resolve(), settings)
    link_graph = build_link_graph(notes)
    vectorizer, tfidf_matrix = build_tfidf(notes)
    orphans = classify_notes(notes, link_graph, tfidf_matrix, settings)
    return {
        'source_dir': str(source_dir.resolve()),
        'files': len(source_files),
        'notes': len(notes),
        'links': link_graph.number_of_edges(),
        'hard_orphans': sum(1 for o in orphans if o.orphan_type == 'hard'),
        'weak_orphans': sum(1 for o in orphans if o.orphan_type == 'weak'),
    }


def run_eval(
    source_dir: Path,
    output_dir: Path,
    settings: RadarSettings | None = None,
    *,
    holdout_ratio: float = 0.10,
    calibrate: bool = False,
    trials: int = 40,
) -> dict:
    settings = settings or RadarSettings()
    notes, source_files = load_notes(source_dir.resolve(), settings)
    writer = OutputWriter(source_dir.resolve(), output_dir.resolve())

    result = make_eval_summary(notes, settings, holdout_ratio=holdout_ratio)
    payload: dict = {'link_reconstruction': asdict(result)}

    if calibrate:
        calibration = calibrate_weights(notes, settings, holdout_ratio=holdout_ratio, trials=trials)
        payload['calibration'] = asdict(calibration)

    write_json(writer.path('eval_report.json'), payload)
    return payload
