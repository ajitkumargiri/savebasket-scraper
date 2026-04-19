from __future__ import annotations

import json
from pathlib import Path

from savebasket_data.jobs.run_aldi_import import run_aldi_import


def test_run_aldi_import_writes_artifacts_and_manifest(repo_root: Path, test_settings) -> None:
    fixture_path = repo_root / 'tests' / 'fixtures' / 'raw' / 'aldi' / 'products.json'

    result = run_aldi_import(fixture_path=fixture_path, settings=test_settings)

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

    raw_payload = json.loads(raw_path.read_text(encoding='utf-8'))
    normalized_payload = json.loads(normalized_path.read_text(encoding='utf-8'))
    manifest_payload = json.loads(manifest_path.read_text(encoding='utf-8'))

    assert len(raw_payload) == 3
    assert normalized_payload['store'] == 'ALDI'
    assert len(normalized_payload['records']) == 2
    assert manifest_payload['status'] == 'success'
    assert manifest_payload['valid_records'] == 2
