# SaveBasket Scraper — Workspace Instructions

## Project Summary

**SaveBasket Scraper** is a production-ready Python framework for scraping prices and product data from Dutch supermarket chains (ALDI, Albert Heijn, Jumbo, Vomar). It features browser automation via Playwright, intelligent data cleaning/normalization, and product deduplication using fuzzy matching.

---

## Quick Start

### Install & Setup
```bash
cd /workspaces/savebasket-scraper
pip install -r requirements.txt
python -m playwright install chromium
```

### Run Commands
```bash
# Full pipeline (all stores, deduplicated)
python -m src.pipeline.run_all

# Individual stores
python -m src.scrapers.aldi
python -m src.scrapers.ah
python -m src.scrapers.jumbo
python -m src.scrapers.vomar

# Test/validate logic
python test_brand_extraction.py
```

---

## Architecture

### Data Flow
```
Scrapers (Playwright) → ProductExtractor → Cleaner → JSON
                                                      ↓
                                        ProductMatcher (deduplicate)
                                                      ↓
                                            output/processed/
```

### Core Components

| Location | Component | Purpose |
|----------|-----------|---------|
| `src/scrapers/` | Store-specific scrapers | Browser automation, CSS selectors, page retrieval |
| `src/core/extractor.py` | ProductExtractor | Parse page elements → product dicts per store |
| `src/core/cleaner.py` | Text clean/normalize | Lowercase, units (l/g/kg), prices, whitespace |
| `src/core/matcher.py` | ProductMatcher | Fuzzy match & deduplicate across stores |
| `src/pipeline/run_all.py` | Pipeline orchestrator | Coordinate scrapers, process, deduplicate, save |
| `src/utils/logger.py` | Logger utility | Unified ergonomic logging |

### Product Data Structure
```python
{
    "store": "ALDI",
    "name": "campina melk halfvolle 1l",  # cleaned, lowercase
    "brand": "Campina",
    "price": 1.29,
    "quantity": "1 L",
    "link": "https://...",
    "image_url": "..."  # optional
}
```

---

## Code Conventions

### Import Order
```python
# 1. Standard library
import json
from datetime import datetime

# 2. Third-party
from playwright.sync_api import sync_playwright

# 3. Local/relative
from ..core.extractor import ProductExtractor
from ..utils.logger import Logger
```

### Naming Conventions
- **Functions/variables**: `snake_case` → `clean_product_name()`, `load_all_products`
- **Classes**: `PascalCase` → `ProductExtractor`, `ProductMatcher`
- **Constants/URLs**: `UPPER_CASE` → `BASE_URL`, `URLS`

### Docstrings (Simple Style)
```python
def extract_aldi(item):
    """
    Extract product data from ALDI product tile.
    
    Args:
        item: Playwright element selector for product tile
        
    Returns:
        dict: Product data {brand, name, price, quantity, link}
    """
```

### Logging Pattern
```python
logger = Logger(__name__)
logger.start_scraping("ALDI")
logger.info("Scraping: https://...")
logger.debug("Parsed 42 products")
logger.warning("No more products found")
logger.error(f"Failed to parse: {e}")
```

### Error Handling Strategy
- **Item-level errors**: Silent skip (logged at debug level)
- **Pipeline-level errors**: Log and continue (never hard-fail)
- **JSON I/O**: Always UTF-8, no ASCII escaping (preserves Unicode)
- **Deduplication**: Handles missing fields gracefully

---

## Common Development Tasks

### Adding a New Scraper

1. **Create** `src/scrapers/newstore.py`:
   ```python
   from playwright.sync_api import sync_playwright
   from ..core.extractor import ProductExtractor
   from ..utils.logger import Logger
   
   def run():
       """Main scraper entry point."""
       all_data = []
       logger = Logger(__name__)
       logger.start_scraping("NewStore")
       
       with sync_playwright() as p:
           browser = p.chromium.launch(headless=True)
           page = browser.new_page()
           # Iterate pages, scrape, extract
           page.close()
           browser.close()
       
       logger.end_scraping("NewStore")
       return all_data
   
   def scrape_page(page, offset):
       """Extract products from a single page."""
       items = page.query_selector_all("css-selector")
       results = []
       for item in items:
           product = ProductExtractor.extract_newstore(item)
           results.append(product)
       return results
   ```

2. **Add extractor method** in `src/core/extractor.py`:
   ```python
   @staticmethod
   def extract_newstore(item):
       """Extract fields from NewStore product tile."""
       try:
           brand = item.query_selector("brand-selector").inner_text()
           name = item.query_selector("name-selector").inner_text()
           price_text = item.query_selector("price-selector").inner_text()
           
           product = {
               "store": "NewStore",
               "brand": brand,
               "name": name.lower(),
               "price": parse_price(price_text),
               "link": item.get_attribute("href"),
           }
           return product
       except Exception as e:
           return None
   ```

3. **Register in** `src/pipeline/run_all.py`:
   ```python
   from src.scrapers import newstore
   
   scrapers = [
       ("NewStore", newstore.run),  # Add this
       ("ALDI", aldi.run),
       # ...
   ]
   ```

4. **Test**: `python -m src.pipeline.run_all`

### Modifying Cleaning Rules

Edit `src/core/cleaner.py`:
```python
# Add/modify unit mappings:
unit_mappings = {
    r'\bliter\b|\bl\b': 'l',
    r'\bgram\b|\bg\b': 'g',
    r'\bkilogram\b|\bkg\b': 'kg',
    r'\bnewunit\b': 'nu',  # New rule
    # ...
}

# Or modify price/text cleaners directly
def clean_price(price_str):
    """Return float from price string."""
```

Test changes with `test_brand_extraction.py` (ad-hoc validation).

### Adjusting Deduplication Sensitivity

In `src/pipeline/run_all.py`, modify:
```python
# Threshold = minimum similarity ratio (0-1)
# 0.85 = 85% match required; raise to be stricter
process_and_deduplicate(threshold=0.85, price_threshold=0.10)
```

Also adjust price variance check: `price_threshold=0.10` means ±10% price difference allowed.

### Polite Scraping Configuration

Scrapers include 2–3 second delays between requests. Adjust per store:
```python
import time
time.sleep(2)  # Add before next page fetch
```

---

## Key Files Reference

| File | Why Know It |
|------|-----------|
| [src/pipeline/run_all.py](src/pipeline/run_all.py) | Full pipeline orchestration, output strategy |
| [src/scrapers/aldi.py](src/scrapers/aldi.py) | Exemplary scraper: CSS selectors, Playwright pattern, delays |
| [src/core/extractor.py](src/core/extractor.py) | How extraction per store works; add new `extract_*()` methods |
| [src/core/cleaner.py](src/core/cleaner.py) | All data normalization: units, prices, text cleaning |
| [src/core/matcher.py](src/core/matcher.py) | Deduplication algorithm: similarity thresholds |
| [src/utils/logger.py](src/utils/logger.py) | Logging utilities wrapper |
| [test_brand_extraction.py](test_brand_extraction.py) | Example standalone validation script |

**Legacy/Ignore for new work:**
- `clean_aldi.py`, `master_cleaner.py`, `master_cleaner_v2.py` — deprecated standalone versions

---

## Project Conventions

| Aspect | Standard |
|--------|----------|
| **Python version** | 3.x (uses f-strings, pathlib) |
| **Browser** | Playwright Chromium (headless) |
| **Polite scraping** | 2–3s delays between requests |
| **Output format** | JSON (UTF-8, indent=2, no ASCII escaping) |
| **Dedup algorithm** | SequenceMatcher fuzzy match `>= 0.85` similarity + price validation |
| **File versioning** | Timestamped output + `_latest.json` symlink |
| **Error strategy** | Silent skip item-level errors; log pipeline-level issues |
| **Testing** | Ad-hoc scripts (`test_*.py`); no formal test framework |
| **CI/CD** | Manual CLI runs; no automation configured |

---

## Common Patterns

### Playwright Page Navigation
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url)
    
    # Query elements
    items = page.query_selector_all(".product-card")
    for item in items:
        text = item.inner_text()
        href = item.get_attribute("href")
    
    page.close()
    browser.close()
```

### Logging Lifecycle
```python
logger = Logger(__name__)
logger.start_scraping("StoreName")

try:
    # Scrape logic
    logger.info(f"Scraped {count} products")
except Exception as e:
    logger.error(f"Scraping failed: {e}")
finally:
    logger.end_scraping("StoreName")
```

### Product Extraction Pattern
```python
@staticmethod
def extract_store(item):
    try:
        brand = item.query_selector(".brand").inner_text()
        name = clean_product_name(item.query_selector(".name").inner_text())
        price = clean_price(item.query_selector(".price").inner_text())
        
        return {
            "store": "StoreName",
            "brand": brand,
            "name": name,
            "price": price,
            "link": item.get_attribute("href"),
        }
    except Exception:
        return None  # Silent skip
```

---

## Extending the Project

### Next Steps (Frequent Tasks)
1. **Add new store support**: Follow "Adding a New Scraper" section
2. **Improve data cleaning**: Edit `src/core/cleaner.py` + test with `test_brand_extraction.py`
3. **Adjust dedup sensitivity**: Modify threshold in `run_all.py`
4. **Debug scraper failures**: Run individual scraper, inspect CSS selectors with browser dev tools

### Useful Commands for Development
```bash
# Lint/format (if tools available)
# python -m black src/

# Run single scraper with verbose output
python -m src.scrapers.aldi

# Full pipeline with dedup
python -m src.pipeline.run_all

# Inspect output
cat output/processed/all_stores_latest.json | head -20
```

---

## Questions? Issues?

- **CSS selectors broken**: Store website changed → inspect with browser DevTools, update selector in scraper
- **Cleaning rules too aggressive**: Adjust regexes in `src/core/cleaner.py`
- **Duplicates not merging**: Increase threshold in `src/pipeline/run_all.py` or improve matcher logic
- **New store needed**: Follow "Adding a New Scraper" pattern above

---

**Last Updated**: April 2026  
**Framework**: Playwright, Python 3.x  
**Team**: SaveBasket Scraper Contributors
