from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from math import log, log1p
import networkx as nx
import numpy as np

from orphan_radar.core.models import NoteRecord
from orphan_radar.core.settings import RadarSettings


@dataclass
class HubMetrics:
    authority: float
    title_specificity: float
    content_specificity: float
    specificity: float
    neighbor_entropy: float
    generic_label_score: float
    genericness: float
    hub_penalty: float


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def normalized_entropy(values: list[int]) -> float:
    if not values:
        return 0.0
    counts = Counter(values)
    total = sum(counts.values())
    if len(counts) <= 1:
        return 0.0
    entropy = 0.0
    for count in counts.values():
        p = count / total
        entropy -= p * log(p)
    return clamp(entropy / log(len(counts)))


def generic_label_score(tokens: list[str], generic_terms: set[str]) -> float:
    if not tokens:
        return 1.0
    generic = sum(1 for t in tokens if t in generic_terms)
    ratio = generic / len(tokens)
    if ratio >= 0.75:
        return 1.0
    if ratio > 0:
        return 0.5
    return 0.0


def mean_normalized_idf(tokens: list[str], vectorizer) -> float:
    if not tokens or vectorizer is None:
        return 0.0
    vocab = vectorizer.vocabulary_
    idfs = vectorizer.idf_
    max_idf = float(np.max(idfs)) if len(idfs) else 1.0
    vals = [float(idfs[vocab[t]]) / max_idf for t in tokens if t in vocab]
    if not vals:
        return 0.0
    return clamp(sum(vals) / len(vals))


def mean_top_k_tfidf(note_index: int, tfidf_matrix, k: int = 10) -> float:
    row = tfidf_matrix[note_index]
    data = row.data
    if data.size == 0:
        return 0.0
    top = np.sort(data)[-k:]
    # TF-IDF weights are usually <= 1.0 after L2 normalization.
    return clamp(float(np.mean(top)))


def compute_hub_metrics(
    node_id: str,
    graph: nx.Graph,
    notes_by_id: dict[str, NoteRecord],
    tfidf_matrix,
    vectorizer,
    node_to_community: dict[str, int],
    settings: RadarSettings,
) -> HubMetrics:
    note = notes_by_id[node_id]
    degrees = dict(graph.degree())
    max_degree = max(degrees.values()) if degrees else 0
    degree_norm = log1p(degrees.get(node_id, 0)) / log1p(max_degree) if max_degree else 0.0

    pageranks = [float(graph.nodes[n].get('pagerank', 0.0)) for n in graph.nodes]
    max_pagerank = max(pageranks) if pageranks else 0.0
    pagerank_norm = float(graph.nodes[node_id].get('pagerank', 0.0)) / max_pagerank if max_pagerank else 0.0
    authority = clamp(0.5 * degree_norm + 0.5 * pagerank_norm)

    title_specificity = mean_normalized_idf(note.title_tokens, vectorizer)
    note_index = graph.nodes[node_id].get('index', 0)
    content_specificity = mean_top_k_tfidf(note_index, tfidf_matrix, k=10)
    specificity = clamp(0.65 * title_specificity + 0.35 * content_specificity)

    if graph.number_of_nodes() < settings.entropy_min_nodes:
        neighbor_entropy = 0.0
    else:
        neighbor_comms = [node_to_community[n] for n in graph.neighbors(node_id) if n in node_to_community]
        neighbor_entropy = normalized_entropy(neighbor_comms)

    label_score = generic_label_score(note.title_tokens, settings.generic_terms)
    genericness = clamp(
        0.40 * (1 - title_specificity)
        + 0.25 * (1 - content_specificity)
        + 0.25 * neighbor_entropy
        + 0.10 * label_score
    )
    hub_penalty = clamp(authority * genericness)
    return HubMetrics(
        authority=authority,
        title_specificity=title_specificity,
        content_specificity=content_specificity,
        specificity=specificity,
        neighbor_entropy=neighbor_entropy,
        generic_label_score=label_score,
        genericness=genericness,
        hub_penalty=hub_penalty,
    )
