from playwright.sync_api import sync_playwright
import time
import json

print("🔍 Inspecting AH website structure...\n")

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=[
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-setuid-sandbox",
            "--disable-blink-features=AutomationControlled",
            "--disable-web-resources",
        ]
    )

    # More aggressive anti-detection
    context = browser.new_context(
        user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        locale="nl-NL",
        viewport={"width": 1920, "height": 1080},
        screen={"width": 1920, "height": 1080}
    )
    
    page = context.new_page()
    
    # Add more headers
    page.set_extra_http_headers({
        "Accept-Language": "nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.ah.nl/",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    })

    print("📡 Loading page...")
    page.goto("https://www.ah.nl/producten/1730/zuivel-eieren?page=1", timeout=60000, wait_until="load")
    
    # Wait for JavaScript to fully render
    print("⏳ Waiting for page to render...")
    page.wait_for_timeout(5000)
    
    try:
        page.wait_for_selector("body", timeout=5000)
        print("✅ Page body loaded")
    except:
        print("❌ No body element found")

    content = page.content()
    print(f"📏 Page content length: {len(content)} bytes\n")

    if len(content) < 500:
        print("❌ Page returned minimal content - likely blocked")
        print(f"Content: {content}\n")
    else:
        print("✅ Page returned substantial content\n")

    # Try different selectors to find products
    selectors_to_try = [
        "article",
        "[class*='product']",
        "[class*='Product']",
        "[data-testid*='product']",
        "[role='article']",
        ".product-card",
        ".product-tile",
        "[class*='tile']",
        "[class*='card']",
        "li[data-testid]",
        "div[data-testid]",
    ]

    print("🔎 Testing selectors:\n")
    for selector in selectors_to_try:
        try:
            elements = page.query_selector_all(selector)
            if elements:
                print(f"✅ {selector}: Found {len(elements)} elements")
                
                # Show first element's structure
                first = elements[0]
                html = first.outer_html()[:200]
                print(f"   First element: {html}...\n")
        except:
            pass

    # Save full page HTML to file for inspection
    with open("ah_page_source.html", "w", encoding="utf-8") as f:
        f.write(content)
    print("💾 Saved full page source to: ah_page_source.html\n")

    browser.close()

print("✅ Inspection complete. Check ah_page_source.html to find correct selectors.")
