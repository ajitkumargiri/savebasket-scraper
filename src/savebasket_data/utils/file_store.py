"""Shared file writing helpers for raw, normalized, and manifest artifacts."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ..config.settings import Settings, get_settings
from .clock import date_stamp


class FileStore:
    """Write dated artifacts under the configured data directories."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.settings.ensure_runtime_dirs()

    def _base_dir(self, artifact_type: str) -> Path:
        mapping = {
            "raw": self.settings.raw_dir,
            "normalized": self.settings.normalized_dir,
            "manifests": self.settings.manifests_dir,
        }
        try:
            return mapping[artifact_type]
        except KeyError as exc:
            raise ValueError(f"Unsupported artifact type: {artifact_type}") from exc

    def dated_dir(self, artifact_type: str, value: datetime | None = None) -> Path:
        """Return the dated directory for an artifact type."""
        path = self._base_dir(artifact_type) / date_stamp(value)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def write_json(
        self,
        artifact_type: str,
        filename: str,
        payload: Any,
        value: datetime | None = None,
    ) -> Path:
        """Write a JSON artifact to the dated directory."""
        path = self.dated_dir(artifact_type, value) / filename
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    def write_text(
        self,
        artifact_type: str,
        filename: str,
        content: str,
        value: datetime | None = None,
    ) -> Path:
        """Write a text artifact to the dated directory."""
        path = self.dated_dir(artifact_type, value) / filename
        path.write_text(content, encoding="utf-8")
        return path
