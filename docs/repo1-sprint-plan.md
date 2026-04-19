# SaveBasket Repo 1 Sprint Plan

## Scope

This document is the execution spec for `savebasket-data`, the ingestion repository.

Repo 1 owns:

- ALDI, Jumbo, and Vomar scraping
- AH saved HTML parsing
- manual offer JSON validation and preparation
- normalization into the shared import contract
- raw, normalized, and manifest artifact generation
- internal delivery of normalized data into `savebasket-app`

Repo 1 does not own:

- public REST API
- application database schema
- basket comparison logic
- frontend screens

This plan is intentionally detailed enough for a coding agent to implement sprint by sprint.

## Sprint Model

Use weekly sprints.

Recommended cadence:

- Sprint 0: 2 to 3 days if needed
- Sprint 1 to Sprint 4: 1 week each

Each sprint must end with:

- working code merged in repo 1
- green automated checks for in-scope work
- a runnable demo flow
- documented known gaps

## Global Engineering Rules

These rules apply to every sprint.

### Source Of Truth Rules

- raw files are immutable
- normalized files are versioned per import run
- manifests are always written for success and failure cases
- no import job writes directly to the application database
- repo 1 only communicates through internal application import endpoints

### Validation Rules

- invalid records are skipped and counted
- fatal job errors fail the import run cleanly
- malformed source files are preserved for debugging
- low-confidence values are not silently corrected unless a rule is explicit

### Testing Rules

- every new parser or normalizer requires unit tests
- every import job requires at least one integration test with fixtures
- store-specific parsing logic requires fixture coverage
- every sprint demo must use reproducible fixture or real-run evidence

### Done Criteria For Any Ticket

- code exists in the expected module
- tests exist and pass
- logging is sufficient to debug failures
- output artifact shape matches the contract
- failure path is handled explicitly

## Target Repository Structure

This sprint plan assumes the repo will move toward this structure:

```text
savebasket-data/
  README.md
  pyproject.toml
  requirements.txt
  .env.example
  docs/
    import-contracts.md
    store-notes.md
    repo1-sprint-plan.md
  src/
    savebasket_data/
      __init__.py
      config/
        settings.py
      scrapers/
        aldi.py
        jumbo.py
        vomar.py
      parsers/
        ah_saved_html.py
        offers_manual_json.py
      normalization/
        product_normalizer.py
        price_parser.py
        quantity_parser.py
        category_mapper.py
        name_cleaner.py
      contracts/
        store_price_import.py
        ah_import.py
        offer_import.py
      clients/
        app_import_client.py
      jobs/
        run_aldi_import.py
        run_jumbo_import.py
        run_vomar_import.py
        run_ah_import.py
        run_offer_import.py
        run_all_imports.py
      manifests/
        manifest_writer.py
      utils/
        logger.py
        clock.py
        file_store.py
  tests/
    unit/
    integration/
    fixtures/
      raw/
      normalized/
      html/
      offers/
  data/
    raw/
    normalized/
    manifests/
  scripts/
    setup_local.sh
    run_daily_imports.sh
```

## Sprint 0: Foundation And Contracts

### Goal

Create a clean ingestion foundation so all later sprints build on stable contracts instead of ad hoc scripts.

### Build Items

1. Convert the repo toward the target package structure.
2. Add a single configuration system for environment variables and paths.
3. Define Pydantic models for:
   - store price import payload
   - AH import payload
   - offer import payload
4. Create shared utilities for:
   - timestamp generation
   - file writing
   - manifest writing
   - structured logging
5. Add local CLI entry points with `typer`.
6. Add baseline lint and test tooling.

### Exact Files To Create Or Refactor

- `pyproject.toml`
- `src/savebasket_data/config/settings.py`
- `src/savebasket_data/contracts/store_price_import.py`
- `src/savebasket_data/contracts/ah_import.py`
- `src/savebasket_data/contracts/offer_import.py`
- `src/savebasket_data/utils/logger.py`
- `src/savebasket_data/utils/clock.py`
- `src/savebasket_data/utils/file_store.py`
- `src/savebasket_data/manifests/manifest_writer.py`
- `tests/unit/contracts/`
- `tests/unit/utils/`

### Technical Acceptance Criteria

- package imports work from `src/savebasket_data`
- all three import contracts validate representative payloads
- file store can write JSON and text files to date-based directories
- manifest writer can write `success` and `failed` runs
- CLI can print available commands without errors
- lint and unit test commands run successfully

### Demo

Show:

1. one example contract validation for each payload type
2. one generated manifest file
3. one raw file and one normalized file written through shared utilities

### Sprint Exit Criteria

- repo no longer depends on scattered one-off script patterns for new work
- shared import contract layer exists
- later sprint code can build on shared utilities instead of duplicating path and logging logic

## Sprint 1: Normalization Core

### Goal

Build the reusable normalization engine for all stores.

### Build Items

1. Implement product name cleaning.
2. Implement price parsing and validation.
3. Implement quantity extraction and unit normalization.
4. Implement source category to MVP category mapping.
5. Implement a canonical normalized product record builder.
6. Add fixture-driven tests for edge cases.

### Exact Files To Create Or Refactor

- `src/savebasket_data/normalization/name_cleaner.py`
- `src/savebasket_data/normalization/price_parser.py`
- `src/savebasket_data/normalization/quantity_parser.py`
- `src/savebasket_data/normalization/category_mapper.py`
- `src/savebasket_data/normalization/product_normalizer.py`
- `tests/unit/normalization/test_name_cleaner.py`
- `tests/unit/normalization/test_price_parser.py`
- `tests/unit/normalization/test_quantity_parser.py`
- `tests/unit/normalization/test_category_mapper.py`
- `tests/unit/normalization/test_product_normalizer.py`

### Required Behaviors

- decimal comma and decimal point formats are handled consistently
- obvious currency noise is removed safely
- common Dutch and English unit variants normalize to the same units
- unsupported or malformed quantities do not crash normalization
- output includes `normalized_name`, `quantity_value`, `quantity_unit`, and `captured_at`

### Technical Acceptance Criteria

- normalized output shape matches `StorePriceImport` item contract
- normalization handles at least the top expected unit patterns:
  - `g`
  - `kg`
  - `ml`
  - `l`
  - piece or count-like formats when possible
- malformed quantities degrade gracefully
- all normalization unit tests pass

### Demo

Show normalization of 10 mixed sample products from different stores with before and after output.

### Sprint Exit Criteria

- all later store-specific parsers can call one normalization engine
- normalization behavior is test-backed and stable

## Sprint 2: Automated Store Imports

### Goal

Get ALDI, Jumbo, and Vomar imports working through the new pipeline.

### Build Items

1. Refactor ALDI scraper into package structure.
2. Refactor Jumbo scraper into package structure.
3. Refactor Vomar scraper into package structure.
4. Standardize scraper output before normalization.
5. Implement store job runners that:
   - run scrape
   - save raw output
   - normalize records
   - save normalized output
   - write manifest
6. Add integration tests with store fixtures.

### Exact Files To Create Or Refactor

- `src/savebasket_data/scrapers/aldi.py`
- `src/savebasket_data/scrapers/jumbo.py`
- `src/savebasket_data/scrapers/vomar.py`
- `src/savebasket_data/jobs/run_aldi_import.py`
- `src/savebasket_data/jobs/run_jumbo_import.py`
- `src/savebasket_data/jobs/run_vomar_import.py`
- `tests/integration/jobs/test_run_aldi_import.py`
- `tests/integration/jobs/test_run_jumbo_import.py`
- `tests/integration/jobs/test_run_vomar_import.py`
- `tests/fixtures/raw/aldi/`
- `tests/fixtures/raw/jumbo/`
- `tests/fixtures/raw/vomar/`

### Required Behaviors

- each store run writes raw artifacts under a date folder
- each store run writes normalized output under a date folder
- each store run writes a manifest with counts
- parser failures are counted and logged
- full job failure still writes a failed manifest

### Technical Acceptance Criteria

- ALDI import works end to end from scraper to normalized file
- Jumbo import works end to end from scraper to normalized file
- Vomar import works end to end from scraper to normalized file
- raw and normalized artifacts are reproducible from fixtures in tests
- import counts in manifests are correct for tested fixture runs

### Demo

Show one run for ALDI, one for Jumbo, and one for Vomar with:

1. raw output path
2. normalized output path
3. manifest counts

### Sprint Exit Criteria

- three automated stores are on the new pipeline
- store runs are scriptable and testable

## Sprint 3: Manual AH And Offers Pipeline

### Goal

Make the manual ingestion paths production-usable.

### Build Items

1. Implement saved AH HTML parser.
2. Implement AH import job runner.
3. Implement offer JSON validator and parser.
4. Implement offer import job runner.
5. Preserve raw AH HTML and raw offer JSON artifacts.
6. Normalize parsed AH records into the same shared contract.

### Exact Files To Create Or Refactor

- `src/savebasket_data/parsers/ah_saved_html.py`
- `src/savebasket_data/parsers/offers_manual_json.py`
- `src/savebasket_data/jobs/run_ah_import.py`
- `src/savebasket_data/jobs/run_offer_import.py`
- `tests/unit/parsers/test_ah_saved_html.py`
- `tests/unit/parsers/test_offers_manual_json.py`
- `tests/integration/jobs/test_run_ah_import.py`
- `tests/integration/jobs/test_run_offer_import.py`
- `tests/fixtures/html/ah/`
- `tests/fixtures/offers/`

### Required Behaviors

- AH parser reads saved HTML without live network dependency
- parser extracts product cards robustly enough for selected categories
- offer parser enforces supported offer shapes only
- invalid offers fail validation clearly
- AH and offer runs generate manifests like automated store runs

### Technical Acceptance Criteria

- AH saved HTML import works end to end from saved file to normalized records
- offer JSON validation rejects malformed records and reports why
- valid offers produce a normalized offer payload ready for repo 2
- fixture-based tests cover at least one success and one failure path for AH and offers

### Demo

Show:

1. one saved AH HTML import
2. one valid offers import
3. one invalid offers file rejection with readable error output

### Sprint Exit Criteria

- all four stores now have a defined import path in repo 1
- offer ingestion is safe enough for internal use

## Sprint 4: App Delivery Client And Orchestration

### Goal

Connect repo 1 to repo 2 through stable internal import calls.

### Build Items

1. Implement internal API client using `httpx`.
2. Add retry policy with `tenacity`.
3. Add per-job option to:
   - write files only
   - write files and push to app API
4. Implement `run_all_imports.py`.
5. Add local scripts for scheduled execution.
6. Add integration tests against mocked application endpoints.

### Exact Files To Create Or Refactor

- `src/savebasket_data/clients/app_import_client.py`
- `src/savebasket_data/jobs/run_all_imports.py`
- `scripts/run_daily_imports.sh`
- `tests/integration/clients/test_app_import_client.py`
- `tests/integration/jobs/test_run_all_imports.py`

### Required Behaviors

- API client sends valid headers and payloads
- retry happens only for transient conditions
- hard validation failures do not retry infinitely
- orchestration job can run selected stores or all configured stores
- job summary is logged clearly

### Technical Acceptance Criteria

- repo 1 can successfully post a normalized store import payload to repo 2 mock endpoint
- repo 1 can successfully post AH and offers payloads to repo 2 mock endpoints
- orchestration job returns per-store status summary
- failures in one store do not necessarily prevent independent manual jobs from being executed later

### Demo

Show one orchestration run that:

1. runs one automated store import
2. runs one AH import
3. posts payloads to a mock app endpoint
4. prints a final per-job status summary

### Sprint Exit Criteria

- repo 1 can feed repo 2 over HTTP instead of manual file copying
- daily import flow is operationally realistic

## Sprint 5: Hardening, Scheduling, And QA

### Goal

Make repo 1 stable enough for MVP production use.

### Build Items

1. Add CLI help and operator docs.
2. Add import health summary output.
3. Add retention and cleanup rules for generated artifacts.
4. Add backup-friendly artifact layout verification.
5. Add smoke scripts for scheduled imports.
6. Complete manual QA checklist against real sample imports.

### Exact Files To Create Or Refactor

- `README.md`
- `docs/import-contracts.md`
- `docs/store-notes.md`
- `scripts/setup_local.sh`
- `scripts/run_daily_imports.sh`
- optional `src/savebasket_data/jobs/run_cleanup_job.py`

### Required Behaviors

- operator can run jobs from documented commands
- job output is understandable without reading source code
- artifact layout is stable and backup-friendly
- cleanup rules never remove the latest successful artifacts for each source unintentionally

### Technical Acceptance Criteria

- local setup instructions work from a clean environment
- scheduled import script can run without manual code edits
- cleanup behavior is tested or dry-run safe
- final QA signoff exists for selected categories and sources

### Demo

Show:

1. clean setup flow
2. one scheduled run script execution
3. one operator troubleshooting example using logs and manifests

### Sprint Exit Criteria

- repo 1 is production-usable for MVP imports
- operator workflow is documented
- repo 1 can be handed to another developer without tribal knowledge loss

## Cross-Sprint Test Matrix

Every sprint should extend this matrix.

### Unit Tests

- contracts
- file writing utilities
- manifest generation
- name cleaning
- price parsing
- quantity parsing
- category mapping
- AH HTML parsing
- offer validation

### Integration Tests

- store import job end-to-end with fixtures
- AH import job end-to-end with fixtures
- offer import job end-to-end with fixtures
- HTTP delivery to mocked repo 2 endpoints

### Manual QA

- selected real products from selected categories
- at least one malformed input case per source type
- at least one retry scenario for API delivery

## Sprint Demo Template

Each sprint demo should answer:

1. what code was added
2. what files or modules were created or refactored
3. what command to run the new flow
4. what artifacts are produced
5. what tests passed
6. what is still missing before the next sprint

## Definition Of Done For Repo 1 MVP

Repo 1 is MVP-done only when all of these are true:

- ALDI, Jumbo, and Vomar automated jobs run on the shared pipeline
- AH saved HTML import works on the shared pipeline
- offer JSON import works on the shared pipeline
- every run writes raw, normalized, and manifest artifacts
- normalized payloads can be delivered to repo 2 internal endpoints
- tests cover core parsing and import flows
- operator docs exist for local and scheduled execution

## Recommended Coding Order

If a coding agent implements this plan, the safest order is:

1. package structure and contracts
2. shared utilities and manifests
3. normalization core
4. ALDI, Jumbo, and Vomar jobs
5. AH parser and job
6. offer parser and job
7. HTTP import client
8. orchestration and scheduling scripts
9. hardening and QA docs