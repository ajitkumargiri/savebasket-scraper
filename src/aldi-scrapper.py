from playwright.sync_api import sync_playwright
import json
import time
from datetime import datetime


URLS = [
    "https://www.aldi.nl/producten/zuivel-eieren-boter/verse-zuivel.html",
    "https://www.aldi.nl/producten/zuivel-eieren-boter/eieren.html",
    "https://www.aldi.nl/producten/zuivel-eieren-boter/houdbare-zuviel.html",
    "https://www.aldi.nl/producten/zuivel-eieren-boter/plantaardige-zuivel.html",
    "https://www.aldi.nl/producten/zuivel-eieren-boter/boter-margarine.html"
]


def load_all_products(page):
    print("Loading all products...")

    while True:
        try:
            button = page.query_selector('[data-testid="product-tile-grid-load-more-button"]')

            if button:
                button.click()
                print("Clicked 'Show more'")
                time.sleep(2)
            else:
                print("No more button found")
                break

        except:
            print("Finished loading all")
            break


def scrape_page(page, url):
    print(f"\nScraping: {url}")

    page.goto(url, timeout=60000)
    page.wait_for_timeout(5000)

    # load all products
    load_all_products(page)

    items = page.query_selector_all('.product-tile')
    print(f"Found {len(items)} products")

    results = []

    for item in items:
        try:
            # brand
            brand_el = item.query_selector('.product-tile__content__upper__brand-name')
            brand = brand_el.inner_text().strip() if brand_el else None

            # name
            name_el = item.query_selector('.product-tile__content__upper__product-name')
            name = name_el.inner_text().strip() if name_el else None

            # price
            price_el = item.query_selector('.tag__label--price')
            price = price_el.inner_text().strip() if price_el else None

            # size
            size_el = item.query_selector('.tag__marker--salesunit')
            size = size_el.inner_text().strip() if size_el else None

            # link
            link_el = item.query_selector('a.product-tile__action')
            link = "https://www.aldi.nl" + link_el.get_attribute("href") if link_el else None

            # image
            img_el = item.query_selector('img')
            image = img_el.get_attribute("src") if img_el else None

            results.append({
                "brand": brand,
                "name": name,
                "price": price,
                "size": size,
                "link": link,
                "image": image,
                "store": "ALDI"
            })

        except Exception as e:
            print("Error:", e)

    return results


def run():
    all_products = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,   # VPS safe
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )

        page = context.new_page()

        for url in URLS:
            data = scrape_page(page, url)
            all_products.extend(data)

        browser.close()

    # save file
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"output/aldi_{timestamp}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(all_products, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Saved {len(all_products)} products to {filename}")


if __name__ == "__main__":
    run()
