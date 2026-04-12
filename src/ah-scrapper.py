from playwright.sync_api import sync_playwright
import json
import os
import time

BASE_URL = "https://www.ah.nl/producten/1730/zuivel-eieren?page={}"
MAX_PAGES = 10


def scrape_page(page, page_num):
    url = BASE_URL.format(page_num)
    print(f"Scraping page {page_num}...")

    page.goto(url)

    # ✅ IMPORTANT FIX (not selector issue)
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(8000)   # AH needs time

    # ✅ YOUR EXACT selector
    items = page.query_selector_all('[data-testid="product-card-vertical-container"]')

    print(f"Found {len(items)} products")

    data = []

    for item in items:
        try:
            # name
            name = item.query_selector(
                '.product-card-content_title__VNanP'
            ).inner_text().strip()

            # price
            whole = item.query_selector(
                '.current-price_root__8Ka3V p'
            ).inner_text().strip()

            frac = item.query_selector(
                '.current-price_cents__VCUS4'
            ).inner_text().strip()

            price = float(f"{whole}.{frac}")

            # unit
            unit_el = item.query_selector(
                '[data-testid="product-card-price-description"]'
            )
            unit = unit_el.inner_text().strip() if unit_el else ""

            # link
            link_el = item.query_selector(
                'a.product-card-container_linkContainer__P3Zzz'
            )
            link = link_el.get_attribute("href") if link_el else ""
            link = "https://www.ah.nl" + link if link else ""

            data.append({
                "name": name,
                "price": price,
                "unit": unit,
                "url": link
            })

        except Exception as e:
            continue

    return data


def run():
    os.makedirs("output", exist_ok=True)

    all_data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for i in range(1, MAX_PAGES + 1):
            data = scrape_page(page, i)

            if not data:
                print("No data, stopping")
                break

            all_data.extend(data)
            time.sleep(2)

        browser.close()

    with open("output/ah.json", "w") as f:
        json.dump(all_data, f, indent=2)

    print(f"Total products: {len(all_data)}")


if __name__ == "__main__":
    run()
