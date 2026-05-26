from __future__ import annotations

from collections import defaultdict
import networkx as nx

from orphan_radar.core.models import NoteRecord
from orphan_radar.parse.links import normalize_title_key


def resolve_links(notes: list[NoteRecord]) -> None:
    by_key: dict[str, list[str]] = defaultdict(list)
    for note in notes:
        keys = {normalize_title_key(note.title), normalize_title_key(note.note_id)}
        stem = normalize_title_key(note.relpath.rsplit('/', 1)[-1].rsplit('.', 1)[0])
        keys.add(stem)
        for key in keys:
            by_key[key].append(note.note_id)

    for note in notes:
        resolved: set[str] = set()
        unresolved: set[str] = set()
        for raw in note.outbound_links:
            key = normalize_title_key(raw)
            matches = sorted(set(by_key.get(key, [])))
            if len(matches) == 1 and matches[0] != note.note_id:
                resolved.add(matches[0])
            else:
                unresolved.add(raw)
        note.resolved_links = resolved
        note.unresolved_links = unresolved

    backlinks: dict[str, set[str]] = {note.note_id: set() for note in notes}
    for note in notes:
        for target in note.resolved_links:
            backlinks.setdefault(target, set()).add(note.note_id)
    for note in notes:
        note.backlinks = backlinks.get(note.note_id, set())


def build_link_graph(notes: list[NoteRecord]) -> nx.DiGraph:
    resolve_links(notes)
    graph = nx.DiGraph()
    for idx, note in enumerate(notes):
        graph.add_node(
            note.note_id,
            index=idx,
            title=note.title,
            relpath=note.relpath,
            folder_path=note.folder_path,
            tags=sorted(note.tags),
            title_tokens=note.title_tokens,
            content_tokens=note.content_tokens,
            word_count=note.word_count,
            is_generated_output=note.is_generated_output,
        )
    for note in notes:
        for target in note.resolved_links:
            graph.add_edge(note.note_id, target, weight=1.0, edge_type='explicit')
    return graph


def add_pagerank(graph: nx.Graph) -> None:
    if graph.number_of_nodes() == 0:
        return
    try:
        ranks = nx.pagerank(graph, weight='weight')
    except Exception:
        uniform = 1.0 / max(1, graph.number_of_nodes())
        ranks = {node: uniform for node in graph.nodes}
    for node, value in ranks.items():
        graph.nodes[node]['pagerank'] = float(value)
