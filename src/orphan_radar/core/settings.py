from __future__ import annotations

import json
import warnings
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import ClassVar


class ConfigValidationError(ValueError):
    """Raised when a settings value is outside its allowed range."""


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

    # (field_name, inclusive_min, inclusive_max). Fields not listed are unconstrained.
    _BOUNDS: ClassVar[dict[str, tuple[float, float]]] = {
        'title_similarity': (0.0, 1.0), 'content_similarity': (0.0, 1.0),
        'tag_similarity': (0.0, 1.0), 'folder_proximity': (0.0, 1.0),
        'local_authority': (0.0, 1.0), 'specificity': (0.0, 1.0),
        'route_coherence': (0.0, 1.0), 'hub_penalty': (0.0, 1.0),
        'similarity_edge_threshold': (0.0, 1.0), 'implicit_edge_weight': (0.0, 5.0),
        'explicit_edge_weight': (0.0, 5.0), 'weak_orphan_coherence_threshold': (0.0, 1.0),
        'min_candidate_score': (0.0, 1.0), 'strong_candidate_threshold': (0.0, 1.0),
        'acceptance_boundary': (0.0, 1.0), 'boundary_window': (0.0, 1.0),
        'bridge_min_community_score': (0.0, 1.0), 'bridge_max_score_gap': (0.0, 1.0),
        'bridge_min_score': (0.0, 1.0), 'bridge_max_intercommunity_density': (0.0, 1.0),
        'similarity_top_k': (1, 1000), 'weak_edge_threshold': (0, 1000),
        'max_suggestions_per_orphan': (1, 1000), 'min_evidence_signals': (0, 100),
        'queue_size': (1, 100000), 'entropy_min_nodes': (1, 1000000),
        'min_word_count_for_full_score': (0, 100000),
    }

    def validate(self) -> 'RadarSettings':
        """Check numeric fields are within sane ranges; raise on violation."""
        int_fields = {f.name for f in fields(self) if f.type in ('int', int)}
        for name, (low, high) in self._BOUNDS.items():
            value = getattr(self, name)
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise ConfigValidationError(f"'{name}' must be numeric, got {value!r}.")
            if name in int_fields and not float(value).is_integer():
                raise ConfigValidationError(f"'{name}' must be an integer, got {value!r}.")
            if not (low <= value <= high):
                raise ConfigValidationError(
                    f"'{name}' must be in [{low}, {high}], got {value!r}."
                )
        return self

    @classmethod
    def from_json_file(cls, path: str | Path | None) -> 'RadarSettings':
        if path is None:
            return cls()
        data = json.loads(Path(path).read_text(encoding='utf-8'))
        known = {f.name for f in fields(cls)}
        unknown = sorted(set(data) - known)
        if unknown:
            warnings.warn(
                f"Ignoring unknown config keys: {', '.join(unknown)}",
                stacklevel=2,
            )
        settings = cls()
        for key, value in data.items():
            if key in known:
                setattr(settings, key, value)
        return settings.validate()
