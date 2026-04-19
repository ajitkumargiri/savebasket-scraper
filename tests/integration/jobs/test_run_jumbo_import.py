from __future__ import annotations

import json
from pathlib import Path

from savebasket_data.jobs.run_jumbo_import import run_jumbo_import


def test_run_jumbo_import_writes_artifacts_and_manifest(
    repo_root: Path,
    test_settings,
) -> None:
    fixture_path = repo_root / 'tests' / 'fixtures' / 'raw' / 'jumbo' / 'products.json'

    result = run_jumbo_import(fixture_path=fixture_path, settings=test_settings)

    assert result.status == 'success'
    assert result.total_records == 3
    assert result.valid_records == 2
    assert result.invalid_records == 1

    raw_path = test_settings.project_root / result.raw_artifact_path
    normalized_path = test_settings.project_root / result.normalized_artifact_path
    manifest_path = test_settings.project_root / result.manifest_path

    assert raw_path.exists()
    assert normalized_path.exists()
    assert manifest_path.exists()

    normalized_payload = json.loads(normalized_path.read_text(encoding='utf-8'))
    manifest_payload = json.loads(manifest_path.read_text(encoding='utf-8'))

    assert normalized_payload['store'] == 'Jumbo'
    assert len(normalized_payload['records']) == 2
    assert manifest_payload['status'] == 'success'
    assert manifest_payload['invalid_records'] == 1


def test_run_jumbo_import_writes_failed_manifest_for_invalid_fixture(
    tmp_path: Path,
    test_settings,
) -> None:
    fixture_path = tmp_path / 'broken.json'
    fixture_path.write_text('{}', encoding='utf-8')

    result = run_jumbo_import(fixture_path=fixture_path, settings=test_settings)

    assert result.status == 'failed'
    assert result.raw_artifact_path is None
    assert result.normalized_artifact_path is None

    manifest_path = test_settings.project_root / result.manifest_path
    manifest_payload = json.loads(manifest_path.read_text(encoding='utf-8'))

    assert manifest_payload['status'] == 'failed'
    assert 'JSON array' in manifest_payload['error_message']
