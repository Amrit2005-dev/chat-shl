"""
Run in Colab (playwright + chromium already installed from before):
    !python playwright_diagnose_v2.py

This launches Chromium with settings that avoid the common headless-browser
fingerprints CloudFront (and similar WAFs) look for.
"""
from playwright.sync_api import sync_playwright

URL = "https://www.shl.com/products/product-catalog/?start=0&type=1"

REAL_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
        ],
    )
    context = browser.new_context(
        user_agent=REAL_UA,
        viewport={"width": 1366, "height": 768},
        locale="en-US",
    )
    # Hide the most common automation fingerprint before any page script runs
    context.add_init_script(
        """
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        window.chrome = { runtime: {} };
        Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
        """
    )
    page = context.new_page()
    page.goto(URL, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(3000)

    html = page.content()
    with open("rendered_page.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("length:", len(html))
    print(html[:1500])

    tables = page.query_selector_all("table")
    print(f"\n<table> elements found: {len(tables)}")

    links = page.query_selector_all("a[href*='/product-catalog/view/']")
    print(f"Links matching '/product-catalog/view/': {len(links)}")
    for a in links[:10]:
        print(" -", a.inner_text().strip()[:60], "|", a.get_attribute("href"))

    browser.close()
