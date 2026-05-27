from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import networkx as nx

from orphan_radar.core.models import NoteRecord
from orphan_radar.core.settings import RadarSettings
from orphan_radar.graph.build_graph import add_pagerank, build_link_graph
from orphan_radar.graph.communities import (
    build_community_centroids,
    build_hybrid_graph,
    build_tfidf,
    detect_communities,
)


@dataclass
class GraphWorld:
    """The full set of derived structures the ranker needs.

    Built once and shared by ``run_scan`` and the link-reconstruction eval so the
    eval measures the *real* ranking pipeline rather than a parallel copy.
    """

    notes: list[NoteRecord]
    notes_by_id: dict[str, NoteRecord]
    note_index: dict[str, int]
    link_graph: nx.DiGraph
    vectorizer: Any
    tfidf_matrix: Any
    hybrid_graph: nx.Graph
    communities: dict[int, list[str]]
    node_to_community: dict[str, int]
    centroids: dict[int, Any]


def build_world(notes: list[NoteRecord], settings: RadarSettings) -> GraphWorld:
    notes_by_id = {note.note_id: note for note in notes}
    note_index = {note.note_id: idx for idx, note in enumerate(notes)}

    link_graph = build_link_graph(notes)
    add_pagerank(link_graph)
    vectorizer, tfidf_matrix = build_tfidf(notes)
    hybrid_graph = build_hybrid_graph(link_graph, tfidf_matrix, settings)
    add_pagerank(hybrid_graph)
    communities, node_to_community = detect_communities(hybrid_graph, tfidf_matrix)
    centroids = build_community_centroids(communities, tfidf_matrix, note_index)

    return GraphWorld(
        notes=notes,
        notes_by_id=notes_by_id,
        note_index=note_index,
        link_graph=link_graph,
        vectorizer=vectorizer,
        tfidf_matrix=tfidf_matrix,
        hybrid_graph=hybrid_graph,
        communities=communities,
        node_to_community=node_to_community,
        centroids=centroids,
    )
