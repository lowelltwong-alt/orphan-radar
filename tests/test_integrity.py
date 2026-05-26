from pathlib import Path
import pytest

from orphan_radar.io.hasher import assert_no_source_mutation, hash_sources
from orphan_radar.io.output_writer import OutputWriter


def test_hasher_detects_change(tmp_path: Path):
    p = tmp_path / 'a.md'
    p.write_text('hello', encoding='utf-8')
    before = hash_sources([p])
    p.write_text('changed', encoding='utf-8')
    after = hash_sources([p])
    with pytest.raises(RuntimeError):
        assert_no_source_mutation(before, after)


def test_output_writer_refuses_source_directory(tmp_path: Path):
    src = tmp_path / 'src'
    src.mkdir()
    out = src / 'radar_output'
    with pytest.raises(RuntimeError):
        OutputWriter(src, out)
