from playwright.sync_api import sync_playwright
import json
import os
import time
from datetime import datetime

# ✅ CATEGORY: dairy / eggs / butter
BASE_URL = "https://www.jumbo.com/producten/zuivel,-eieren,-boter/?offSet={}"

STEP = 24  # products per page


def scrape_page(page, offset):
    url = BASE_URL.format(offset)
    print(f"\nScraping offset {offset}...")

    try:
        page.goto(url, timeout=60000)
    except:
        print("Retrying page load...")
        page.goto(url, timeout=60000)

    # ✅ DO NOT USE networkidle
    page.wait_for_load_state("domcontentloaded")

    # ✅ wait for actual products
    try:
        page.wait_for_selector("article.product-container", timeout=60000)
    except:
        print("No products found → likely end")
        return []

    page.wait_for_timeout(2000)

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
            price = float(f"{whole_el.inner_text().strip()}.{frac_el.inner_text().strip()}")

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
                "category": "dairy_eggs",
                "name": name,
                "price": price,
                "currency": "EUR",
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
    offset = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        while True:
            data = scrape_page(page, offset)

            # ✅ stop automatically when no more products
            if not data:
                print("\nNo more products → stopping")
                break

            all_data.extend(data)

            offset += STEP
            time.sleep(2)  # polite scraping

        browser.close()

    # ✅ SAVE FILES
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"output/jumbo_dairy_{timestamp}.json"

    with open(filename, "w") as f:
        json.dump(all_data, f, indent=2)

    with open("output/jumbo_dairy_latest.json", "w") as f:
        json.dump(all_data, f, indent=2)

    print(f"\n✅ TOTAL PRODUCTS: {len(all_data)}")
    print(f"📁 Saved: {filename}")
    print("📌 Updated latest file")


if __name__ == "__main__":
    run()
