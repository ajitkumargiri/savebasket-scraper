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

        print("Opening Vomar...")
        page.goto(URL, timeout=60000)

        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(3000)

        items = page.query_selector_all("div.product")
        print(f"Found {len(items)} products")

        for item in items:
            try:
                # NAME
                name_el = item.query_selector(".description")

                # PRICE
                whole_el = item.query_selector(".large")
                frac_el = item.query_selector(".small")

                # LINK
                link_el = item.query_selector("a")

                # IMAGE
                img_el = item.query_selector("img")

                if not name_el or not whole_el or not frac_el:
                    continue

                name = name_el.inner_text().strip()

                price = float(
                    f"{whole_el.inner_text().replace('.', '').strip()}."
                    f"{frac_el.inner_text().strip()}"
                )

                product_url = ""
                if link_el:
                    href = link_el.get_attribute("href")
                    if href:
                        product_url = "https://www.vomar.nl" + href

                image_url = img_el.get_attribute("src") if img_el else ""

                data.append({
                    "store": "Vomar",
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

        browser.close()

    # SAVE
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    file = f"output/vomar_dairy_{timestamp}.json"

    with open(file, "w") as f:
        json.dump(data, f, indent=2)

    with open("output/vomar_dairy_latest.json", "w") as f:
        json.dump(data, f, indent=2)

    print(f"\n✅ Saved {len(data)} products")
    print(f"📁 {file}")


if __name__ == "__main__":
    run()
