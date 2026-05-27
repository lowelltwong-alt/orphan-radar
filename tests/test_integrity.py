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


def test_config_validation_rejects_out_of_range():
    import pytest
    from orphan_radar.core.settings import ConfigValidationError, RadarSettings

    s = RadarSettings()
    assert s.validate() is s
    with pytest.raises(ConfigValidationError):
        RadarSettings(hub_penalty=-10).validate()
    with pytest.raises(ConfigValidationError):
        RadarSettings(acceptance_boundary=2.0).validate()
    with pytest.raises(ConfigValidationError):
        RadarSettings(similarity_top_k=2.5).validate()


def test_config_warns_on_unknown_key(tmp_path):
    import json
    import warnings

    from orphan_radar.core.settings import RadarSettings

    cfg = tmp_path / 'c.json'
    cfg.write_text(json.dumps({'hub_penalty': 0.2, 'hub_pelnaty': 0.9}), encoding='utf-8')
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        settings = RadarSettings.from_json_file(cfg)
    assert settings.hub_penalty == 0.2
    assert any('hub_pelnaty' in str(w.message) for w in caught)
