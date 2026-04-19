"""Vomar scraper using Playwright."""
import json
from datetime import datetime
from playwright.sync_api import sync_playwright

from ..core.extractor import ProductExtractor
from ..utils.logger import Logger


logger = Logger(__name__)

URL = "https://www.vomar.nl/producten/vers/zuivel-boter-eieren"


def run():
    """Main scraper runner."""
    data = []

    logger.start_scraping("Vomar")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        logger.info("Opening Vomar...")
        page.goto(URL, timeout=60000)

        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(3000)

        items = page.query_selector_all("div.product")
        logger.info(f"Found {len(items)} products")

        for item in items:
            try:
                product = ProductExtractor.extract_vomar(item)
                if product:
                    data.append(product)
            except Exception as e:
                logger.debug(f"Error parsing product: {e}")
                continue

        browser.close()

    # Save files
    os.makedirs("output/raw/vomar", exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"output/raw/vomar/vomar_{timestamp}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    with open("output/raw/vomar/vomar_latest.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    logger.end_scraping("Vomar", len(data))
    logger.info(f"📁 Saved: {filename}")
    logger.info("📌 Updated latest file")
    
    return data


if __name__ == "__main__":
    run()
