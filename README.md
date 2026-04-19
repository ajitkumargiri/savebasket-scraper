# SaveBasket Scraper

Multi-store price scraper for Dutch supermarkets (ALDI, Albert Heijn, Jumbo, Vomar).

## Project Structure

```
savebasket-scraper/
├── src/
│   ├── scrapers/              # Individual store scrapers
│   │   ├── aldi.py            # ALDI products scraper
│   │   ├── ah.py              # Albert Heijn products scraper
│   │   ├── jumbo.py           # Jumbo products scraper
│   │   ├── vomar.py           # Vomar products scraper
│   │
│   ├── core/                  # Core functionality
│   │   ├── cleaner.py         # Text cleaning & normalization
│   │   ├── extractor.py       # Product data extraction
│   │   ├── matcher.py         # Product matching & deduplication
│   │
│   ├── pipeline/              # Scraping pipelines
│   │   ├── run_all.py         # Run all scrapers + processing
│   │
│   ├── utils/                 # Utilities
│   │   ├── logger.py          # Logging utilities
│   │
│   └── __init__.py
│
├── output/
│   ├── raw/                   # Raw scraped data (unprocessed)
│   ├── processed/             # Processed & deduplicated data
│
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Installation

1. **Clone or navigate to the repository:**
   ```bash
   cd savebasket-scraper
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright browsers:**
   ```bash
   python -m playwright install chromium
   ```

## Usage

### Run Sprint 1 Normalization Demo

```bash
python -m savebasket_data demo-normalization
```

This reads [tests/fixtures/raw/normalization_demo.json](/workspaces/savebasket-scraper/tests/fixtures/raw/normalization_demo.json), normalizes 10 mixed sample products, and prints before/after output plus one validated import payload per store. Normalized records now keep `category_group` and `category` as separate taxonomy fields.

### Run Sprint 2 Store Imports

```bash
python -m savebasket_data run-aldi-import
python -m savebasket_data run-jumbo-import
python -m savebasket_data run-vomar-import --fixture-path tests/fixtures/raw/vomar/products.json
```

`run-aldi-import` and `run-jumbo-import` now scrape the full live catalog for each store. All three commands also accept `--fixture-path` if you want deterministic input for testing. `run-vomar-import` still requires a fixture because Vomar is returning `403` to this environment.

### Run All Scrapers (Recommended)

Run the complete pipeline - scrape all stores, collect data, and deduplicate:

```bash
python -m src.pipeline.run_all
```

This will:
1. Scrape ALDI, Albert Heijn, Jumbo, and Vomar
2. Save raw data to `output/raw/`
3. Deduplicate products
4. Save processed data to `output/processed/`

### Run Individual Scrapers

#### ALDI
```bash
python -m src.scrapers.aldi
```

#### Albert Heijn
```bash
python -m src.scrapers.ah
```

#### Jumbo
```bash
python -m src.scrapers.jumbo
```

#### Vomar
```bash
python -m src.scrapers.vomar
```

## Features

### 🧹 Data Cleaning
- Converts product names to lowercase
- Normalizes units: `liter` → `l`, `gram` → `g`, `kilogram` → `kg`, etc.
- Removes special characters
- Cleans whitespace

### 🔍 Product Extraction
- Extracts: name, brand, price, quantity, link
- Per-store optimized CSS selectors
- Robust error handling

### 🔗 Product Matching
- Detects duplicate products across stores
- Similarity-based matching
- Optional deduplication

### 📊 Logging
- Progress tracking
- Error reporting
- Success summaries

## Data Format

### Raw Output (output/raw/)

```json
{
  "store": "ALDI",
  "brand": "brand name",
  "name": "product name",
  "price": 2.50,
  "quantity": "500g",
  "link": "https://..."
}
```

### Processed Output (output/processed/)

Same format, but deduplicated (no duplicate entries across stores).

## File Outputs

Each scraper creates:
- **Timestamped file**: `{store}_{YYYY-MM-DD_HH-MM}.json`
- **Latest file**: `{store}_latest.json` (always the most recent run)

Examples:
- `output/raw/aldi_2026-04-12_16-04.json`
- `output/raw/aldi_latest.json`

## Configuration

### Store URLs
Edit the `URLS` or `BASE_URL` in individual scraper files to change which categories are scraped.

### Cleaning Rules
Modify `src/core/cleaner.py` to customize:
- Unit normalization
- Special character removal
- Text case conversion

### Deduplication Threshold
Set the `threshold` parameter in `run_all.py`:
```python
process_and_deduplicate(threshold=0.85)  # 0-1, higher = stricter matching
```

## Requirements

- Python 3.8+
- Playwright 1.46.0+
- Chromium browser (installed via playwright)

See `requirements.txt` for dependencies.

## Notes

- 🌐 **VPS-friendly**: Uses headless browser with sandbox disabled for server environments
- ⏱️ **Polite scraping**: 2-3 second delays between requests
- 🔒 **User-agent spoofing**: Mimics real browser to avoid blocks
- 📌 **Latest file pattern**: Each scraper saves a "latest" version for easy access

## MVP Blueprint

This repository currently provides the ingestion layer for SaveBasket. The implementation-ready plan for the revised 4-store, offer-aware MVP lives in [docs/mvp-blueprint.md](/workspaces/savebasket-scraper/docs/mvp-blueprint.md).

That document defines:

- the reduced PostgreSQL schema
- import and comparison JSON contracts
- the AH saved-HTML workflow
- the manual offers import flow
- the 4-week delivery plan

## Troubleshooting

### Browser not found
```bash
python -m playwright install chromium
```

### Import errors
Make sure you're running from the project root:
```bash
cd /path/to/savebasket-scraper
python -m src.pipeline.run_all
```

### Selector errors
Website HTML may change. Update CSS selectors in:
- `src/scrapers/{store}.py` (scrape_page function)
- `src/core/extractor.py` (extract_{store} method)

## License

MIT

## Author

SaveBasket Team
