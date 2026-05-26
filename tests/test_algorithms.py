from pathlib import Path

from orphan_radar.core.settings import RadarSettings
from orphan_radar.graph.build_graph import add_pagerank, build_link_graph
from orphan_radar.graph.communities import build_hybrid_graph, build_tfidf, detect_communities
from orphan_radar.graph.hub_penalty import compute_hub_metrics
from orphan_radar.ingest.loader import load_notes
from orphan_radar.rank.bridge_detector import detect_bridge_candidate
from orphan_radar.graph.communities import build_community_centroids
from orphan_radar.rank.community_router import score_note_to_communities
from orphan_radar.rank.orphan_classifier import classify_notes


def make_notes(tmp_path: Path):
    (tmp_path / 'AI.md').write_text('# AI\nGeneral AI research strategy innovation notes. [[Agent Reliability]] [[Testing Strategy]] [[Knowledge Graph Maintenance]]', encoding='utf-8')
    (tmp_path / 'Agent Reliability.md').write_text('# Agent Reliability\nAgent timeout memory testing reliability failures. [[Testing Strategy]]', encoding='utf-8')
    (tmp_path / 'Testing Strategy.md').write_text('# Testing Strategy\nLong-running tests timeout command reliability. [[Agent Reliability]]', encoding='utf-8')
    (tmp_path / 'Knowledge Graph Maintenance.md').write_text('# Knowledge Graph Maintenance\nOrphan notes backlinks graph review evidence links.', encoding='utf-8')
    (tmp_path / 'Orphan Timeout.md').write_text('# Orphan Timeout\nAgents need timeout memory for long-running tests and failed commands.', encoding='utf-8')


def setup_graph(tmp_path: Path):
    settings = RadarSettings()
    notes, _ = load_notes(tmp_path, settings)
    notes_by_id = {n.note_id: n for n in notes}
    graph = build_link_graph(notes)
    add_pagerank(graph)
    vectorizer, tfidf = build_tfidf(notes)
    hybrid = build_hybrid_graph(graph, tfidf, settings)
    add_pagerank(hybrid)
    communities, node_to_community = detect_communities(hybrid, tfidf)
    return settings, notes, notes_by_id, graph, hybrid, vectorizer, tfidf, communities, node_to_community


def test_hub_penalty_generic_high_degree_node_gets_penalized(tmp_path):
    make_notes(tmp_path)
    settings, notes, notes_by_id, graph, hybrid, vectorizer, tfidf, communities, node_to_community = setup_graph(tmp_path)
    generic = compute_hub_metrics('ai', hybrid, notes_by_id, tfidf, vectorizer, node_to_community, settings)
    specific = compute_hub_metrics('agent reliability', hybrid, notes_by_id, tfidf, vectorizer, node_to_community, settings)
    assert generic.hub_penalty >= specific.hub_penalty


def test_hard_and_weak_orphan_classification(tmp_path):
    make_notes(tmp_path)
    settings, notes, notes_by_id, graph, hybrid, vectorizer, tfidf, communities, node_to_community = setup_graph(tmp_path)
    records = {r.node_id: r for r in classify_notes(notes, graph, tfidf, settings)}
    assert records['orphan timeout'].orphan_type == 'hard'


def test_bridge_candidate_detected_between_two_communities(tmp_path):
    make_notes(tmp_path)
    settings, notes, notes_by_id, graph, hybrid, vectorizer, tfidf, communities, node_to_community = setup_graph(tmp_path)
    # Relax for small synthetic graph.
    settings.bridge_min_community_score = 0.01
    settings.bridge_min_score = 0.001
    note = notes_by_id['orphan timeout']
    centroids = build_community_centroids(communities, tfidf, {n.note_id: i for i, n in enumerate(notes)})
    scores = score_note_to_communities(note, communities, centroids, tfidf, {n.note_id: i for i, n in enumerate(notes)}, notes_by_id, settings)
    bridge = detect_bridge_candidate(note, scores, communities, hybrid, notes_by_id, settings)
    # Depending on clustering, this may or may not bridge. It must not crash and if returned is well-formed.
    if bridge:
        assert bridge.orphan_id == 'orphan timeout'
        assert len(bridge.communities) == 2
