from playwright.sync_api import sync_playwright
import json
import os
import time
from datetime import datetime
import threading

# ✅ SCRAPE ALL CATEGORIES DYNAMICALLY
MAIN_PAGE_URL = "https://www.jumbo.com/producten/"

STEP = 24  # products per page
DELAY_BETWEEN_REQUESTS = 0.5  # 500ms - respectful & fast
TIMEOUT_PER_PAGE = 30000  # 30 seconds

# Thread-safe counter
lock = threading.Lock()
total_products = 0


def get_all_categories(page):
    """Extract all categories from Jumbo main products page."""
    print("📂 Discovering all Jumbo categories...")

    try:
        page.goto(MAIN_PAGE_URL, timeout=TIMEOUT_PER_PAGE)
        page.wait_for_load_state("domcontentloaded", timeout=TIMEOUT_PER_PAGE)
        page.wait_for_timeout(1000)
    except Exception as e:
        print(f"❌ Failed to load main page: {e}")
        return []

    # Find all category links directly: <a class="category-card">
    category_links = page.query_selector_all("a.category-card")

    categories = []

    for link_el in category_links:
        try:
            href = link_el.get_attribute("href")
            if not href:
                continue

            category_url = "https://www.jumbo.com" + href if not href.startswith("http") else href

            name_el = link_el.query_selector(".category-card__label div")
            if not name_el:
                continue

            category_name = name_el.inner_text().strip()

            if category_name and category_url:
                categories.append({"name": category_name, "url": category_url})
                print(f"  ✓ Found: {category_name}")
        except:
            continue

    print(f"\n✅ Found {len(categories)} categories\n")
    return categories


def get_category_filename(category_name):
    """Generate a safe output filename for a category (date-stamped)."""
    safe_name = category_name.replace(" ", "_").replace(",", "").lower()
    date = datetime.now().strftime("%d-%m-%Y")
    return f"output/jumbo/{date}/{safe_name}.json"


def category_file_exists(category_name):
    """Return True if today's JSON file for this category already exists."""
    return os.path.exists(get_category_filename(category_name))


def save_category_products(category_name, products):
    """Save products for a single category to its own JSON file."""
    filename = get_category_filename(category_name)
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)
    return filename


def scrape_page(page, category_name, offset, page_num):
    """Scrape products from a single paginated page."""
    global total_products

    try:
        page.wait_for_load_state("domcontentloaded", timeout=TIMEOUT_PER_PAGE)
    except:
        return []

    try:
        page.wait_for_selector("article.product-container", timeout=5000)
    except:
        return []

    page.wait_for_timeout(300)

    items = page.query_selector_all("article.product-container")

    if not items:
        return []

    print(f"  ✓ {category_name}: Page {page_num} ({len(items)} products)")

    data = []

    for item in items:
        try:
            name_el = item.query_selector("h3")
            whole_el = item.query_selector(".whole")
            frac_el = item.query_selector(".fractional")
            link_el = item.query_selector("a[href]")

            if not name_el or not whole_el or not frac_el:
                continue

            name = name_el.inner_text().strip()
            price = float(f"{whole_el.inner_text().strip()}.{frac_el.inner_text().strip()}")

            product_url = ""
            if link_el:
                href = link_el.get_attribute("href")
                if href:
                    product_url = "https://www.jumbo.com" + href

            data.append({
                "store": "Jumbo",
                "category": category_name,
                "name": name,
                "price": price,
                "currency": "EUR",
                "product_url": product_url,
                "scraped_at": datetime.now().isoformat()
            })

        except:
            continue

    with lock:
        total_products += len(data)

    return data


def scrape_category(page, category_name, category_url):
    """Scrape all paginated products from a single category."""
    print(f"\n📂 Scraping: {category_name}")

    all_products = []
    offset = 0
    page_num = 0

    while True:
        url_with_offset = (
            f"{category_url}?offSet={offset}"
            if "?" not in category_url
            else f"{category_url}&offSet={offset}"
        )

        try:
            page.goto(url_with_offset, timeout=TIMEOUT_PER_PAGE)
        except:
            break

        products = scrape_page(page, category_name, offset, page_num)

        if not products:
            print(f"  ℹ️  End of category")
            break

        all_products.extend(products)
        offset += STEP
        page_num += 1
        time.sleep(DELAY_BETWEEN_REQUESTS)

    print(f"  ✅ Total: {len(all_products)} products")
    return all_products


def run():
    """Main scraper: discover categories, scrape each one, save separately."""
    global total_products
    total_products = 0

    os.makedirs("output", exist_ok=True)

    print("🚀 Starting Jumbo Scraper (MULTI-CATEGORY MODE)")

    print(f"{'='*60}\n")

    all_data = []
    start_time = time.time()
    categories_processed = 0
    categories_skipped = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # STEP 1: Discover all categories
        all_categories = get_all_categories(page)

        if not all_categories:
            print("❌ No categories found!")
            return []

        # STEP 2: Scrape all categories
        categories_to_scrape = all_categories
        print(f"Processing {len(categories_to_scrape)} categories\n")

        # STEP 3: Scrape each category
        for i, category in enumerate(categories_to_scrape, 1):
            category_name = category["name"]
            print(f"\n[{i}/{len(categories_to_scrape)}] {category_name}")

            # Skip if today's file already exists
            if category_file_exists(category_name):
                print(f"  ⏭️  SKIPPED: file already exists for today")
                categories_skipped += 1
                continue

            products = scrape_category(page, category_name, category["url"])

            if products:
                filename = save_category_products(category_name, products)
                print(f"  💾 Saved: {filename}")
                all_data.extend(products)
                categories_processed += 1
            else:
                print(f"  ⚠️  No products found")

        page.close()
        browser.close()

    elapsed = time.time() - start_time

    print(f"\n{'='*60}")
    print(f"✅ COMPLETE!")
    print(f"  Processed : {categories_processed} categories")
    print(f"  Skipped   : {categories_skipped} categories (file already exists)")
    print(f"  Products  : {len(all_data)}")
    print(f"  Time      : {elapsed:.1f}s")
    print(f"{'='*60}\n")

    return all_data


if __name__ == "__main__":
    run()
