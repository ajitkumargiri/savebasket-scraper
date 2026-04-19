"""Manifest writing helpers for import runs."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ..utils.file_store import FileStore

ManifestStatus = Literal["success", "failed"]


class ImportManifest(BaseModel):
    """Recorded outcome for an import run."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    import_id: str = Field(min_length=1)
    job_name: str = Field(min_length=1)
    status: ManifestStatus
    started_at: datetime
    finished_at: datetime
    raw_artifact_path: str | None = None
    normalized_artifact_path: str | None = None
    total_records: int = Field(ge=0)
    valid_records: int = Field(ge=0)
    invalid_records: int = Field(ge=0)
    error_message: str | None = None


class ManifestWriter:
    """Persist import manifests through the shared file store."""

    def __init__(self, file_store: FileStore | None = None):
        self.file_store = file_store or FileStore()

    def write(self, manifest: ImportManifest) -> ImportManifest:
        """Write the manifest payload and return it."""
        filename = f"{manifest.import_id}.json"
        self.file_store.write_json(
            "manifests",
            filename,
            manifest.model_dump(mode="json"),
            value=manifest.finished_at,
        )
        return manifest

    def write_success(self, **kwargs: object) -> ImportManifest:
        """Create and write a successful manifest."""
        manifest = ImportManifest(status="success", error_message=None, **kwargs)
        return self.write(manifest)

    def write_failed(self, **kwargs: object) -> ImportManifest:
        """Create and write a failed manifest."""
        manifest = ImportManifest(status="failed", **kwargs)
        return self.write(manifest)
