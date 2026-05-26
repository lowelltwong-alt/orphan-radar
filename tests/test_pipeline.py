from pathlib import Path
import json

from orphan_radar.core.pipeline import run_scan, run_status, run_eval
from orphan_radar.core.settings import RadarSettings
from orphan_radar.io.hasher import hash_sources
from orphan_radar.ingest.loader import scan_source_files


def test_end_to_end_pipeline_execution_produces_outputs(tmp_path: Path):
    src = tmp_path / 'notes'
    out = tmp_path / 'out'
    src.mkdir()
    (src / 'Agent Reliability.md').write_text('# Agent Reliability\nTesting timeout memory reliability. [[Testing Strategy]]', encoding='utf-8')
    (src / 'Testing Strategy.md').write_text('# Testing Strategy\nLong running test timeout defaults. [[Agent Reliability]]', encoding='utf-8')
    (src / 'Orphan Timeout.md').write_text('# Orphan Timeout\nAgent needs timeout memory for long running tests.', encoding='utf-8')
    settings = RadarSettings()
    files = scan_source_files(src, settings)
    before = hash_sources(files)
    summary = run_scan(src, out, settings)
    after = hash_sources(files)
    assert before == after
    assert summary.total_notes_scanned == 3
    assert (out / 'review_report.md').exists()
    assert (out / 'candidate_edges.jsonl').exists()
    assert json.loads((out / 'run_summary.json').read_text())['source_files_mutated'] is False


def test_status_and_eval(tmp_path: Path):
    src = tmp_path / 'notes'
    out = tmp_path / 'eval'
    src.mkdir()
    (src / 'A.md').write_text('# A\nSee [[B]]', encoding='utf-8')
    (src / 'B.md').write_text('# B\nContent', encoding='utf-8')
    status = run_status(src)
    assert status['notes'] == 2
    report = run_eval(src, out)
    assert 'eligible_edges' in report
    assert (out / 'eval_report.json').exists()
