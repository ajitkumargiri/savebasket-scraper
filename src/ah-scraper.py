from playwright.sync_api import sync_playwright
import json
import time
from datetime import datetime

BASE_URL = "https://www.ah.nl/producten/1730/zuivel-eieren?page={}"
MAX_PAGES = 50   # adjust if needed


def scrape_page(page, page_num):
    url = BASE_URL.format(page_num)
    print(f"\nScraping page {page_num}...")

    page.goto(url, timeout=60000)

    # wait for your exact selector
    try:
        page.wait_for_selector('[data-testid="product-card-vertical-container"]', timeout=60000)
    except:
        print("⚠️ No products found (maybe blocked or end)")
        return []

    items = page.query_selector_all('[data-testid="product-card-vertical-container"]')
    print(f"Found {len(items)} products")

    results = []

    for item in items:
        try:
            # name
            name_el = item.query_selector('p[data-testid="product-card-title"], p.typography_body-regular__Vnq4U')
            name = name_el.inner_text().strip() if name_el else None

            # price
            price_whole = item.query_selector('.current-price_root__8Ka3V p')
            price_decimal = item.query_selector('.current-price_cents__VCUS4')

            if price_whole and price_decimal:
                price = f"{price_whole.inner_text().strip()}.{price_decimal.inner_text().strip()}"
            else:
                price = None

            # size
            size_el = item.query_selector('[data-testid="product-card-price-description"]')
            size = size_el.inner_text().strip() if size_el else None

            # link
            link_el = item.query_selector('a[href]')
            link = "https://www.ah.nl" + link_el.get_attribute("href") if link_el else None

            # image
            img_el = item.query_selector('img')
            image = img_el.get_attribute("src") if img_el else None

            results.append({
                "name": name,
                "price": price,
                "size": size,
                "link": link,
                "image": image,
                "store": "AH"
            })

        except Exception as e:
            print("Error parsing item:", e)

    return results


def run():
    all_products = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,   # ✅ IMPORTANT FOR VPS
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

        for page_num in range(1, MAX_PAGES + 1):
            data = scrape_page(page, page_num)

            if not data:
                print("No more data, stopping.")
                break

            all_products.extend(data)

            time.sleep(2)  # avoid blocking

        browser.close()

    # save with timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"output/ah_{timestamp}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(all_products, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Saved {len(all_products)} products to {filename}")


if __name__ == "__main__":
    run()
