from datetime import datetime, timezone

from savebasket_data.config.settings import Settings
from savebasket_data.manifests.manifest_writer import ManifestWriter
from savebasket_data.utils.file_store import FileStore


def test_manifest_writer_writes_success_and_failed(tmp_path) -> None:
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        raw_dir=tmp_path / "data" / "raw",
        normalized_dir=tmp_path / "data" / "normalized",
        manifests_dir=tmp_path / "data" / "manifests",
        log_level="INFO",
        app_import_base_url="http://localhost:8080",
        app_import_api_key="secret",
    )
    writer = ManifestWriter(FileStore(settings))
    now = datetime(2026, 4, 19, 9, 0, tzinfo=timezone.utc)

    success = writer.write_success(
        import_id="aldi-20260419",
        job_name="run_aldi_import",
        started_at=now,
        finished_at=now,
        raw_artifact_path="data/raw/2026-04-19/aldi.json",
        normalized_artifact_path="data/normalized/2026-04-19/aldi.json",
        total_records=10,
        valid_records=9,
        invalid_records=1,
    )
    failed = writer.write_failed(
        import_id="aldi-20260420",
        job_name="run_aldi_import",
        started_at=now,
        finished_at=now,
        total_records=0,
        valid_records=0,
        invalid_records=0,
        error_message="boom",
    )

    success_path = settings.manifests_dir / "2026-04-19" / "aldi-20260419.json"
    failed_path = settings.manifests_dir / "2026-04-19" / "aldi-20260420.json"

    assert success.status == "success"
    assert failed.status == "failed"
    assert success_path.exists()
    assert failed_path.exists()
