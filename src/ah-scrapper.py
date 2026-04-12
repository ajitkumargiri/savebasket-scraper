from playwright.sync_api import sync_playwright
import json, os, time
from datetime import datetime

BASE_URL = "https://www.ah.nl/producten/1730/zuivel-eieren?page={}"
MAX_PAGES = 10  # increase later


def scrape_page(page, page_num):
    url = BASE_URL.format(page_num)
    print(f"\nScraping page {page_num}...")

    page.goto(url, timeout=60000)

    # ✅ IMPORTANT
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_selector('[data-testid="product-card-vertical-container"]', timeout=60000)

    items = page.query_selector_all('[data-testid="product-card-vertical-container"]')
    print(f"Found {len(items)} items")

    data = []

    for item in items:
        try:
            name_el = item.query_selector('.product-card-content_title__VNanP')
            whole_el = item.query_selector('[data-testid="product-card-current-price"] p')
            frac_el = item.query_selector('[data-testid="product-card-current-price"] sup')
            unit_el = item.query_selector('[data-testid="product-card-price-description"]')
            link_el = item.query_selector("a[href]")
            img_el = item.query_selector("img")

            if not name_el or not whole_el or not frac_el:
                continue

            name = name_el.inner_text().strip()
            price = float(f"{whole_el.inner_text().strip()}.{frac_el.inner_text().strip()}")

            unit = unit_el.inner_text().strip() if unit_el else ""

            product_url = ""
            if link_el:
                href = link_el.get_attribute("href")
                if href:
                    product_url = "https://www.ah.nl" + href

            image_url = img_el.get_attribute("src") if img_el else ""

            data.append({
                "store": "AH",
                "category": "dairy_eggs",
                "name": name,
                "price": price,
                "unit": unit,
                "product_url": product_url,
                "image_url": image_url,
                "scraped_at": datetime.now().isoformat()
            })

        except:
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

            # ✅ STOP CONDITION
            if not data:
                print("No more data → stopping")
                break

            all_data.extend(data)

            time.sleep(2)

        browser.close()

    # SAVE
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    file = f"output/ah_dairy_{timestamp}.json"

    with open(file, "w") as f:
        json.dump(all_data, f, indent=2)

    with open("output/ah_dairy_latest.json", "w") as f:
        json.dump(all_data, f, indent=2)

    print(f"\n✅ TOTAL PRODUCTS: {len(all_data)}")
    print(f"📁 {file}")


if __name__ == "__main__":
    run()
