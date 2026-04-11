from playwright.sync_api import sync_playwright
import json
import os
import time
from datetime import datetime

BASE_URL = "https://www.jumbo.com/producten/zuivel,-eieren,-boter/?offSet={}"

STEP = 24
MAX_PAGES = 10  # increase later


def scrape_page(page, offset):
    url = BASE_URL.format(offset)
    print(f"\nScraping offset {offset}...")

    page.goto(url, timeout=60000)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(3000)

    items = page.query_selector_all("article.product-container")
    print(f"Found {len(items)} items")

    data = []

    for item in items:
        try:
            name_el = item.query_selector("h3")
            whole_el = item.query_selector(".whole")
            frac_el = item.query_selector(".fractional")
            link_el = item.query_selector("a[href]")
            img_el = item.query_selector("img")

            if not name_el or not whole_el or not frac_el:
                continue

            name = name_el.inner_text().strip()
            price = float(f"{whole_el.inner_text()}.{frac_el.inner_text()}")

            product_url = ""
            if link_el:
                href = link_el.get_attribute("href")
                if href:
                    product_url = "https://www.jumbo.com" + href

            image_url = ""
            if img_el:
                image_url = img_el.get_attribute("src")

            data.append({
                "store": "Jumbo",
                "name": name,
                "price": price,
                "product_url": product_url,
                "image_url": image_url
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

        for i in range(MAX_PAGES):
            offset = i * STEP

            data = scrape_page(page, offset)

            if not data:
                print("No more data → stopping")
                break

            all_data.extend(data)

            time.sleep(2)

        browser.close()

    # save
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"output/jumbo_{timestamp}.json"

    with open(filename, "w") as f:
        json.dump(all_data, f, indent=2)

    with open("output/jumbo_latest.json", "w") as f:
        json.dump(all_data, f, indent=2)

    print(f"\n✅ TOTAL PRODUCTS: {len(all_data)}")
    print(f"Saved: {filename}")


if __name__ == "__main__":
    run()
