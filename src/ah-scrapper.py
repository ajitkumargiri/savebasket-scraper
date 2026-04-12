from playwright.sync_api import sync_playwright
import json
import os
import time

BASE_URL = "https://www.ah.nl/producten/1730/zuivel-eieren?page={}"
MAX_PAGES = 20


def scrape_page(page, page_num):
    url = BASE_URL.format(page_num)
    print(f"\nScraping page {page_num}...")

    page.goto(url, timeout=60000)

    # ✅ critical fix for AH
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(5000)

    # ✅ YOUR EXACT selector
    items = page.query_selector_all('[data-testid="product-card-vertical-container"]')

    print(f"Found {len(items)} products")

    data = []

    for item in items:
        try:
            # name
            name_el = item.query_selector('.product-card-content_title__VNanP')
            name = name_el.inner_text().strip() if name_el else ""

            # price
            whole_el = item.query_selector('.current-price_root__8Ka3V p')
            frac_el = item.query_selector('.current-price_cents__VCUS4')

            if whole_el and frac_el:
                price = float(f"{whole_el.inner_text().strip()}.{frac_el.inner_text().strip()}")
            else:
                price = None

            # unit
            unit_el = item.query_selector('[data-testid="product-card-price-description"]')
            unit = unit_el.inner_text().strip() if unit_el else ""

            # link
            link_el = item.query_selector('a.product-card-container_linkContainer__P3Zzz')
            link = link_el.get_attribute("href") if link_el else ""
            if link:
                link = "https://www.ah.nl" + link

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

        for page_num in range(1, MAX_PAGES + 1):
            data = scrape_page(page, page_num)

            if not data:
                print("No more data, stopping.")
                break

            all_data.extend(data)

            # ✅ small delay (avoid blocking)
            time.sleep(2)

        browser.close()

    # save file
    with open("output/ah.json", "w") as f:
        json.dump(all_data, f, indent=2)

    print(f"\n✅ Total products scraped: {len(all_data)}")


if __name__ == "__main__":
    run()
