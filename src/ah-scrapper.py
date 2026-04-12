from playwright.sync_api import sync_playwright
import json
import os
import time

BASE_URL = "https://www.ah.nl/producten/1730/zuivel-eieren?page={}"
MAX_PAGES = 20


def scrape_page(page, page_num):
    url = BASE_URL.format(page_num)
    print(f"\nScraping page {page_num}...")

    page.goto(url, timeout=60000)

    # ✅ wait + behave like real user
    page.wait_for_timeout(8000)

    # scroll to trigger lazy load
    page.mouse.wheel(0, 3000)
    page.wait_for_timeout(3000)

    # ✅ YOUR selector (correct)
    items = page.query_selector_all('[data-testid="product-card-vertical-container"]')

    print(f"Found {len(items)} products")

    data = []

    for item in items:
        try:
            # name
            name_el = item.query_selector('.product-card-content_title__VNanP')
            name = name_el.inner_text().strip() if name_el else ""

            # price
            whole_el = item.query_selector('.current-price_root__8Ka3V p')
            frac_el = item.query_selector('.current-price_cents__VCUS4')

            if whole_el and frac_el:
                price = float(f"{whole_el.inner_text().strip()}.{frac_el.inner_text().strip()}")
            else:
                price = None

            # unit
            unit_el = item.query_selector('[data-testid="product-card-price-description"]')
            unit = unit_el.inner_text().strip() if unit_el else ""

            # link
            link_el = item.query_selector('a.product-card-container_linkContainer__P3Zzz')
            link = link_el.get_attribute("href") if link_el else ""
            if link:
                link = "https://www.ah.nl" + link

            data.append({
                "name": name,
                "price": price,
                "unit": unit,
                "url": link
            })

        except Exception:
            continue

    return data


def run():
    os.makedirs("output", exist_ok=True)
    all_data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,  # 🔥 important to bypass blocking
            args=[
                "--no-sandbox",
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

            all_data.extend(data)
            time.sleep(2)

        browser.close()

    with open("output/ah.json", "w") as f:
        json.dump(all_data, f, indent=2)

    print(f"\n✅ Total products scraped: {len(all_data)}")


if __name__ == "__main__":
    run()

Regards,
Ajit Giri
+31-685254581

On Sun, Apr 12, 2026, 4:53 PM Ajit Kumar Giri <ajitkugiri@gmail.com> wrote:
from playwright.sync_api import sync_playwright
import json
import os
import time

BASE_URL = "https://www.ah.nl/producten/1730/zuivel-eieren?page={}"
MAX_PAGES = 20


def scrape_page(page, page_num):
    url = BASE_URL.format(page_num)
    print(f"\nScraping page {page_num}...")

    page.goto(url, timeout=60000)

    # ✅ critical fix for AH
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(5000)

    # ✅ YOUR EXACT selector
    items = page.query_selector_all('[data-testid="product-card-vertical-container"]')

    print(f"Found {len(items)} products")

    data = []

    for item in items:
        try:
            # name
            name_el = item.query_selector('.product-card-content_title__VNanP')
            name = name_el.inner_text().strip() if name_el else ""

            # price
            whole_el = item.query_selector('.current-price_root__8Ka3V p')
            frac_el = item.query_selector('.current-price_cents__VCUS4')

            if whole_el and frac_el:
                price = float(f"{whole_el.inner_text().strip()}.{frac_el.inner_text().strip()}")
            else:
                price = None

            # unit
            unit_el = item.query_selector('[data-testid="product-card-price-description"]')
            unit = unit_el.inner_text().strip() if unit_el else ""

            # link
            link_el = item.query_selector('a.product-card-container_linkContainer__P3Zzz')
            link = link_el.get_attribute("href") if link_el else ""
            if link:
                link = "https://www.ah.nl" + link

            data.append({
                "name": name,
                "price": price,
                "unit": unit,
                "url": link
            })

        except Exception as e:
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

            if not data:
                print("No more data, stopping.")
                break

            all_data.extend(data)

            # ✅ small delay (avoid blocking)
            time.sleep(2)

        browser.close()

    # save file
    with open("output/ah.json", "w") as f:
        json.dump(all_data, f, indent=2)

    print(f"\n✅ Total products scraped: {len(all_data)}")


if __name__ == "__main__":
    run()

Regards,
Ajit Giri
+31-685254581

On Sun, Apr 12, 2026, 4:47 PM Ajit Kumar Giri <ajitkugiri@gmail.com> wrote:
from playwright.sync_api import sync_playwright
import json
import os
import time

BASE_URL = "https://www.ah.nl/producten/1730/zuivel-eieren?page={}"
MAX_PAGES = 10


def scrape_page(page, page_num):
    url = BASE_URL.format(page_num)
    print(f"Scraping page {page_num}...")

    page.goto(url)

    # ✅ IMPORTANT FIX (not selector issue)
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(8000)   # AH needs time

    # ✅ YOUR EXACT selector
    items = page.query_selector_all('[data-testid="product-card-vertical-container"]')

    print(f"Found {len(items)} products")

    data = []

    for item in items:
        try:
            # name
            name = item.query_selector(
                '.product-card-content_title__VNanP'
            ).inner_text().strip()

            # price
            whole = item.query_selector(
                '.current-price_root__8Ka3V p'
            ).inner_text().strip()

            frac = item.query_selector(
                '.current-price_cents__VCUS4'
            ).inner_text().strip()

            price = float(f"{whole}.{frac}")

            # unit
            unit_el = item.query_selector(
                '[data-testid="product-card-price-description"]'
            )
            unit = unit_el.inner_text().strip() if unit_el else ""

            # link
            link_el = item.query_selector(
                'a.product-card-container_linkContainer__P3Zzz'
            )
            link = link_el.get_attribute("href") if link_el else ""
            link = "https://www.ah.nl" + link if link else ""

            data.append({
                "name": name,
                "price": price,
                "unit": unit,
                "url": link
            })

        except Exception as e:
            continue

    return data


def run():
    os.makedirs("output", exist_ok=True)

    all_data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for i in range(1, MAX_PAGES + 1):
            data = scrape_page(page, i)

            if not data:
                print("No data, stopping")
                break

            all_data.extend(data)
            time.sleep(2)

        browser.close()

    with open("output/ah.json", "w") as f:
        json.dump(all_data, f, indent=2)

    print(f"Total products: {len(all_data)}")


if __name__ == "__main__":
    run()

Regards,
Ajit Giri
+31-685254581

On Sun, Apr 12, 2026, 4:39 PM Ajit Kumar Giri <ajitkugiri@gmail.com> wrote:
from playwright.sync_api import sync_playwright
import json
import os
import time
from datetime import datetime

BASE_URL = "https://www.ah.nl/producten/1730/zuivel-eieren?page={}"
MAX_PAGES = 20   # increase later


def scrape_page(page, page_num):
    url = BASE_URL.format(page_num)
    print(f"\n🔎 Scraping page {page_num}...")

    page.goto(url, timeout=60000)

    # ✅ Accept cookies
    try:
        page.click('button:has-text("Akkoord")', timeout=5000)
        print("✔ Cookies accepted")
    except:
        pass

    # ✅ Wait for page load
    page.wait_for_load_state("domcontentloaded")

    # ✅ IMPORTANT: wait for carousel (parent container)
    try:
        page.wait_for_selector('div[class*="carousel"]', timeout=60000)
    except:
        print("⚠ Carousel not found")

    # buffer for JS rendering
    page.wait_for_timeout(4000)

    # ✅ Your correct selector
    items = page.query_selector_all('[data-testid="product-card-vertical-container"]')

    print(f"✔ Found {len(items)} products")

    data = []

    for item in items:
        try:
            # name
            name_el = item.query_selector('.product-card-content_title__VNanP')

            # price
            whole_el = item.query_selector('[data-testid="product-card-current-price"] p')
            frac_el = item.query_selector('[data-testid="product-card-current-price"] sup')

            # unit
            unit_el = item.query_selector('[data-testid="product-card-price-description"]')

            # link
            link_el = item.query_selector("a[href]")

            # image
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

            # ✅ Stop when no more data
            if not data:
                print("🛑 No more products → stopping")
                break

            all_data.extend(data)

            # polite delay
            time.sleep(2)

        browser.close()

    # ✅ Save with timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    file_name = f"output/ah_dairy_{timestamp}.json"

    with open(file_name, "w") as f:
        json.dump(all_data, f, indent=2)

    # latest file
    with open("output/ah_dairy_latest.json", "w") as f:
        json.dump(all_data, f, indent=2)

    print("\n========================")
    print(f"✅ TOTAL PRODUCTS: {len(all_data)}")
    print(f"📁 Saved: {file_name}")
    print("========================")


if __name__ == "__main__":
    run()

Regards,
Ajit Giri
+31-685254581

On Sun, Apr 12, 2026, 4:28 PM Ajit Kumar Giri <ajitkugiri@gmail.com> wrote:
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

Regards,
Ajit Giri
+31-685254581

On Sun, Apr 12, 2026, 4:14 PM Ajit Kumar Giri <ajitkugiri@gmail.com> wrote:
from playwright.sync_api import sync_playwright
import json, os, time
from datetime import datetime

URL = "https://www.ah.nl/producten/1730/zuivel-eieren"


def run():
    os.makedirs("output", exist_ok=True)
    data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(URL, timeout=60000)
        page.wait_for_load_state("domcontentloaded")

        # 🔥 SCROLL (IMPORTANT)
        for _ in range(25):
            page.mouse.wheel(0, 5000)
            page.wait_for_timeout(1500)

        items = page.query_selector_all('[data-testid="product-card-vertical-container"]')
        print(f"Found {len(items)} products")

        for item in items:
            try:
                # NAME
                name_el = item.query_selector('.product-card-content_title__VNanP')

                # PRICE
                whole_el = item.query_selector('[data-testid="product-card-current-price"] p')
                frac_el = item.query_selector('[data-testid="product-card-current-price"] sup')

                # UNIT
                unit_el = item.query_selector('[data-testid="product-card-price-description"]')

                # LINK
                link_el = item.query_selector("a[href]")

                # IMAGE
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

        browser.close()

    # SAVE
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    file = f"output/ah_dairy_{timestamp}.json"

    with open(file, "w") as f:
        json.dump(data, f, indent=2)

    with open("output/ah_dairy_latest.json", "w") as f:
        json.dump(data, f, indent=2)

    print(f"\n✅ Saved {len(data)} products")
    print(f"📁 {file}")


if __name__ == "__main__":
    run()

Regards,
Ajit Giri
+31-685254581

On Sun, Apr 12, 2026, 4:11 PM Ajit Kumar Giri <ajitkugiri@gmail.com> wrote:
<div class="carousel_carouselItem__yFMoV product-lane_carouselItem__dRaBI"><div class="product-card_refWrapper__3SJXA"><div class="product-card-container_verticalContainer__oloJT product-lane_productCard__5CRJ4" role="group" data-testid="product-card-vertical-container" data-card-layout="vertical" id="_r_2c_"><a class="product-card-container_linkContainer__P3Zzz product-card-vertical-templates_linkContainer__LrMTl" href="/producten/product/wi583038/xxl-nutrition-fit-yoghurt-protein-strawberry" tabindex="0" aria-label="XXL Nutrition Fit yoghurt protein strawberry, Nutri-Score A, 200 grams €1.99, Vegetarian" target="_self"></a><div class="product-card-container_verticalImageContainer___qYU8" data-product-card-image-container="true"><div class="product-card-container_verticalHighlightImageContainer__Li3FJ" data-testid="product-card-highlight-image-container"><svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 60 32" height="32" width="60" aria-label="Nutri-Score A" size="50"><path fill="#fff" d="M53.176.007h-46.3a6.95 6.95 0 0 0-4.86 1.978A6.69 6.69 0 0 0 0 6.75v18.41C0 28.926 3.378 32 7.537 32h.759a8.04 8.04 0 0 0 4.06-1.087h40.767a6.95 6.95 0 0 0 4.863-1.98A6.69 6.69 0 0 0 60 24.162V6.744a6.69 6.69 0 0 0-2.016-4.767A6.95 6.95 0 0 0 53.124 0"></path><path fill="#E53312" d="M53.176 28.516h-6.588V10.92h6.588c1.175 0 2.301.457 3.132 1.27a4.3 4.3 0 0 1 1.301 3.07v8.932a4.3 4.3 0 0 1-1.3 3.069 4.48 4.48 0 0 1-3.133 1.27"></path><path fill="#fff" d="M54.634 15.81h-5.078v7.846h5.13v-1.184h-3.582v-2.307h2.505V18.98h-2.505v-1.987h3.53z" opacity="0.4"></path><path fill="#7C7B7B" d="M5.844 4.883V7.28h-.986V3.082h.774l1.996 2.463V3.082h.987V7.28h-.797zm5.42 1.571a.9.9 0 0 0 .432-.105.8.8 0 0 0 .281-.275q.11-.184.152-.395a2.2 2.2 0 0 0 .046-.446V3.097h.986v2.15q-.004.422-.121.827a1.8 1.8 0 0 1-.35.662 1.5 1.5 0 0 1-.584.447c-.27.116-.563.172-.857.164-.3.007-.599-.052-.873-.171a1.5 1.5 0 0 1-.585-.462 1.8 1.8 0 0 1-.334-.662 3 3 0 0 1-.106-.79V3.098h.987v2.15a1.8 1.8 0 0 0 .053.462q.044.206.152.387a.9.9 0 0 0 .28.276c.13.07.278.103.426.096m5.935-2.531h-1.298V7.28H14.9V3.938h-1.313v-.856h3.598zm1.48 1.146h.903a.4.4 0 0 0 .304-.164.67.67 0 0 0 .121-.417.58.58 0 0 0-.144-.417.4.4 0 0 0-.311-.148h-.873zm-.994 2.233v-4.22h1.935a1.36 1.36 0 0 1 .994.454c.128.13.229.285.297.454.067.163.104.337.106.513q.001.19-.053.372a1.3 1.3 0 0 1-.137.343q-.088.158-.22.283a1.2 1.2 0 0 1-.288.223l.979 1.556h-1.116l-.858-1.355h-.645v1.355zm5.093-4.235h-.987V7.28h.987zm2.596 2.151h-1.86v.848h1.86zm3.301-.923-.136-.082a2.2 2.2 0 0 0-.63-.26 1.3 1.3 0 0 0-.38-.053.73.73 0 0 0-.395.082.29.29 0 0 0-.128.26l.053.18a.5.5 0 0 0 .174.126q.135.066.281.104l.38.104q.305.088.554.186.233.084.425.239a1 1 0 0 1 .265.357c.065.156.096.323.091.491.006.208-.038.415-.129.603-.086.16-.21.295-.364.395a1.4 1.4 0 0 1-.516.216q-.295.075-.6.074a3.5 3.5 0 0 1-.956-.141 3 3 0 0 1-.456-.164 2 2 0 0 1-.41-.216l.433-.849.16.112q.155.098.326.164.21.09.433.149.241.066.493.067.525 0 .524-.313a.28.28 0 0 0-.076-.194.9.9 0 0 0-.22-.141 1.7 1.7 0 0 0-.327-.112l-.41-.119a4 4 0 0 1-.508-.193 1.3 1.3 0 0 1-.364-.238.85.85 0 0 1-.213-.313 1.32 1.32 0 0 1 .053-1.005c.081-.164.198-.309.342-.424q.229-.18.508-.268.298-.081.608-.082.221-.004.44.037l.417.104.372.15c.114.059.22.11.311.17zm.888.84a2.17 2.17 0 0 1 .539-1.414c.184-.198.406-.36.653-.476.272-.129.571-.193.873-.186a1.95 1.95 0 0 1 .994.253c.267.16.483.389.623.663l-.76.52a.9.9 0 0 0-.166-.275 1.2 1.2 0 0 0-.22-.178.9.9 0 0 0-.251-.09 1 1 0 0 0-.25 0 .9.9 0 0 0-.456.112 1 1 0 0 0-.319.29 1.4 1.4 0 0 0-.19.402q-.063.222-.06.454-.003.249.076.484.064.22.205.402c.088.117.203.214.334.283.13.07.276.105.425.104a1 1 0 0 0 .25 0q.133-.038.25-.104a.8.8 0 0 0 .22-.179.7.7 0 0 0 .153-.268l.812.47a1.2 1.2 0 0 1-.281.416 1.7 1.7 0 0 1-.418.305 2.2 2.2 0 0 1-.493.186 2 2 0 0 1-.516.067 1.8 1.8 0 0 1-.82-.186 2.3 2.3 0 0 1-.637-.49 2.34 2.34 0 0 1-.57-1.49m4.964-.037q0 .24.069.47.064.22.197.409c.088.114.2.21.326.282a1 1 0 0 0 .448.105.9.9 0 0 0 .456-.112 1 1 0 0 0 .318-.29q.133-.19.198-.41.06-.23.06-.469t-.068-.469a1.3 1.3 0 0 0-.205-.402 1 1 0 0 0-.326-.275.93.93 0 0 0-.44-.104.9.9 0 0 0-.448.111 1.1 1.1 0 0 0-.327.283 1.4 1.4 0 0 0-.197.41q-.06.227-.06.461Zm1.033 2.13a1.8 1.8 0 0 1-.835-.187 2.2 2.2 0 0 1-.645-.476 2.2 2.2 0 0 1-.41-.685 2.2 2.2 0 0 1 0-1.593c.104-.248.25-.477.432-.678.183-.196.405-.354.653-.461a1.9 1.9 0 0 1 .82-.179c.29-.004.576.06.835.186.243.118.46.283.637.484.18.202.322.434.418.685.089.239.137.49.144.744 0 .274-.054.544-.16.797a2.1 2.1 0 0 1-1.07 1.146c-.255.12-.536.182-.82.179m3.613-2.196h.904a.4.4 0 0 0 .303-.164.67.67 0 0 0 .13-.417.59.59 0 0 0-.29-.526.4.4 0 0 0-.174-.04h-.873zm-.986 2.233v-4.22h1.928c.192-.001.382.042.554.126a1.49 1.49 0 0 1 .736.782c.072.162.108.337.106.513q0 .189-.045.372a1.5 1.5 0 0 1-.137.343 1.36 1.36 0 0 1-.516.506l.98 1.556h-1.11l-.864-1.355h-.645v1.355zm7.104-.886v.849H42.27V3.082h2.953v.856h-1.966v.811h1.693v.79h-1.693v.892h2.02Z"></path><path fill="#86BC25" d="M24.524 10.92h-9.61a6.25 6.25 0 0 1 .98 3.35v10.897a6.27 6.27 0 0 1-.98 3.35h9.61z"></path><path fill="#FC0" d="M35.56 10.912H24.53V28.51h11.03z"></path><path fill="#EF7D00" d="M46.588 10.912H35.56V28.51h11.028z"></path><path fill="#fff" d="M19.507 15.81h-2.194v7.846h2.475c2.33 0 3.278-.923 3.278-2.33 0-.393-.13-.775-.371-1.09a1.85 1.85 0 0 0-.964-.652c.27-.192.49-.444.643-.735a2.06 2.06 0 0 0 .237-.94c0-1.153-.835-2.099-3.104-2.099m-.646 3.35v-2.166h.456c1.222 0 1.715.35 1.715 1.057s-.47 1.087-1.465 1.101zm0 3.312V20.24h.76c1.411 0 1.867.417 1.867 1.072 0 .804-.6 1.146-1.776 1.146l-.85.015Zm11.363-6.781c-2.14 0-3.795 1.57-3.795 4.027s1.518 4.05 3.795 4.05a3.5 3.5 0 0 0 1.84-.382 3.4 3.4 0 0 0 1.363-1.271l-1.154-.826a2.25 2.25 0 0 1-.831.85c-.35.206-.75.316-1.157.318-1.473 0-2.277-.997-2.277-2.746 0-1.638.842-2.71 2.148-2.71.38-.016.758.085 1.078.289s.566.502.705.85l1.473-.536a3.06 3.06 0 0 0-1.274-1.484 3.15 3.15 0 0 0-1.93-.429m10.308.119h-2.429v7.846h2.277c2.862 0 4.6-1.675 4.6-3.923 0-2.456-1.617-3.923-4.425-3.923zm-.91 6.64v-5.434h.865c1.92 0 2.846.998 2.846 2.717 0 1.563-1.002 2.74-3.036 2.74z" opacity="0.4"></path><path fill="#00803D" d="M8.35 30.712h-.76c-3.438 0-6.224-2.479-6.224-5.545V14.262c0-3.067 2.786-5.553 6.224-5.553h.76c3.438 0 6.223 2.486 6.223 5.553v10.897c0 3.067-2.786 5.546-6.224 5.546"></path><path fill="#fff" d="M6.861 20.708H9.04l-1.063-3.305zm-3.855 3.819L6.96 14.106h2.178l3.925 10.42h-2.794l-.53-1.682H6.132l-.57 1.683H3.007Z"></path></svg></div><img alt="XXL Nutrition Fit yogurt protein strawberry" class="image_root__ykCAj image_fit__qJY4e product-card-container_verticalImage__Tzh0_" aria-hidden="true" src="https://static.ah.nl/dam/product/AHI_54697355335f4561537653763878395a397876496677?revLabel=1&amp;rendition=200x200_JPG_Q85&amp;fileType=binary"><div class="product-card-vertical-templates_verticalPriceContainer__jPEgf"><div><div class="price_root___8pvy price_vertical__RpjUn price_right__w7awq product-card-content_price___8IYP product-card-content_showPrice__vGEL_" tabindex="-1" aria-labelledby="" data-testid="product-card-price"><div aria-label="for 1 euro and 99 cents" class="current-price_root__8Ka3V current-price_price-3___i_Jr price_currentPrice__NNwwe price_vertical__RpjUn" role="definition" id="current-price-_r_2d_" data-testid="product-card-current-price"><p><font dir="auto" style="vertical-align: inherit;"><font dir="auto" style="vertical-align: inherit;">1</font></font></p><div aria-hidden="true" class="current-price_centsWrapper__4RRHe"><p aria-hidden="true" class="current-price_separator__NNp20"><font dir="auto" style="vertical-align: inherit;"><font dir="auto" style="vertical-align: inherit;">.</font></font></p><sup aria-hidden="true" class="current-price_cents__VCUS4 current-price_price-superscript-3__gqt5W"><font dir="auto" style="vertical-align: inherit;"><font dir="auto" style="vertical-align: inherit;">99</font></font></sup></div></div><div class="price_additionalPriceInfo__79E1M price_vertical__RpjUn price_right__w7awq"><div class="price_originalPrice__GdZu8 price_right__w7awq price_vertical__RpjUn"></div></div><p class="typography_typography__wxrkf typography_subtext-regular__gXZlN typography_align-left__vfMmn description_description__7EJNy price_verticalDescription__GOSVK" id="price-description-_r_2d_" aria-label="200 grams" data-testid="product-card-price-description"><font dir="auto" style="vertical-align: inherit;"><font dir="auto" style="vertical-align: inherit;">200 g</font></font></p></div></div></div><div class="product-card-container_verticalLogoLabelContainer___OuAq product-card-container_verticalProductLogoLabelContainerPosition__W5oit" data-testid="product-card-logo-label-container"><div class="product-card-container_productLogoContainer__VnA4f" data-testid="product-card-product-logo-container"><span class="product-card-container_productLogo__QiFIo"><svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" height="24" width="24" aria-label="Vegetarian"><g clip-path="url(#3981e84c96e29f1e28852f39e11a1daf-a)"><path fill="#fff" d="m21.31 6.608-2.984-3.61-4.82-.507-4.5-1h-5l-.5 1.5 2.5 5.5 4.5 10.5 3 3h3.5l2.5-3 2-6.5.5-2.5-.587-2.723z"></path><path fill="#68BC45" d="M22.805 10.989c-.2-1.5-.8-3.1-1.5-4.4-.7 1.6-4.4 10.8-4.7 11.9-.2.5-.3 1-.3 1.3-.1.4 0 .9 0 .9s-.5.1-.9.2c-1.3.2-2.3-.1-2.8-1.4-.6-1.4-4.1-10.3-4.6-11.6-1.6-4.4-3.6-5.3-3.6-5.3s1.7-.5 3.2 0c1.8.5 2.5 1.8 2.8 2.8.3.9 4 10.2 4 10.2l.6 1.5 2.7-6.7c.3-.7 1-2.5 1.3-3.4.7-1.8.1-3.4-1.1-4.4-6.2-4.9-16.9-1.4-16.9-1.4.9.7 2.3 3.1 2.5 6.6.3 7.2 1.1 11.7 4.1 14 3.4 2.5 7.5 3 14.1 1-.1-.1 1.9-6.6 1.1-11.8"></path></g><defs><clipPath id="3981e84c96e29f1e28852f39e11a1daf-a"><path fill="#fff" d="M0 0h24v24H0z"></path></clipPath></defs></svg></span></div></div></div><div class="product-card-container_verticalActionContainer__2cIkK"><div class="product-card-container_textContainer__GFJ7j product-card-container_showContent__YfpI3 product-card-vertical-templates_textContainer__q_1jt" data-testid="product-card-text-container"><p class="typography_typography__wxrkf typography_body-regular__Vnq4U typography_align-left__vfMmn product-card-content_title__VNanP"><font dir="auto" style="vertical-align: inherit;"><font dir="auto" style="vertical-align: inherit;">XXL Nutrition Fit yogurt protein strawberry</font></font></p></div><div class="product-card-quantity-stepper_root__JeuZB product-card-vertical-templates_action__tL9tY" data-testid="product-card-action"><div class="product-card-quantity-stepper_quantityStepper__T_GTQ" tabindex="0" role="group" aria-description="Druk enter of spatie om aan te passen met het toetsenbord" aria-label="Quantity in cart: 0, button. Add XXL Nutrition Fit yoghurt protein strawberry"><button class="icon-button_root__nywm0 icon-button_secondary__Ft9lX icon-button_small__0UNeI product-card-quantity-stepper_stepperButton__VThaT product-card-quantity-stepper_decreaseButton__WFPJ2" disabled="" type="button" aria-label="Reduce" tabindex="-1" data-testid="quantity-stepper-decrease-button"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" height="16" width="16" fill="currentColor"><path d="M5 3h6c0-.5-1-1-2-1H7c-1 0-2 .5-2 1M3 3l.5-1C3.995.71 6 0 7.14 0h1.83C10 0 11.994.681 12.5 2l.5 1h2c.607 0 1 .398 1 1s-.293 1-.9 1H15v5.546C15 13.547 12.328 16 9.3 16H6.7C3.672 16 1 13.548 1 10.546V5H.9C.292 5 0 4.602 0 4s.392-1 1-1zm0 2v5.5C3 12.297 4.888 14 6.7 14h2.6c1.813 0 3.7-1.657 3.7-3.454V5zm4 2.5c0-.602-.392-1-1-1s-1 .398-1 1V11c0 .602.392 1 1 1s1-.398 1-1zm4 0c0-.602-.393-1-1-1-.608 0-1 .398-1 1V11c0 .602.392 1 1 1 .607 0 1-.398 1-1z"></path></svg></button><div class="quantity-stepper-input_root__W7D94 quantity-stepper-input_scopedTypography__p26nJ quantity-stepper-input_small__JvJEY quantity-stepper-input_collapsed__dCJs6 product-card-quantity-stepper_inputHide___A9VF product-card-quantity-stepper_inputCollapse__hVWqH"><input autocomplete="off" class="quantity-stepper-input_hiddenInput__TtsRK" inputmode="numeric" max="99" maxlength="2" min="0" pattern="[0-9]{1,2}" tabindex="-1" aria-live="polite" aria-label="0 XXL Nutrition Fit yogurt protein strawberry" data-testid="quantity-stepper-input" type="number" value="0" name="quantity"><div class="quantity-stepper-input_formattedDisplay__SbXSu"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 12 12" height="12" width="12" fill="currentColor"><path d="M3 7a1 1 0 0 1 0-2h6a1 1 0 1 1 0 2z"></path></svg><span class="typography_typography__wxrkf typography_body-strong__bqFkS typography_align-left__vfMmn"><font dir="auto" style="vertical-align: inherit;"><font dir="auto" style="vertical-align: inherit;">0</font></font></span><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 12 12" height="12" width="12" fill="currentColor"><path d="M6 2a1 1 0 0 1 1 1v2h2a1 1 0 1 1 0 2H7v2a1 1 0 0 1-2 0V7H3a1 1 0 0 1 0-2h2V3a1 1 0 0 1 1-1"></path></svg></div></div><button class="icon-button_root__nywm0 icon-button_primary__octce icon-button_small__0UNeI product-card-quantity-stepper_stepperButton__VThaT product-card-quantity-stepper_increaseButton__KhyBF product-card-quantity-stepper_showIncreaseButton__Ld3sP" type="button" aria-label="Raise" value="0" tabindex="-1" data-testid="quantity-stepper-increase-button"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" height="16" width="16" fill="currentColor"><path d="M8 1.5a1 1 0 0 0-1 1V7H2.5a1 1 0 0 0 0 2H7v4.5a1 1 0 1 0 2 0V9h4.5a1 1 0 1 0 0-2H9V2.5a1 1 0 0 0-1-1"></path></svg></button></div></div></div></div></div></div>

On Sun, Apr 12, 2026 at 3:50 PM Ajit Kumar Giri <ajitkugiri@gmail.com> wrote:
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

