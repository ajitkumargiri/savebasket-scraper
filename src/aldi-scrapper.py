from playwright.sync_api import sync_playwright
import json, os, time
from datetime import datetime

URL = "https://www.aldi.nl/producten/zuivel-eieren-boter.html"

def run():
    os.makedirs("output", exist_ok=True)
    data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(URL)
        page.wait_for_load_state("domcontentloaded")

        # 🔥 CLICK LOAD MORE LOOP
        while True:
            try:
                button = page.query_selector("button:has-text('Meer laden')")
                if button:
                    button.click()
                    page.wait_for_timeout(2000)
                else:
                    break
            except:
                break

        items = page.query_selector_all("article")

        print(f"Found {len(items)} items")

        for item in items:
            try:
                name_el = item.query_selector("h3")
                price_el = item.query_selector('[class*="price"]')

                if not name_el or not price_el:
                    continue

                data.append({
                    "store": "Aldi",
                    "category": "dairy_eggs",
                    "name": name_el.inner_text().strip(),
                    "price": price_el.inner_text().strip()
                })
            except:
                continue

        browser.close()

    file = f"output/aldi_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.json"
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Saved {len(data)} products")


if __name__ == "__main__":
    run()
