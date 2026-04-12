from playwright.sync_api import sync_playwright
import json, os
from datetime import datetime

URL = "https://www.vomar.nl/producten/vers/zuivel-boter-eieren"

def run():
    os.makedirs("output", exist_ok=True)
    data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(URL)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(3000)

        items = page.query_selector_all("article")

        print(f"Found {len(items)} items")

        for item in items:
            try:
                name_el = item.query_selector("h3")
                price_el = item.query_selector('[class*="price"]')

                if not name_el or not price_el:
                    continue

                data.append({
                    "store": "Vomar",
                    "category": "dairy_eggs",
                    "name": name_el.inner_text().strip(),
                    "price": price_el.inner_text().strip()
                })
            except:
                continue

        browser.close()

    file = f"output/vomar_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.json"
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Saved {len(data)} products")


if __name__ == "__main__":
    run()
