"""
Run in Colab:
    !pip install playwright -q
    !playwright install chromium --with-deps
    !python playwright_diagnose.py

This renders the catalog page with a real (headless) browser so the
JS-loaded table actually appears, then saves the rendered HTML and prints
useful bits so we can figure out the real selectors.
"""
from playwright.sync_api import sync_playwright

URL = "https://www.shl.com/products/product-catalog/?start=0&type=1"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(URL, wait_until="networkidle", timeout=60000)

    # give any lazy client-side rendering a moment to settle
    page.wait_for_timeout(3000)

    html = page.content()
    with open("rendered_page.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Saved rendered_page.html, length:", len(html))

    # Try the obvious things first
    tables = page.query_selector_all("table")
    print(f"\n<table> elements found: {len(tables)}")

    # Links that look like assessment detail pages
    links = page.query_selector_all("a[href*='/product-catalog/view/']")
    print(f"Links matching '/product-catalog/view/': {len(links)}")
    for a in links[:10]:
        print(" -", a.inner_text().strip()[:60], "|", a.get_attribute("href"))

    # Print a chunk of HTML around the first such link for structure inspection
    if links:
        first_href = links[0].get_attribute("href")
        idx = html.find(first_href)
        print("\n--- HTML context around first assessment link ---")
        print(html[max(0, idx - 800): idx + 800])

    browser.close()
