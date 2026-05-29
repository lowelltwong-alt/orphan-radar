from __future__ import annotations

import random
import re
from dataclasses import dataclass, replace

import networkx as nx

from orphan_radar.core.models import NoteRecord
from orphan_radar.core.settings import RadarSettings
from orphan_radar.core.world import build_world
from orphan_radar.parse.links import normalize_title_key
from orphan_radar.rank.candidate_ranker import collect_candidates, score_candidate
from orphan_radar.rank.community_router import (
    score_note_to_communities,
    select_candidate_communities,
)

# Weight fields that participate in the linear candidate score. These are exactly
# the additive terms in ``score_candidate``; calibration searches over them.
WEIGHT_FIELDS = (
    'title_similarity',
    'content_similarity',
    'tag_similarity',
    'folder_proximity',
    'local_authority',
    'specificity',
    'route_coherence',
    'information_gain',
    'hub_penalty',
)


@dataclass
class LinkReconstructionEval:
    eligible_edges: int
    hidden_edges: int
    scored_edges: int = 0
    recall_at_1: float = 0.0
    recall_at_3: float = 0.0
    recall_at_5: float = 0.0
    mean_reciprocal_rank: float = 0.0
    low_confidence_reason: str | None = None


@dataclass
class CalibrationResult:
    baseline: LinkReconstructionEval
    best: LinkReconstructionEval
    baseline_weights: dict[str, float]
    best_weights: dict[str, float]
    trials: int
    objective: str = 'recall_at_5'
    improved: bool = False
    note: str | None = None


# --------------------------------------------------------------------------- #
# Eligible-edge selection and holdout sampling
# --------------------------------------------------------------------------- #

def select_eligible_edges(graph: nx.DiGraph) -> list[tuple[str, str]]:
    """Resolved explicit links, excluding generated review output on either end."""
    edges: list[tuple[str, str]] = []
    for u, v in graph.edges:
        if graph.nodes[u].get('is_generated_output') or graph.nodes[v].get('is_generated_output'):
            continue
        u_title = graph.nodes[u].get('title', '').lower()
        v_title = graph.nodes[v].get('title', '').lower()
        if 'orphan radar review' in u_title or 'orphan radar review' in v_title:
            continue
        edges.append((u, v))
    return edges


def sample_holdout_edges(edges: list[tuple[str, str]], ratio: float = 0.10, seed: int = 42) -> list[tuple[str, str]]:
    if not edges:
        return []
    rng = random.Random(seed)
    k = max(1, int(len(edges) * ratio))
    return rng.sample(edges, min(k, len(edges)))


# --------------------------------------------------------------------------- #
# Leakage masking
# --------------------------------------------------------------------------- #

def mask_hidden_link_text(note: NoteRecord, target_title: str) -> NoteRecord:
    """Aggressively remove any mention of the hidden target (wiki link or prose).

    Kept for the strict leakage test. The eval itself uses
    :func:`strip_link_markup`, which removes only explicit link *syntax* so that
    legitimate topical word overlap (the signal we are testing) is preserved.
    """
    escaped = re.escape(target_title)
    content = re.sub(r"\[\[" + escaped + r"(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]", "[hidden-link]", note.content, flags=re.IGNORECASE)
    content = re.sub(escaped, "hidden target", content, flags=re.IGNORECASE)
    return replace(note, content=content, search_text=f"{note.title}\n{content}")


def strip_link_markup(note: NoteRecord, target_titles: set[str]) -> NoteRecord:
    """Remove explicit ``[[Target]]`` / ``[txt](Target.md)`` markup for held-out targets.

    Topical prose is left intact on purpose: the proxy task asks whether the
    ranker can *rediscover* a removed link from content/structure, not whether it
    can read the answer key.
    """
    content = note.content
    for title in target_titles:
        esc = re.escape(title)
        content = re.sub(r"\[\[\s*" + esc + r"\s*(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]", " ", content, flags=re.IGNORECASE)
        content = re.sub(r"\[[^\]]+\]\(\s*" + esc + r"(?:\.md|\.txt)?\s*\)", " ", content, flags=re.IGNORECASE)
    if content == note.content:
        return note
    return replace(note, content=content, search_text=f"{note.title}\n{' '.join(sorted(note.tags))}\n{content}")


def _masked_corpus(notes: list[NoteRecord], hidden: list[tuple[str, str]]) -> list[NoteRecord]:
    """Return a copy of ``notes`` with held-out edges removed from links + markup.

    The held-out target is dropped from each source note's resolved/outbound links
    so structural signals (backlinks, pagerank, community co-membership) do not
    already encode the answer, and the link markup is stripped from the text.
    """
    targets_by_source: dict[str, set[str]] = {}
    title_by_id = {n.note_id: n.title for n in notes}
    for u, v in hidden:
        targets_by_source.setdefault(u, set()).add(v)

    rebuilt: list[NoteRecord] = []
    for note in notes:
        hidden_targets = targets_by_source.get(note.note_id)
        if not hidden_targets:
            rebuilt.append(note)
            continue
        target_titles = {title_by_id.get(t, t) for t in hidden_targets}
        clone = strip_link_markup(note, target_titles)
        # Drop the resolved/outbound link so the link graph no longer contains it.
        clone = replace(
            clone,
            outbound_links={
                link for link in clone.outbound_links
                if normalize_title_key(link) not in {normalize_title_key(t) for t in target_titles}
            },
            resolved_links=set(),
            unresolved_links=set(),
            backlinks=set(),
        )
        rebuilt.append(clone)
    return rebuilt


# --------------------------------------------------------------------------- #
# The actual reconstruction measurement
# --------------------------------------------------------------------------- #

def _rank_of_target(
    source_id: str,
    target_id: str,
    world,
    settings: RadarSettings,
) -> int | None:
    """1-based rank of ``target_id`` among scored candidates for ``source_id``.

    Returns ``None`` if the target was never produced as a candidate.
    """
    note = world.notes_by_id.get(source_id)
    if note is None:
        return None
    community_scores = score_note_to_communities(
        note, world.communities, world.centroids, world.tfidf_matrix,
        world.note_index, world.notes_by_id, settings,
    )
    candidate_cids = select_candidate_communities(community_scores, top_k=3)
    candidates = collect_candidates(note, candidate_cids, world.communities, world.notes_by_id)
    if all(c.note_id != target_id for c in candidates):
        # Target lives outside the routed communities; fall back to whole-corpus
        # ranking so a routing miss still counts as a (low) rank rather than None.
        candidates = [n for n in world.notes if n.note_id != source_id and not n.is_generated_output]

    scored: list[tuple[float, str]] = []
    for target in candidates:
        cid = world.node_to_community.get(target.note_id)
        edge, _ = score_candidate(
            note, target, cid, world.communities, world.hybrid_graph,
            world.notes_by_id, world.tfidf_matrix, world.vectorizer,
            world.node_to_community, settings, community_scores=community_scores,
        )
        scored.append((edge.score, target.note_id))
    scored.sort(key=lambda x: (-x[0], x[1]))
    for rank, (_, nid) in enumerate(scored, 1):
        if nid == target_id:
            return rank
    return None


def evaluate_weights(
    notes: list[NoteRecord],
    hidden: list[tuple[str, str]],
    settings: RadarSettings,
    eligible_count: int,
) -> LinkReconstructionEval:
    """Run link reconstruction for a given settings/weight vector."""
    masked = _masked_corpus(notes, hidden)
    world = build_world(masked, settings)

    ranks: list[int | None] = []
    for source_id, target_id in hidden:
        if target_id not in world.notes_by_id or source_id not in world.notes_by_id:
            continue
        ranks.append(_rank_of_target(source_id, target_id, world, settings))

    scored = len(ranks)
    if scored == 0:
        return LinkReconstructionEval(
            eligible_edges=eligible_count, hidden_edges=len(hidden), scored_edges=0,
            low_confidence_reason='No held-out edges were scorable after masking.',
        )

    def recall_at(k: int) -> float:
        hit = sum(1 for r in ranks if r is not None and r <= k)
        return round(hit / scored, 4)

    mrr = round(sum((1.0 / r) for r in ranks if r is not None) / scored, 4)
    return LinkReconstructionEval(
        eligible_edges=eligible_count,
        hidden_edges=len(hidden),
        scored_edges=scored,
        recall_at_1=recall_at(1),
        recall_at_3=recall_at(3),
        recall_at_5=recall_at(5),
        mean_reciprocal_rank=mrr,
    )


def make_eval_summary(
    notes: list[NoteRecord],
    settings: RadarSettings | None = None,
    holdout_ratio: float = 0.10,
    seed: int = 42,
) -> LinkReconstructionEval:
    settings = settings or RadarSettings()
    from orphan_radar.graph.build_graph import build_link_graph
    graph = build_link_graph(list(notes))
    eligible = select_eligible_edges(graph)
    if len(eligible) < 3:
        return LinkReconstructionEval(
            eligible_edges=len(eligible),
            hidden_edges=0,
            low_confidence_reason='Too few eligible links for meaningful reconstruction eval (need >= 3).',
        )
    hidden = sample_holdout_edges(eligible, ratio=holdout_ratio, seed=seed)
    return evaluate_weights(notes, hidden, settings, eligible_count=len(eligible))


# --------------------------------------------------------------------------- #
# Weight calibration (the missing half of red-team Problem 3)
# --------------------------------------------------------------------------- #

def _weights_dict(settings: RadarSettings) -> dict[str, float]:
    return {f: float(getattr(settings, f)) for f in WEIGHT_FIELDS}


def _objective_value(result: LinkReconstructionEval, objective: str) -> float:
    return float(getattr(result, objective, 0.0))


def calibrate_weights(
    notes: list[NoteRecord],
    settings: RadarSettings | None = None,
    holdout_ratio: float = 0.10,
    trials: int = 40,
    seed: int = 42,
    objective: str = 'recall_at_5',
) -> CalibrationResult:
    """Random search over the linear weight vector, maximising a proxy recall metric.

    No labelled data required: the signal comes from reconstructing held-out
    existing links. Ties on the objective are broken by MRR. Positive weights are
    sampled in [0, 0.4]; ``hub_penalty`` is treated as a subtractive term and kept
    in the same range. The result reports baseline vs best so a human decides
    whether to adopt the tuned vector.
    """
    settings = settings or RadarSettings()
    from orphan_radar.graph.build_graph import build_link_graph
    graph = build_link_graph(list(notes))
    eligible = select_eligible_edges(graph)
    if len(eligible) < 3:
        base = LinkReconstructionEval(
            eligible_edges=len(eligible), hidden_edges=0,
            low_confidence_reason='Too few eligible links to calibrate (need >= 3).',
        )
        wd = _weights_dict(settings)
        return CalibrationResult(
            baseline=base, best=base, baseline_weights=wd, best_weights=wd,
            trials=0, objective=objective, improved=False,
            note='Calibration skipped: corpus too small.',
        )

    hidden = sample_holdout_edges(eligible, ratio=holdout_ratio, seed=seed)
    baseline = evaluate_weights(notes, hidden, settings, eligible_count=len(eligible))
    baseline_weights = _weights_dict(settings)

    rng = random.Random(seed)
    best_result = baseline
    best_weights = dict(baseline_weights)

    def key(res: LinkReconstructionEval) -> tuple[float, float]:
        return (_objective_value(res, objective), res.mean_reciprocal_rank)

    for _ in range(max(0, trials)):
        trial_weights = {f: round(rng.uniform(0.0, 0.40), 3) for f in WEIGHT_FIELDS}
        trial_settings = replace(settings, **trial_weights)  # type: ignore[arg-type]
        result = evaluate_weights(notes, hidden, trial_settings, eligible_count=len(eligible))
        if key(result) > key(best_result):
            best_result = result
            best_weights = trial_weights

    improved = key(best_result) > key(baseline)
    return CalibrationResult(
        baseline=baseline,
        best=best_result,
        baseline_weights=baseline_weights,
        best_weights=best_weights,
        trials=max(0, trials),
        objective=objective,
        improved=improved,
        note=None if improved else 'No weight vector beat the baseline on this corpus.',
    )
