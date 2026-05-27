from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal


OrphanType = Literal['hard', 'weak', 'intentional', 'connected']
CandidateType = Literal['direct', 'bridge', 'calibration']
ReviewTrack = Literal['cleanup', 'structural_gap', 'bridge', 'calibration']


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def to_dict(obj: Any) -> dict[str, Any]:
    return asdict(obj)


@dataclass
class NoteRecord:
    note_id: str
    filepath: str
    relpath: str
    title: str
    content: str
    search_text: str
    file_hash: str
    folder_path: str
    outbound_links: set[str] = field(default_factory=set)
    resolved_links: set[str] = field(default_factory=set)
    unresolved_links: set[str] = field(default_factory=set)
    backlinks: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    metadata: dict[str, str] = field(default_factory=dict)
    title_tokens: list[str] = field(default_factory=list)
    content_tokens: list[str] = field(default_factory=list)
    word_count: int = 0
    is_generated_output: bool = False


@dataclass
class OrphanRecord:
    node_id: str
    orphan_type: OrphanType
    assigned_communities: list[int] = field(default_factory=list)
    community_scores: dict[int, float] = field(default_factory=dict)
    existing_edge_count: int = 0
    outgoing_count: int = 0
    backlink_count: int = 0
    local_coherence: float = 0.0
    bridge_candidate: bool = False
    reasons: list[str] = field(default_factory=list)


@dataclass
class EvidencePacket:
    evidence_packet_id: str
    candidate_edge_id: str
    source_id: str
    target_id: str
    shared_terms: list[str]
    shared_tags: list[str]
    route: list[str]
    metrics: dict[str, float]
    explanation: str


@dataclass
class CandidateEdge:
    candidate_edge_id: str
    source_id: str
    target_id: str
    score: float
    rank: int
    target_community_id: int | None
    candidate_type: CandidateType
    confidence_label: str
    reasons: list[str]
    metrics: dict[str, float]
    evidence_id: str | None = None


@dataclass
class BridgeCandidate:
    bridge_candidate_id: str
    orphan_id: str
    communities: list[int]
    bridge_score: float
    suggested_bridge_label: str
    suggested_targets: list[str]
    evidence: list[str]


@dataclass
class ReviewQueueItem:
    item_id: str
    track: ReviewTrack
    priority_score: float
    source_id: str
    target_id: str | None
    source_title: str
    target_title: str | None
    explanation: str
    payload: dict[str, Any]


@dataclass
class RunSummary:
    generated_at: str
    source_dir: str
    output_dir: str
    total_notes_scanned: int
    hard_orphans_found: int
    weak_orphans_found: int
    bridge_candidates_found: int
    candidate_edges_generated: int
    review_items_generated: int
    source_files_mutated: bool
    execution_time_seconds: float
