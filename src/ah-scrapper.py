from playwright.sync_api import sync_playwright
import json

def scrape_ah():

    url = "https://www.ah.nl/producten/1355/bakkerij"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("Opening page...")
        page.goto(url, timeout=60000)

        # wait for products
        page.wait_for_selector('[data-testhook="product-card"]')

        # scroll to load more
        for _ in range(6):
            page.mouse.wheel(0, 5000)
            page.wait_for_timeout(1500)

        items = page.query_selector_all('[data-testhook="product-card"]')

        print(f"Found {len(items)} products")

        data = []

        for item in items[:50]:
            try:
                name = item.query_selector('[data-testhook="product-title"]').inner_text()
                price = item.query_selector('[data-testhook="price"]').inner_text()

                data.append({
                    "store": "AH",
                    "category": "bakkerij",
                    "name": name.strip(),
                    "price": price.strip()
                })
            except:
                continue

        browser.close()

        return data


def run():
    data = scrape_ah()

    with open("ah_bakkerij.json", "w") as f:
        json.dump(data, f, indent=2)

    print(f"\nSaved {len(data)} products")


if __name__ == "__main__":
    run()
