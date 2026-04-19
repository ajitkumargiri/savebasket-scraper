# SaveBasket Repo Structure And Tech Stack

## Decision

The MVP should use `2 repositories`.

This is the best tradeoff for speed, maintainability, and team clarity.

### Why Not 1 Repo

A single repo would mix:

- Python scraping and parsing
- Spring Boot REST API
- React frontend
- deployment and infra

That is possible, but it creates avoidable coupling and makes release flow harder.

### Why Not 3 Repos

Three repos are too heavy for the MVP.

That would mean separate repos for:

- ingestion
- backend
- frontend

This adds unnecessary overhead:

- more CI pipelines
- more version coordination
- more cross-repo feature work
- more deployment complexity

## Recommended Repositories

## Repo 1: savebasket-data

Purpose:

- scrape ALDI, Jumbo, and Vomar
- parse saved AH HTML files
- prepare and validate manual offer JSON payloads
- normalize raw source data into one shared import contract
- keep raw, normalized, and manifest artifacts
- push normalized payloads to the application API

This repo evolves from the current scraper repository.

### Responsibilities

This repo owns:

- source collection
- parsing
- normalization
- artifact versioning
- import job orchestration
- internal delivery of normalized data to the app repo

This repo does not own:

- public REST API
- user-facing frontend
- database schema for the application
- basket comparison logic used by the live product

### Recommended Tech Stack

- Python `3.12`
- Playwright for ALDI, Jumbo, and Vomar automation
- BeautifulSoup4 plus `lxml` for saved AH HTML parsing
- Pydantic v2 for contract validation
- `httpx` for calling internal Spring Boot import endpoints
- `typer` for CLI commands
- `tenacity` for retry behavior on internal API calls
- `orjson` for fast JSON handling
- `pytest` for tests
- `ruff` for linting and formatting

### Exact Repo Structure

```text
savebasket-data/
  README.md
  pyproject.toml
  requirements.txt
  .env.example
  docs/
    import-contracts.md
    store-notes.md
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

### Key Module Responsibilities

- `scrapers/`: collect live store pages where automation is stable
- `parsers/ah_saved_html.py`: parse manually downloaded AH category pages
- `parsers/offers_manual_json.py`: validate manually prepared flyer JSON
- `normalization/`: convert store-specific fields into the shared import contract
- `contracts/`: exact payload shapes expected by the app repo
- `clients/app_import_client.py`: send normalized payloads to Spring Boot internal endpoints
- `jobs/`: orchestration entry points
- `manifests/`: import metadata for auditability
- `data/`: immutable artifacts and derived normalized files

### How Repo 1 Talks To Repo 2

Repo 1 should call internal application endpoints such as:

- `POST /api/internal/imports/store-prices`
- `POST /api/internal/imports/ah-html`
- `POST /api/internal/imports/offers`

Authentication:

- API key in request header
- internal-only endpoint exposure
- optional IP allowlist if convenient on Hetzner

## Repo 2: savebasket-app

Purpose:

- host the actual product
- provide the public REST API
- provide the frontend
- own the application database schema
- own basket comparison logic
- own offer application logic
- own deployment and runtime operations

### Responsibilities

This repo owns:

- Spring Boot REST API
- React frontend
- database migrations
- product search
- basket comparison
- active offer application
- internal ops pages
- deployment configuration

This repo does not own:

- live scraping implementation
- raw source artifact collection
- browser automation logic

## Spring Boot Backend Stack

Use Spring Boot for the REST API.

### Recommended Backend Stack

- Java `21` LTS
- Spring Boot `3.4.x`
- Spring Web for REST endpoints
- Spring Validation for request validation
- Spring Data JPA for persistence
- Flyway for database migrations
- PostgreSQL driver
- Spring Security for internal endpoint protection
- Spring Actuator for health and readiness endpoints
- Springdoc OpenAPI for API docs
- Testcontainers for integration tests
- JUnit 5 for tests
- AssertJ for assertions
- Mockito for focused unit tests when needed
- MapStruct for DTO to entity mapping

### Backend Responsibilities By Module

- `controller`: HTTP endpoints
- `service`: business logic
- `repository`: database access
- `entity`: JPA entities
- `dto`: request and response payloads
- `mapper`: DTO and entity mapping
- `config`: security, CORS, serialization, app settings
- `scheduler`: freshness checks or maintenance jobs if needed
- `support`: shared utility classes
- `exception`: global error handling

### Exact Backend Structure

```text
savebasket-app/
  README.md
  .env.example
  backend/
    build.gradle.kts
    settings.gradle.kts
    src/
      main/
        java/
          com/savebasket/app/
            SaveBasketApplication.java
            config/
              SecurityConfig.java
              JacksonConfig.java
              CorsConfig.java
              OpenApiConfig.java
            controller/
              ProductController.java
              BasketController.java
              ImportController.java
              OfferController.java
              StoreController.java
              HealthController.java
            service/
              ProductService.java
              BasketComparisonService.java
              ImportService.java
              AhImportService.java
              OfferService.java
              MatchingService.java
              FreshnessService.java
            repository/
              StoreRepository.java
              CanonicalProductRepository.java
              StoreProductRepository.java
              CurrentPriceRepository.java
              OfferRepository.java
              ImportRunRepository.java
            entity/
              Store.java
              CanonicalProduct.java
              StoreProduct.java
              CurrentPrice.java
              Offer.java
              ImportRun.java
            dto/
              request/
                StorePriceImportRequest.java
                AhHtmlImportRequest.java
                OfferImportRequest.java
                BasketCompareRequest.java
              response/
                ProductSearchResponse.java
                BasketCompareResponse.java
                StoreStatusResponse.java
                ImportRunResponse.java
            mapper/
              ProductMapper.java
              OfferMapper.java
            validation/
              OfferRulesValidator.java
              QuantityValidator.java
            exception/
              GlobalExceptionHandler.java
              ApiError.java
            support/
              MoneyUtils.java
              QuantityUtils.java
              ClockProvider.java
      main/
        resources/
          application.yml
          db/
            migration/
              V001__create_stores.sql
              V002__create_canonical_products.sql
              V003__create_store_products.sql
              V004__create_current_prices.sql
              V005__create_offers.sql
              V006__create_import_runs.sql
      test/
        java/
          com/savebasket/app/
            unit/
            integration/
            e2e/
```

## Frontend Stack

### Recommended Frontend Stack

- React `19`
- TypeScript
- Vite
- React Router
- TanStack Query
- Zustand for local basket and UI state
- Zod for runtime validation where needed
- Tailwind CSS for styling
- Vitest for unit tests
- Playwright for frontend E2E tests

### Frontend Structure

```text
savebasket-app/
  frontend/
    package.json
    vite.config.ts
    tsconfig.json
    src/
      main.tsx
      app/
        App.tsx
        routes.tsx
        providers.tsx
      pages/
        SearchPage.tsx
        BasketPage.tsx
        ComparisonPage.tsx
        ImportStatusPage.tsx
        AhImportPage.tsx
        OfferImportPage.tsx
      components/
        layout/
          Layout.tsx
          Header.tsx
        search/
          ProductSearchInput.tsx
          CategoryFilter.tsx
          SearchResultsList.tsx
          ProductCard.tsx
          StorePricePreview.tsx
          OfferBadge.tsx
        basket/
          BasketList.tsx
          BasketItem.tsx
          QuantityControl.tsx
          BasketSummaryPanel.tsx
          BasketEmptyState.tsx
        comparison/
          ComparisonSummary.tsx
          StoreComparisonCard.tsx
          PriceBreakdownRow.tsx
          AppliedOfferList.tsx
          MissingProductNotice.tsx
          WinnerBanner.tsx
        internal/
          ImportRunTable.tsx
          StoreFreshnessCard.tsx
          OfferImportForm.tsx
          AhImportForm.tsx
      api/
        client.ts
        productsApi.ts
        basketApi.ts
        importsApi.ts
        offersApi.ts
        storesApi.ts
      store/
        basketStore.ts
        comparisonStore.ts
        searchStore.ts
        systemStore.ts
      hooks/
      types/
      utils/
      test/
```

## Infra And Deployment Layout

### Recommended Infra Structure

```text
savebasket-app/
  infra/
    docker/
      backend.Dockerfile
      frontend.Dockerfile
    caddy/
      Caddyfile
    compose/
      docker-compose.prod.yml
      docker-compose.local.yml
    scripts/
      deploy.sh
      rollback.sh
      backup.sh
      restore.sh
```

### Runtime Stack On Hetzner

- Ubuntu host
- Docker Engine
- Docker Compose
- Caddy
- Spring Boot container
- frontend static container or frontend static artifact mounted into Caddy
- PostgreSQL 16
- host cron or systemd timer for backups and import scheduling

## Recommended Final Stack By Repo

## Repo 1: savebasket-data

- Python 3.12
- Playwright
- BeautifulSoup4 plus lxml
- Pydantic v2
- httpx
- typer
- pytest
- ruff
- orjson

## Repo 2: savebasket-app

### Backend

- Java 21
- Spring Boot 3.4.x
- Spring Web
- Spring Validation
- Spring Data JPA
- Flyway
- PostgreSQL
- Spring Security
- Spring Actuator
- Springdoc OpenAPI
- Testcontainers
- JUnit 5
- MapStruct

### Frontend

- React 19
- TypeScript
- Vite
- React Router
- TanStack Query
- Zustand
- Zod
- Tailwind CSS
- Vitest
- Playwright

### Infra

- Docker Compose
- Caddy
- PostgreSQL 16
- Hetzner single-server deployment

## CI/CD Recommendation

## Repo 1 CI

- run lint
- run unit tests
- run parser and normalization integration tests
- optionally run dry-run imports against fixtures

## Repo 2 CI

- run backend unit and integration tests
- run frontend unit tests
- run selected E2E tests
- build backend artifact
- build frontend assets
- build Docker images

## Communication Contract Between Repos

The contract between the two repos must be stable and versioned.

Rules:

- repo 1 publishes payloads that conform to the import contract
- repo 2 validates all payloads before persistence
- breaking changes to import contracts must be versioned and documented
- repo 1 never writes directly to repo 2 database in MVP

## Local Development Recommendation

During development:

- run repo 2 locally with PostgreSQL
- run repo 1 locally for imports
- send normalized data from repo 1 into repo 2 local internal import endpoints

This keeps the boundary realistic from day one.

## Final Recommendation

Use these repository names:

1. `savebasket-data`
2. `savebasket-app`

Use this split:

- `savebasket-data` = ingestion and normalization
- `savebasket-app` = Spring Boot REST API, React frontend, database, deployment

This is the best MVP structure for your preferred stack and for future team scaling.
