from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json


@dataclass
class RadarSettings:
    title_similarity: float = 0.25
    content_similarity: float = 0.25
    tag_similarity: float = 0.15
    folder_proximity: float = 0.08
    local_authority: float = 0.10
    specificity: float = 0.12
    route_coherence: float = 0.10
    hub_penalty: float = 0.10

    similarity_edge_threshold: float = 0.22
    similarity_top_k: int = 5
    implicit_edge_weight: float = 0.35
    explicit_edge_weight: float = 1.0

    weak_edge_threshold: int = 2
    weak_orphan_coherence_threshold: float = 0.12
    min_candidate_score: float = 0.18
    max_suggestions_per_orphan: int = 5
    min_evidence_signals: int = 1
    strong_candidate_threshold: float = 0.65
    acceptance_boundary: float = 0.45
    boundary_window: float = 0.15
    queue_size: int = 30

    bridge_min_community_score: float = 0.12
    bridge_max_score_gap: float = 0.25
    bridge_min_score: float = 0.06
    bridge_max_intercommunity_density: float = 0.35

    entropy_min_nodes: int = 30
    min_word_count_for_full_score: int = 50

    excluded_folders: set[str] = field(default_factory=lambda: {
        '.git', '.obsidian', '__pycache__', 'orphan_radar_output', 'radar_output'
    })
    ignore_tags: set[str] = field(default_factory=lambda: {'orphan-radar-ignore', 'no-radar'})
    generic_terms: set[str] = field(default_factory=lambda: {
        'ai', 'research', 'strategy', 'ideas', 'notes', 'misc', 'knowledge',
        'innovation', 'projects', 'writing', 'todo', 'archive', 'index', 'inbox',
        'dashboard', 'home', 'general', 'meeting', 'meetings'
    })

    @classmethod
    def from_json_file(cls, path: str | Path | None) -> 'RadarSettings':
        if path is None:
            return cls()
        data = json.loads(Path(path).read_text(encoding='utf-8'))
        settings = cls()
        for key, value in data.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        return settings
