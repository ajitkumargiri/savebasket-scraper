from playwright.sync_api import sync_playwright
import json, os, time
from datetime import datetime

URL = "https://www.ah.nl/producten/1730/zuivel-eieren"

def run():
    os.makedirs("output", exist_ok=True)
    all_data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(URL, timeout=60000)
        page.wait_for_load_state("domcontentloaded")

        # 🔥 SCROLL TO LOAD ALL PRODUCTS
        for _ in range(20):
            page.mouse.wheel(0, 5000)
            page.wait_for_timeout(2000)

        items = page.query_selector_all('[data-testhook="product-card"]')
        print(f"Found {len(items)} products")

        for item in items:
            try:
                name = item.query_selector('[data-testhook="product-title"]').inner_text()
                price = item.query_selector('[data-testhook="price"]').inner_text()

                all_data.append({
                    "store": "AH",
                    "category": "dairy_eggs",
                    "name": name.strip(),
                    "price": price.strip()
                })
            except:
                continue

        browser.close()

    file = f"output/ah_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.json"
    with open(file, "w") as f:
        json.dump(all_data, f, indent=2)

    print(f"Saved {len(all_data)} products")


if __name__ == "__main__":
    run()
