from playwright.sync_api import sync_playwright
import json
import os
import time
from datetime import datetime

BASE_URL = "https://www.ah.nl/producten/1730/zuivel-eieren?page={}"
MAX_PAGES = 20   # increase later


def scrape_page(page, page_num):
    url = BASE_URL.format(page_num)
    print(f"\n🔎 Scraping page {page_num}...")

    page.goto(url, timeout=60000)

    # ✅ Accept cookies
    try:
        page.click('button:has-text("Akkoord")', timeout=5000)
        print("✔ Cookies accepted")
    except:
        pass

    # ✅ Wait for page load
    page.wait_for_load_state("domcontentloaded")

    # ✅ IMPORTANT: wait for carousel (parent container)
    try:
        page.wait_for_selector('div[class*="carousel"]', timeout=60000)
    except:
        print("⚠ Carousel not found")

    # buffer for JS rendering
    page.wait_for_timeout(4000)

    # ✅ Your correct selector
    items = page.query_selector_all('[data-testid="product-card-vertical-container"]')

    print(f"✔ Found {len(items)} products")

    data = []

    for item in items:
        try:
            # name
            name_el = item.query_selector('.product-card-content_title__VNanP')

            # price
            whole_el = item.query_selector('[data-testid="product-card-current-price"] p')
            frac_el = item.query_selector('[data-testid="product-card-current-price"] sup')

            # unit
            unit_el = item.query_selector('[data-testid="product-card-price-description"]')

            # link
            link_el = item.query_selector("a[href]")

            # image
            # ✅ Stop when no more data
            if not data:
                print("🛑 No more products → stopping")
                break

            all_data.extend(data)

            # polite delay
            time.sleep(2)

        browser.close()

    # ✅ Save with timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    file_name = f"output/ah_dairy_{timestamp}.json"

    with open(file_name, "w") as f:
        json.dump(all_data, f, indent=2)

    # latest file
    with open("output/ah_dairy_latest.json", "w") as f:
        json.dump(all_data, f, indent=2)

    print("\n========================")
    print(f"✅ TOTAL PRODUCTS: {len(all_data)}")
    print(f"📁 Saved: {file_name}")
    print("========================")


if __name__ == "__main__":
    run()
