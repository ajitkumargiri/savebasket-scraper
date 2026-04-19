"""Environment-backed settings for SaveBasket data jobs."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class Settings:
    """Resolved application settings."""

    project_root: Path
    data_dir: Path
    raw_dir: Path
    normalized_dir: Path
    manifests_dir: Path
    log_level: str
    app_import_base_url: str
    app_import_api_key: str

    def ensure_runtime_dirs(self) -> None:
        """Create the standard artifact directories if they do not exist."""
        for path in (self.data_dir, self.raw_dir, self.normalized_dir, self.manifests_dir):
            path.mkdir(parents=True, exist_ok=True)

    def to_public_dict(self) -> dict[str, str]:
        """Serialize settings without secrets."""
        return {
            "project_root": str(self.project_root),
            "data_dir": str(self.data_dir),
            "raw_dir": str(self.raw_dir),
            "normalized_dir": str(self.normalized_dir),
            "manifests_dir": str(self.manifests_dir),
            "log_level": self.log_level,
            "app_import_base_url": self.app_import_base_url,
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Build and cache settings from the environment."""
    project_root = _repo_root()
    data_root_value = os.getenv("SAVEBASKET_DATA_DIR", "data")
    data_dir = Path(data_root_value)
    if not data_dir.is_absolute():
        data_dir = project_root / data_dir

    return Settings(
        project_root=project_root,
        data_dir=data_dir,
        raw_dir=data_dir / "raw",
        normalized_dir=data_dir / "normalized",
        manifests_dir=data_dir / "manifests",
        log_level=os.getenv("SAVEBASKET_LOG_LEVEL", "INFO").upper(),
        app_import_base_url=os.getenv("SAVEBASKET_APP_IMPORT_BASE_URL", "http://localhost:8080"),
        app_import_api_key=os.getenv("SAVEBASKET_APP_IMPORT_API_KEY", "change-me"),
    )
