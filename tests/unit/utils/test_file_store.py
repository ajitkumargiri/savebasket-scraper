from datetime import datetime, timezone

from savebasket_data.config.settings import Settings
from savebasket_data.utils.file_store import FileStore


def test_file_store_writes_json_and_text(tmp_path) -> None:
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
    store = FileStore(settings)
    current = datetime(2026, 4, 19, 9, 0, tzinfo=timezone.utc)

    json_path = store.write_json("raw", "aldi.json", [{"name": "milk"}], value=current)
    text_path = store.write_text("normalized", "aldi.txt", "done", value=current)

    assert json_path.exists()
    assert text_path.exists()
    assert json_path.parent.name == "2026-04-19"
    assert text_path.read_text(encoding="utf-8") == "done"
