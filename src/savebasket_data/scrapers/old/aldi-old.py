"""ALDI scraper using Playwright."""
import json
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

from ..core.extractor import ProductExtractor
from ..utils.logger import Logger


logger = Logger(__name__)


URLS = [
    "https://www.aldi.nl/producten/zuivel-eieren-boter/verse-zuivel.html",
    "https://www.aldi.nl/producten/zuivel-eieren-boter/eieren.html",
    "https://www.aldi.nl/producten/zuivel-eieren-boter/houdbare-zuviel.html",
    "https://www.aldi.nl/producten/zuivel-eieren-boter/plantaardige-zuivel.html",
    "https://www.aldi.nl/producten/zuivel-eieren-boter/boter-margarine.html"
]


def load_all_products(page):
    """Click 'Show more' button until all products are loaded."""
    logger.info("Loading all products...")
    
    clicks = 0
    while True:
        try:
            button = page.query_selector('[data-testid="product-tile-grid-load-more-button"]')

            if button:
                try:
                    button.scroll_into_view_if_needed()
                    button.click()
                    clicks += 1
                    logger.debug(f"Clicked 'Show more' (click #{clicks})")
                    time.sleep(2)
                except Exception as e:
                    logger.warning(f"Could not click button: {e}")
                    break
            else:
                logger.info(f"No more button found. Loaded {clicks} times")
                break

        except Exception as e:
            logger.warning(f"Error loading products: {e}")
            break


def scrape_page(page, url):
    """Scrape a single ALDI category page."""
    logger.info(f"Scraping: {url}")

    page.goto(url, timeout=60000)
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(3000)

    # load all products by clicking "show more"
    load_all_products(page)

    items = page.query_selector_all('.product-tile')
    logger.info(f"Found {len(items)} products")

    results = []

    for item in items:
        try:
            product = ProductExtractor.extract_aldi(item)
            
            # Only add if we have at least name and link
            if product.get('name') and product.get('link'):
                results.append(product)

        except Exception as e:
            logger.debug(f"Error parsing product: {e}")
            continue

    return results


def run():
    """Main scraper runner."""
    all_products = []

    logger.start_scraping("ALDI")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled"
            ]
        )

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )

        page = context.new_page()

        for i, url in enumerate(URLS, 1):
            data = scrape_page(page, url)
            all_products.extend(data)
            logger.progress(i, len(URLS), f"({len(all_products)} products so far)")

        browser.close()

    # Save files
    os.makedirs("output/raw/aldi", exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")

    filename = f"output/raw/aldi/aldi_{timestamp}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(all_products, f, indent=2, ensure_ascii=False)

    with open("output/raw/aldi/aldi_latest.json", "w", encoding="utf-8") as f:
        json.dump(all_products, f, indent=2, ensure_ascii=False)

    logger.end_scraping("ALDI", len(all_products))
    logger.info(f"📁 Saved to: {filename}")
    logger.info("📌 Updated: output/raw/aldi/aldi_latest.json")
    
    return all_products


if __name__ == "__main__":
    run()
