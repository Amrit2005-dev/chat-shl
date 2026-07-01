from playwright.sync_api import sync_playwright

URL = "https://www.shl.com/products/product-catalog/?start=0&type=1"

REAL_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
    )
    context = browser.new_context(user_agent=REAL_UA, viewport={"width": 1366, "height": 768}, locale="en-US")
    context.add_init_script(
        """
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        window.chrome = { runtime: {} };
        """
    )
    page = context.new_page()
    page.goto(URL, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(3000)

    # Try dismissing a cookie banner if present, then wait a bit more
    for sel in ["#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll", "button:has-text('Allow all')", "button:has-text('Accept')"]:
        try:
            if page.locator(sel).count() > 0:
                page.locator(sel).first.click(timeout=2000)
                page.wait_for_timeout(1500)
                break
        except Exception:
            pass

    html = page.content()
    with open("rendered_page2.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("length:", len(html))

    # Broad link search
    all_links = page.query_selector_all("a")
    print(f"total <a> tags: {len(all_links)}")
    view_links = [a for a in all_links if a.get_attribute("href") and "/view/" in a.get_attribute("href")]
    print(f"links containing '/view/': {len(view_links)}")
    for a in view_links[:15]:
        print(" -", a.inner_text().strip()[:60], "|", a.get_attribute("href"))

    # Look for any element mentioning known assessment-ish words
    body_text = page.inner_text("body")
    for kw in ["Java", "Python", "OPQ", "Individual Test Solutions", "Verify", "SQL"]:
        print(f"\nkeyword '{kw}' present in visible body text: {kw in body_text}")

    print("\n--- first 500 chars of visible body text ---")
    print(body_text[:500])

    browser.close()
