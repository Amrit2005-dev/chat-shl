from playwright.sync_api import sync_playwright

URL = "https://www.shl.com/solutions/products/product-catalog/?type=1&type=1&start=0"

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
        "Object.defineProperty(navigator, 'webdriver', { get: () => undefined }); window.chrome = { runtime: {} };"
    )
    page = context.new_page()
    page.goto(URL, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(2000)

    for sel in ["#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll", "button:has-text('Allow all')", "button:has-text('Accept')"]:
        try:
            if page.locator(sel).count() > 0:
                page.locator(sel).first.click(timeout=2000)
                page.wait_for_timeout(1500)
                break
        except Exception:
            pass

    page.wait_for_timeout(2000)
    html = page.content()
    with open("rendered_page3.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("length:", len(html))
    print("final URL after navigation:", page.url)

    all_links = page.query_selector_all("a")
    view_links = [a for a in all_links if a.get_attribute("href") and "/view/" in a.get_attribute("href")]
    print(f"total <a> tags: {len(all_links)}, links with '/view/': {len(view_links)}")
    for a in view_links[:15]:
        print(" -", a.inner_text().strip()[:60], "|", a.get_attribute("href"))

    body_text = page.inner_text("body")
    for kw in ["Java", "OPQ", "Individual Test Solutions", "Verify"]:
        print(f"keyword '{kw}' in body: {kw in body_text}")

    idx = body_text.find("result")
    print("\ncontext around 'result':", body_text[max(0,idx-100):idx+200] if idx != -1 else "not found")

    browser.close()
