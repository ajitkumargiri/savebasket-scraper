# SaveBasket MVP Blueprint

## Goal

Build a human-assisted grocery comparison MVP that answers one question well:

Which single store is cheapest for a user's basket after active offers are applied?

The MVP keeps automation where it is reliable and uses manual imports where automation is still fragile.

## MVP Scope

In scope:

- Stores: ALDI, Jumbo, Vomar, AH
- Categories: 1 to 3 selected categories only
- ALDI, Jumbo, Vomar via existing scraper/import pipeline
- AH via saved category page HTML import
- Offers via manually prepared JSON from scanned flyer PDFs
- Product search
- Basket comparison across 4 stores
- Offer-aware totals
- Cheapest complete basket result

Out of scope:

- OCR automation
- Fully automated AH scraping as the primary path
- Split-basket optimization across stores
- User accounts
- Saved baskets
- Price history charts
- Admin dashboard beyond a small internal API

## Current Repo Mapping

This repository is currently the ingestion foundation, not the full application.

Existing components:

- [src/scrapers/aldi.py](/workspaces/savebasket-scraper/src/scrapers/aldi.py)
- [src/scrapers/jumbo.py](/workspaces/savebasket-scraper/src/scrapers/jumbo.py)
- [src/scrapers/vomar.py](/workspaces/savebasket-scraper/src/scrapers/vomar.py)
- [src/scrapers/ah.py](/workspaces/savebasket-scraper/src/scrapers/ah.py)
- [src/core/cleaner.py](/workspaces/savebasket-scraper/src/core/cleaner.py)
- [src/core/matcher.py](/workspaces/savebasket-scraper/src/core/matcher.py)
- [src/pipeline/run_all.py](/workspaces/savebasket-scraper/src/pipeline/run_all.py)
- [ah_page_source.html](/workspaces/savebasket-scraper/ah_page_source.html)

Missing application layers for the MVP:

- database schema and migrations
- import API
- product search API
- basket comparison API
- offer import and validation flow
- frontend for search, basket, and comparison

## Recommended Categories

Start with no more than three categories:

- dairy and eggs
- drinks
- breakfast and bread basics

These categories are frequent, visible to users, and easier to match than long-tail products.

## System Shape

The MVP should be split into five layers:

1. Ingestion layer
2. Normalization layer
3. Matching layer
4. API layer
5. UI layer

### Ingestion Layer

- ALDI, Jumbo, Vomar: existing scrapers produce normalized or near-normalized records
- AH: parse saved HTML from manually downloaded category pages
- Offers: import manually prepared JSON from scanned flyers

### Normalization Layer

Standardize all store records into one shape before matching or persistence.

Required normalized fields:

- store
- external_id
- name
- normalized_name
- brand
- category
- price
- currency
- quantity_text
- quantity_value
- quantity_unit
- product_url
- image_url
- availability
- captured_at

### Matching Layer

Use strict rules for MVP. False positives are worse than unmatched products.

Matching order:

1. exact normalized name plus same unit
2. exact normalized name after punctuation cleanup plus same unit
3. same brand plus high similarity plus same unit
4. manual review bucket for uncertain matches

Do not auto-match if unit or quantity clearly disagree.

### API Layer

The backend only needs a small set of endpoints:

- `POST /api/imports/store-prices`
- `POST /api/imports/ah-html`
- `POST /api/imports/offers`
- `GET /api/products?query=milk&category=dairy_eggs`
- `GET /api/products/{id}`
- `POST /api/basket/compare`
- `GET /api/stores`
- `GET /api/stores/{slug}/status`
- `GET /api/imports/runs`
- `GET /api/offers/active?store=aldi`

### UI Layer

The frontend should stay small:

- search page
- basket page
- comparison page
- optional internal freshness page

## Data Handling Rules

Do not write scraper output directly into live comparison tables.

Use four stages:

1. raw capture
2. normalized store items
3. matched canonical products
4. live current prices and offers

Raw files should be immutable and versioned.

Recommended storage layout:

```text
data/
  raw/
    aldi/2026-04-18/run_001.json
    jumbo/2026-04-18/run_001.json
    vomar/2026-04-18/run_001.json
    ah/2026-04-18/dairy_eggs_page_1.html
    offers/2026-04-18/aldi_week17.json
  normalized/
    aldi/2026-04-18/run_001.normalized.json
    ah/2026-04-18/dairy_eggs.normalized.json
  manifests/
    imp_20260418_001.json
```

Each import run should also produce a manifest with:

- import_run_id
- source_type
- store
- category
- started_at
- finished_at
- raw_path
- normalized_path
- records_seen
- records_valid
- records_matched
- status

## Reduced PostgreSQL Schema

This is the recommended MVP database model.

### stores

```sql
CREATE TABLE stores (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    slug TEXT NOT NULL UNIQUE,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### canonical_products

```sql
CREATE TABLE canonical_products (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    normalized_name TEXT NOT NULL,
    brand TEXT,
    category TEXT NOT NULL,
    quantity_value NUMERIC(12, 3),
    quantity_unit TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_canonical_products_search
    ON canonical_products (category, normalized_name);
```

### store_products

```sql
CREATE TABLE store_products (
    id BIGSERIAL PRIMARY KEY,
    store_id BIGINT NOT NULL REFERENCES stores(id),
    canonical_product_id BIGINT REFERENCES canonical_products(id),
    external_id TEXT,
    store_product_name TEXT NOT NULL,
    normalized_name TEXT NOT NULL,
    brand TEXT,
    category TEXT NOT NULL,
    quantity_value NUMERIC(12, 3),
    quantity_unit TEXT,
    product_url TEXT,
    image_url TEXT,
    last_seen_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (store_id, external_id)
);

CREATE INDEX idx_store_products_match
    ON store_products (store_id, category, normalized_name);
```

### current_prices

```sql
CREATE TABLE current_prices (
    id BIGSERIAL PRIMARY KEY,
    store_product_id BIGINT NOT NULL REFERENCES store_products(id),
    store_id BIGINT NOT NULL REFERENCES stores(id),
    canonical_product_id BIGINT REFERENCES canonical_products(id),
    price NUMERIC(12, 2) NOT NULL CHECK (price > 0),
    currency TEXT NOT NULL DEFAULT 'EUR',
    captured_at TIMESTAMPTZ NOT NULL,
    import_run_id TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (store_product_id)
);

CREATE INDEX idx_current_prices_lookup
    ON current_prices (store_id, canonical_product_id);
```

### offers

```sql
CREATE TABLE offers (
    id BIGSERIAL PRIMARY KEY,
    store_id BIGINT NOT NULL REFERENCES stores(id),
    canonical_product_id BIGINT REFERENCES canonical_products(id),
    store_product_id BIGINT REFERENCES store_products(id),
    offer_external_id TEXT NOT NULL,
    offer_type TEXT NOT NULL,
    offer_price NUMERIC(12, 2),
    discount_amount NUMERIC(12, 2),
    discount_percent NUMERIC(5, 2),
    valid_from DATE NOT NULL,
    valid_to DATE NOT NULL,
    source_type TEXT NOT NULL,
    source_file TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (store_id, offer_external_id)
);

CREATE INDEX idx_offers_active
    ON offers (store_id, valid_from, valid_to, status);
```

### import_runs

```sql
CREATE TABLE import_runs (
    id TEXT PRIMARY KEY,
    store_id BIGINT REFERENCES stores(id),
    import_type TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_ref TEXT,
    status TEXT NOT NULL,
    records_seen INTEGER NOT NULL DEFAULT 0,
    records_valid INTEGER NOT NULL DEFAULT 0,
    records_matched INTEGER NOT NULL DEFAULT 0,
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ,
    error_message TEXT
);
```

Notes:

- `current_prices` is intentionally current-only for MVP. Add history later.
- `canonical_product_id` can remain null for unmatched store products.
- `offers` should only apply automatically when linked with high confidence.

## Import Contracts

### Store Price Import

```json
{
  "store": "Jumbo",
  "import_type": "price_import",
  "category": "dairy_eggs",
  "imported_at": "2026-04-18T10:00:00Z",
  "source_ref": "data/raw/jumbo/2026-04-18/run_001.json",
  "items": [
    {
      "external_id": "566232ZK",
      "name": "Jumbo Snack Worteltjes 300 g",
      "normalized_name": "jumbo snack worteltjes 300 g",
      "brand": "Jumbo",
      "category": "dairy_eggs",
      "price": 1.49,
      "currency": "EUR",
      "quantity_text": "300 g",
      "quantity_value": 300,
      "quantity_unit": "g",
      "product_url": "https://www.jumbo.com/producten/jumbo-snack-worteltjes-300-g-566232ZK",
      "image_url": null,
      "availability": "in_stock",
      "captured_at": "2026-04-18T12:31:03Z"
    }
  ]
}
```

Validation rules:

- `store`, `import_type`, and `items` are required
- each item must include `name` and `price`
- `price` must be numeric and greater than zero
- duplicate `external_id` values in one import should be rejected or flagged

### AH Saved HTML Import

Preferred path-based request:

```json
{
  "store": "AH",
  "category": "dairy_eggs",
  "source_type": "saved_html",
  "source_filename": "ah_dairy_eggs_page_1.html",
  "captured_at": "2026-04-18T09:00:00Z",
  "html_path": "data/raw/ah/2026-04-18/ah_dairy_eggs_page_1.html"
}
```

Fallback inline request if needed:

```json
{
  "store": "AH",
  "category": "dairy_eggs",
  "source_type": "saved_html_inline",
  "captured_at": "2026-04-18T09:00:00Z",
  "html_content": "<html>...</html>"
}
```

Use `html_path` internally when possible to avoid very large request bodies.

### Manual Offer Import

```json
{
  "store": "ALDI",
  "source_type": "manual_pdf_scan",
  "source_file": "aldi_week17_offers.json",
  "valid_from": "2026-04-22",
  "valid_to": "2026-04-28",
  "offers": [
    {
      "offer_external_id": "aldi_week17_offer_001",
      "product_name": "Campina Halfvolle Melk 1 L",
      "normalized_product_name": "campina halfvolle melk 1 l",
      "brand": "Campina",
      "category": "dairy_eggs",
      "quantity_text": "1 L",
      "quantity_value": 1,
      "quantity_unit": "l",
      "offer_type": "fixed_price",
      "offer_price": 1.19,
      "discount_amount": null,
      "discount_percent": null,
      "store_price_before": 1.39,
      "valid_from": "2026-04-22",
      "valid_to": "2026-04-28",
      "notes": "from scanned flyer"
    }
  ]
}
```

Supported MVP offer types:

- `fixed_price`
- `percent_discount`
- `amount_discount`

Validation rules:

- `fixed_price` requires `offer_price`
- `percent_discount` requires `discount_percent`
- `amount_discount` requires `discount_amount`
- `valid_to` must be on or after `valid_from`
- low-confidence matches should be stored but not auto-applied

## Basket Comparison Contract

### Request

```json
{
  "items": [
    {
      "canonical_product_id": 101,
      "quantity": 2
    },
    {
      "canonical_product_id": 205,
      "quantity": 1
    }
  ],
  "apply_offers": true
}
```

### Response

```json
{
  "basket_summary": {
    "item_count": 2,
    "currency": "EUR"
  },
  "stores": [
    {
      "store": "ALDI",
      "base_total": 4.18,
      "discount_total": 0.40,
      "final_total": 3.78,
      "is_complete": true,
      "missing_items": [],
      "applied_offers": [
        {
          "offer_external_id": "aldi_week17_offer_001",
          "canonical_product_id": 101,
          "savings": 0.40
        }
      ]
    },
    {
      "store": "Jumbo",
      "base_total": 4.59,
      "discount_total": 0.00,
      "final_total": 4.59,
      "is_complete": true,
      "missing_items": [],
      "applied_offers": []
    },
    {
      "store": "AH",
      "base_total": 3.10,
      "discount_total": 0.00,
      "final_total": 3.10,
      "is_complete": false,
      "missing_items": [205],
      "applied_offers": []
    }
  ],
  "cheapest_store": "ALDI"
}
```

Comparison rules:

- calculate per-store totals from current prices only
- apply active offers only when product linkage is trusted
- do not rank an incomplete basket as cheapest over complete baskets
- return missing products explicitly

## Suggested Backend Layout

```text
backend/
  app/
    main.py
    api/
      routers/
        products.py
        basket.py
        imports.py
        offers.py
        stores.py
    services/
      product_service.py
      comparison_service.py
      import_service.py
      offer_service.py
      matcher_service.py
    models/
      store.py
      canonical_product.py
      store_product.py
      current_price.py
      offer.py
      import_run.py
    schemas/
      product.py
      basket.py
      imports.py
      offer.py
      comparison.py
```

## Suggested Frontend Layout

```text
frontend/
  src/
    app/
    pages/
      SearchPage.tsx
      BasketPage.tsx
      ComparisonPage.tsx
    components/
      ProductSearchInput.tsx
      ProductResultsList.tsx
      ProductCard.tsx
      BasketList.tsx
      BasketItem.tsx
      QuantityControl.tsx
      StoreComparisonCard.tsx
      OfferBadge.tsx
      MissingProductNotice.tsx
```

## Four-Week Delivery Plan

### Week 1

- lock exact categories
- define canonical product shape
- stabilize ALDI, Jumbo, and Vomar imports
- add saved-HTML AH parser flow
- store raw and normalized outputs with manifests

### Week 2

- add PostgreSQL schema
- implement import endpoints
- implement product matching and upsert logic
- add offer import validation and persistence
- build basket comparison service

### Week 3

- build search, basket, and comparison UI
- surface applied offers and missing products
- connect UI to product and basket APIs

### Week 4

- improve matching for top products in selected categories
- test AH manual import end to end
- test offer import end to end
- add freshness indicators
- prepare demo deployment

## Quality Rules

Non-negotiable rules for this MVP:

1. one canonical product model
2. immutable raw imports plus validated normalized imports
3. strict comparison logic with explicit missing-item handling

Quality checks to implement early:

- price must be numeric and greater than zero
- normalized name must exist
- offer dates must be valid
- units should agree before auto-matching
- duplicate external ids within one import should be flagged
- unmatched or uncertain offers should not be auto-applied

## Recommended Next Build Step

The next implementation step should be the backend data contract layer, not more scraping.

Build in this order:

1. PostgreSQL schema and migrations
2. Pydantic request and response models for imports and basket comparison
3. import persistence flow for one store and AH saved HTML
4. offer import validation
5. comparison service

Once those pieces exist, the current scraper repo can feed a usable application MVP.