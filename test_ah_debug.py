from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=[
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-blink-features=AutomationControlled"
        ]
    )

    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
    )

    page.goto("https://www.ah.nl/producten/1730/zuivel-eieren", timeout=60000)
    
    # Wait longer for JavaScript to render
    page.wait_for_timeout(3000)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)
    
    content = page.content()
    print(f"Page content length: {len(content)}")
    print(f"\nFirst 500 chars of page:\n{content[:500]}")
    
    # Check for common block indicators
    if "403" in content or "Forbidden" in content:
        print("\n❌ Server returned 403 Forbidden - Site is blocking requests")
    elif "blocked" in content.lower():
        print("\n❌ Page contains 'blocked' text")
    elif "captcha" in content.lower():
        print("\n❌ CAPTCHA detected")
    elif "<html" not in content.lower():
        print("\n❌ Not valid HTML - site may be returning minimal response")
    else:
        print("\n✅ Page seems to be loading")
    
    # Try to find product elements
    try:
        products = page.query_selector_all("[data-testid*='product']")
        print(f"Found {len(products)} elements with 'product' in testid")
    except:
        print("No product elements found")
    
    browser.close()
