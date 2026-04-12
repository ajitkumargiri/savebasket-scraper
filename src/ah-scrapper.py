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
