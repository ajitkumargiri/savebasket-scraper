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

    page.goto("https://www.ah.nl/producten/1730/zuivel-eieren?page=1", timeout=60000)
    time.sleep(5)
    
    # Save page content to check
    content = page.content()
    print(f"Page loaded, content length: {len(content)}")
    
    # Check for blocking indicators
    if "blocked" in content.lower() or "captcha" in content.lower():
        print("⚠️ Page seems to be blocked or showing CAPTCHA")
    else:
        print("✅ Page loaded successfully")
    
    # Try to find ANY product-like elements
    all_divs = page.query_selector_all("div")
    print(f"Total divs: {len(all_divs)}")
    
    browser.close()
EOF
