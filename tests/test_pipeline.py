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
    assert 'link_reconstruction' in report
    assert 'eligible_edges' in report['link_reconstruction']
    assert (out / 'eval_report.json').exists()


def test_eval_actually_reconstructs_recoverable_links(tmp_path: Path):
    """Regression guard: the eval must measure real recall, not return all-zeros.

    A small but topically separable corpus with reconstructable links should
    yield recall_at_5 > 0 once the held-out link is hidden and the ranker re-run.
    """
    src = tmp_path / 'notes'
    out = tmp_path / 'eval'
    src.mkdir()
    (src / 'Agent Reliability.md').write_text(
        '# Agent Reliability\nAgent timeout memory reliability failures retries. '
        '[[Testing Strategy]] [[Timeout Memory]]', encoding='utf-8')
    (src / 'Testing Strategy.md').write_text(
        '# Testing Strategy\nLong running tests timeout command reliability retries. '
        '[[Agent Reliability]] [[Timeout Memory]]', encoding='utf-8')
    (src / 'Timeout Memory.md').write_text(
        '# Timeout Memory\nTimeout memory retries reliability for long running agent tests. '
        '[[Agent Reliability]]', encoding='utf-8')
    (src / 'Pasta Recipes.md').write_text(
        '# Pasta Recipes\nTomato basil garlic olive oil simmer sauce noodles. [[Dessert Ideas]]', encoding='utf-8')
    (src / 'Dessert Ideas.md').write_text(
        '# Dessert Ideas\nChocolate cake sugar vanilla cream baking oven. [[Pasta Recipes]]', encoding='utf-8')

    report = run_eval(src, out, holdout_ratio=0.30)
    lr = report['link_reconstruction']
    assert lr['scored_edges'] >= 1
    # At least one held-out topical link should be recovered in the top 5.
    assert lr['recall_at_5'] > 0.0
    assert lr['mean_reciprocal_rank'] > 0.0


def test_eval_calibration_runs_and_reports_baseline(tmp_path: Path):
    src = tmp_path / 'notes'
    out = tmp_path / 'eval'
    src.mkdir()
    (src / 'Agent Reliability.md').write_text(
        '# Agent Reliability\nAgent timeout memory reliability retries. [[Testing Strategy]] [[Timeout Memory]]', encoding='utf-8')
    (src / 'Testing Strategy.md').write_text(
        '# Testing Strategy\nLong running tests timeout reliability retries. [[Agent Reliability]] [[Timeout Memory]]', encoding='utf-8')
    (src / 'Timeout Memory.md').write_text(
        '# Timeout Memory\nTimeout memory retries for long running agent tests. [[Agent Reliability]]', encoding='utf-8')
    report = run_eval(src, out, holdout_ratio=0.30, calibrate=True, trials=8)
    assert 'calibration' in report
    cal = report['calibration']
    assert cal['trials'] == 8
    assert set(cal['best_weights']) == set(cal['baseline_weights'])
    # Calibration never reports a worse vector than the baseline as "best".
    assert cal['best']['recall_at_5'] >= cal['baseline']['recall_at_5']
