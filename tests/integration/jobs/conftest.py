from __future__ import annotations

from pathlib import Path

import pytest

from savebasket_data.config.settings import Settings


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


@pytest.fixture
def test_settings(tmp_path: Path) -> Settings:
    data_dir = tmp_path / 'data'
    return Settings(
        project_root=tmp_path,
        data_dir=data_dir,
        raw_dir=data_dir / 'raw',
        normalized_dir=data_dir / 'normalized',
        manifests_dir=data_dir / 'manifests',
        log_level='INFO',
        app_import_base_url='http://localhost:8080',
        app_import_api_key='secret',
    )
