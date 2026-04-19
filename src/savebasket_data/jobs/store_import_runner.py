"""Shared store import runner for automated store jobs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from ..config.settings import Settings, get_settings
from ..contracts.store_price_import import StorePriceImportPayload, StorePriceRecord
from ..manifests.manifest_writer import ImportManifest, ManifestWriter
from ..normalization.product_normalizer import RawStoreProduct, normalize_store_product
from ..utils.clock import date_stamp, run_id, utc_now
from ..utils.file_store import FileStore
from ..utils.logger import get_logger

RawRecordFetcher = Callable[[Path | None], list[dict[str, Any]]]


@dataclass(slots=True)
class StoreImportRunResult:
    """Materialized result of a store import job run."""

    import_id: str
    store: str
    status: str
    raw_artifact_path: str | None
    normalized_artifact_path: str | None
    manifest_path: str
    total_records: int
    valid_records: int
    invalid_records: int
    error_message: str | None = None


def _relative_to_project(path: Path, project_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(project_root.resolve()))
    except ValueError:
        return str(path.resolve())


def _manifest_path(settings: Settings, manifest: ImportManifest) -> str:
    path = settings.manifests_dir / date_stamp(manifest.finished_at) / f'{manifest.import_id}.json'
    return _relative_to_project(path, settings.project_root)


def run_store_import(
    *,
    store_slug: str,
    store_name: str,
    job_name: str,
    fetch_records: RawRecordFetcher,
    fixture_path: Path | None = None,
    settings: Settings | None = None,
) -> StoreImportRunResult:
    """Run one automated store import from raw records to normalized artifact."""
    resolved_settings = settings or get_settings()
    file_store = FileStore(resolved_settings)
    manifest_writer = ManifestWriter(file_store)
    logger = get_logger(f'savebasket_data.jobs.{store_slug}')

    started_at = utc_now()
    import_id = run_id(store_slug, started_at)
    total_records = 0
    valid_records = 0
    invalid_records = 0
    raw_artifact_path: str | None = None
    normalized_artifact_path: str | None = None

    try:
        logger.info('Starting %s import', store_name)
        raw_records = fetch_records(fixture_path)
        total_records = len(raw_records)

        raw_path = file_store.write_json('raw', f'{import_id}.json', raw_records, value=started_at)
        raw_artifact_path = _relative_to_project(raw_path, resolved_settings.project_root)

        normalized_records: list[StorePriceRecord] = []
        for index, raw_record in enumerate(raw_records):
            try:
                product = RawStoreProduct.from_mapping(raw_record)
            except (KeyError, TypeError, ValueError) as exc:
                invalid_records += 1
                logger.warning('Skipping malformed %s record %s: %s', store_name, index, exc)
                continue

            normalized_record = normalize_store_product(product)
            if normalized_record is None:
                invalid_records += 1
                logger.warning('Skipping unnormalizable %s record %s', store_name, index)
                continue

            normalized_records.append(normalized_record)

        if not normalized_records:
            raise ValueError('No valid records after normalization')

        canonical_store = normalized_records[0].store
        if any(record.store != canonical_store for record in normalized_records[1:]):
            raise ValueError('Normalized records span multiple stores')

        payload = StorePriceImportPayload(
            import_id=import_id,
            store=canonical_store,
            imported_at=started_at,
            source_type='scraper',
            source_artifact_path=raw_artifact_path,
            records=normalized_records,
        )
        valid_records = len(payload.records)

        normalized_path = file_store.write_json(
            'normalized',
            f'{import_id}.json',
            payload.model_dump(mode='json'),
            value=started_at,
        )
        normalized_artifact_path = _relative_to_project(
            normalized_path,
            resolved_settings.project_root,
        )

        manifest = manifest_writer.write_success(
            import_id=import_id,
            job_name=job_name,
            started_at=started_at,
            finished_at=utc_now(),
            raw_artifact_path=raw_artifact_path,
            normalized_artifact_path=normalized_artifact_path,
            total_records=total_records,
            valid_records=valid_records,
            invalid_records=invalid_records,
        )
        logger.info(
            'Completed %s import: %s valid, %s invalid',
            store_name,
            valid_records,
            invalid_records,
        )
    except Exception as exc:
        manifest = manifest_writer.write_failed(
            import_id=import_id,
            job_name=job_name,
            started_at=started_at,
            finished_at=utc_now(),
            raw_artifact_path=raw_artifact_path,
            normalized_artifact_path=normalized_artifact_path,
            total_records=total_records,
            valid_records=valid_records,
            invalid_records=invalid_records,
            error_message=str(exc),
        )
        logger.error('Failed %s import: %s', store_name, exc)

    return StoreImportRunResult(
        import_id=import_id,
        store=store_name,
        status=manifest.status,
        raw_artifact_path=raw_artifact_path,
        normalized_artifact_path=normalized_artifact_path,
        manifest_path=_manifest_path(resolved_settings, manifest),
        total_records=manifest.total_records,
        valid_records=manifest.valid_records,
        invalid_records=manifest.invalid_records,
        error_message=manifest.error_message,
    )
