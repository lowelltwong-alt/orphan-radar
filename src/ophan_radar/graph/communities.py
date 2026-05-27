from __future__ import annotations

from math import sqrt
import networkx as nx
import numpy as np
from scipy import sparse
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from orphan_radar.core.models import NoteRecord
from orphan_radar.core.settings import RadarSettings


def build_tfidf(notes: list[NoteRecord]):
    texts = [note.search_text or note.title for note in notes]
    if not texts:
        texts = ['empty']
    vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2), min_df=1, max_df=0.95)
    matrix = vectorizer.fit_transform(texts)
    return vectorizer, matrix


def build_hybrid_graph(link_graph: nx.DiGraph, tfidf_matrix, settings: RadarSettings) -> nx.Graph:
    hybrid = nx.Graph()
    for node, attrs in link_graph.nodes(data=True):
        hybrid.add_node(node, **attrs)
    for u, v, attrs in link_graph.edges(data=True):
        hybrid.add_edge(u, v, weight=settings.explicit_edge_weight, edge_type=attrs.get('edge_type', 'explicit'))

    nodes = list(link_graph.nodes)
    if len(nodes) <= 1:
        return hybrid

    sims = cosine_similarity(tfidf_matrix)
    for i, u in enumerate(nodes):
        row = [(j, float(sims[i, j])) for j in range(len(nodes)) if j != i]
        row.sort(key=lambda x: x[1], reverse=True)
        added = 0
        for j, sim in row:
            if sim < settings.similarity_edge_threshold or added >= settings.similarity_top_k:
                break
            v = nodes[j]
            if hybrid.has_edge(u, v):
                continue
            hybrid.add_edge(u, v, weight=settings.implicit_edge_weight * sim, edge_type='similarity')
            added += 1
    return hybrid


def detect_communities(hybrid_graph: nx.Graph, tfidf_matrix=None) -> tuple[dict[int, list[str]], dict[str, int]]:
    nodes = list(hybrid_graph.nodes)
    n = len(nodes)
    if n == 0:
        return {}, {}
    if n == 1:
        return {0: nodes}, {nodes[0]: 0}

    communities_sets = None
    if hybrid_graph.number_of_edges() > 0:
        try:
            communities_sets = list(nx.algorithms.community.louvain_communities(hybrid_graph, weight='weight', seed=42))
        except Exception:
            try:
                communities_sets = list(nx.algorithms.community.greedy_modularity_communities(hybrid_graph, weight='weight'))
            except Exception:
                communities_sets = None

    if not communities_sets or len(communities_sets) == 1 and n >= 8 and tfidf_matrix is not None:
        k = max(2, min(n, int(sqrt(n))))
        labels = KMeans(n_clusters=k, random_state=42, n_init='auto').fit_predict(tfidf_matrix)
        communities: dict[int, list[str]] = {cid: [] for cid in sorted(set(labels))}
        for node, label in zip(nodes, labels):
            communities[int(label)].append(node)
    else:
        communities = {i: sorted(list(c)) for i, c in enumerate(communities_sets)}

    node_to_community: dict[str, int] = {}
    for cid, members in communities.items():
        for node in members:
            node_to_community[node] = cid
            hybrid_graph.nodes[node]['community_id'] = cid
    return communities, node_to_community


def build_community_centroids(communities: dict[int, list[str]], tfidf_matrix, note_index: dict[str, int]):
    centroids = {}
    for cid, members in communities.items():
        indices = [note_index[m] for m in members if m in note_index]
        if not indices:
            continue
        sub = tfidf_matrix[indices]
        centroids[cid] = sub.mean(axis=0)
    return centroids
