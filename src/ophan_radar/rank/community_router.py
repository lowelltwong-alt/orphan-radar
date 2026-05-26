from __future__ import annotations

from collections import Counter
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from orphan_radar.core.models import NoteRecord
from orphan_radar.core.settings import RadarSettings
from orphan_radar.parse.tokens import jaccard


def community_profile(community_nodes: list[str], notes_by_id: dict[str, NoteRecord]) -> tuple[set[str], set[str], Counter[str]]:
    tags: set[str] = set()
    title_tokens: set[str] = set()
    folders: Counter[str] = Counter()
    for node in community_nodes:
        note = notes_by_id[node]
        tags |= {t for t in note.tags}
        title_tokens |= set(note.title_tokens)
        folders[note.folder_path] += 1
    return tags, title_tokens, folders


def folder_signal(note: NoteRecord, folders: Counter[str]) -> float:
    if not folders or not note.folder_path:
        return 0.0
    if note.folder_path in folders:
        return 1.0
    # shared prefix signal for nested folders
    note_parts = note.folder_path.split('/')
    best = 0.0
    for folder in folders:
        parts = folder.split('/')
        shared = 0
        for a, b in zip(note_parts, parts):
            if a == b:
                shared += 1
            else:
                break
        best = max(best, shared / max(len(note_parts), len(parts), 1))
    return best


def score_note_to_communities(
    note: NoteRecord,
    communities: dict[int, list[str]],
    centroids: dict[int, object],
    tfidf_matrix,
    note_index: dict[str, int],
    notes_by_id: dict[str, NoteRecord],
    settings: RadarSettings,
) -> dict[int, float]:
    scores: dict[int, float] = {}
    note_vec = tfidf_matrix[note_index[note.note_id]]
    for cid, members in communities.items():
        centroid = centroids.get(cid)
        if centroid is None:
            continue
        centroid_vec = np.asarray(centroid)
        cosine = float(cosine_similarity(note_vec, centroid_vec)[0, 0])
        c_tags, c_title_tokens, c_folders = community_profile(members, notes_by_id)
        tag_overlap = jaccard(note.tags - settings.generic_terms, c_tags - settings.generic_terms)
        title_overlap = jaccard(note.title_tokens, c_title_tokens)
        folder = folder_signal(note, c_folders)
        scores[cid] = 0.55 * cosine + 0.20 * tag_overlap + 0.15 * title_overlap + 0.10 * folder
    return scores


def select_candidate_communities(scores: dict[int, float], top_k: int = 3) -> list[int]:
    if not scores:
        return []
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    primary_score = ranked[0][1]
    selected = [ranked[0][0]]
    for cid, score in ranked[1:top_k]:
        if primary_score <= 0 or score >= 0.80 * primary_score:
            selected.append(cid)
    return selected
