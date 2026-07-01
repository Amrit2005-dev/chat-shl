"""
SHL Product Catalog Scraper
----------------------------
Scrapes the "Individual Test Solutions" table from
https://www.shl.com/products/product-catalog/ (type=1), then visits each
assessment's detail page to pull description, job levels, languages, etc.

Usage:
    python scrape_shl_catalog.py

Output:
    shl_catalog.json   -> list of assessment dicts, one per assessment
    shl_catalog.csv     -> flat CSV version (easy to eyeball in Excel)

Run this somewhere with normal internet access (your own machine, or a
free Google Colab notebook) since it needs to reach www.shl.com directly.
"""

import json
import csv
import time
import concurrent.futures as cf
from dataclasses import dataclass, field, asdict

import requests
from bs4 import BeautifulSoup

BASE = "https://www.shl.com"
LISTING_URL = "https://www.shl.com/products/product-catalog/"
PAGE_SIZE = 12
TYPE_INDIVIDUAL = 1  # "Individual Test Solutions" (Job Solutions = type 2, out of scope)

TEST_TYPE_LEGEND = {
    "A": "Ability & Aptitude",
    "B": "Biodata & Situational Judgement",
    "C": "Competencies",
    "D": "Development & 360",
    "E": "Assessment Exercises",
    "K": "Knowledge & Skills",
    "P": "Personality & Behavior",
    "S": "Simulations",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}

session = requests.Session()
session.headers.update(HEADERS)


@dataclass
class Assessment:
    name: str
    url: str
    remote_testing: bool = False
    adaptive_irt: bool = False
    test_types: list = field(default_factory=list)
    description: str = ""
    job_levels: list = field(default_factory=list)
    languages: list = field(default_factory=list)
    duration_minutes: str = ""


def fetch(url: str, retries: int = 3, backoff: float = 1.5) -> BeautifulSoup | None:
    for attempt in range(retries):
        try:
            resp = session.get(url, timeout=20)
            if resp.status_code == 200:
                return BeautifulSoup(resp.text, "lxml")
            print(f"  [warn] {resp.status_code} on {url}")
        except requests.RequestException as e:
            print(f"  [warn] {e} on {url}")
        time.sleep(backoff * (attempt + 1))
    return None


def discover_total_pages() -> int:
    """Read the pagination control on page 1 to find the last page's `start` value."""
    soup = fetch(f"{LISTING_URL}?start=0&type={TYPE_INDIVIDUAL}")
    if soup is None:
        raise RuntimeError("Could not load the first catalog page.")
    max_start = 0
    for a in soup.select("a[href*='start=']"):
        href = a.get("href", "")
        if f"type={TYPE_INDIVIDUAL}" not in href:
            continue
        try:
            start_val = int(href.split("start=")[1].split("&")[0])
            max_start = max(max_start, start_val)
        except (IndexError, ValueError):
            continue
    return max_start // PAGE_SIZE + 1


def parse_listing_page(soup: BeautifulSoup) -> list[Assessment]:
    """The catalog table has two tables on the page (Job Solutions, Individual
    Test Solutions). We want the one whose header says 'Individual Test Solutions'."""
    results = []
    for table in soup.find_all("table"):
        header_text = table.find("tr").get_text(" ", strip=True).lower()
        if "individual test solutions" not in header_text:
            continue
        for row in table.find_all("tr")[1:]:
            cells = row.find_all("td")
            if len(cells) < 4:
                continue
            link = cells[0].find("a")
            if not link:
                continue
            name = link.get_text(strip=True)
            url = link.get("href", "")
            if url.startswith("/"):
                url = BASE + url
            remote = bool(cells[1].find(["span", "img"]))
            adaptive = bool(cells[2].find(["span", "img"]))
            types = [t.strip() for t in cells[3].get_text(strip=True) if t.strip()]
            results.append(
                Assessment(
                    name=name,
                    url=url,
                    remote_testing=remote,
                    adaptive_irt=adaptive,
                    test_types=types,
                )
            )
    return results


def scrape_all_listings() -> list[Assessment]:
    total_pages = discover_total_pages()
    print(f"Found {total_pages} listing pages of Individual Test Solutions.")
    all_items: list[Assessment] = []
    for page in range(total_pages):
        start = page * PAGE_SIZE
        url = f"{LISTING_URL}?start={start}&type={TYPE_INDIVIDUAL}"
        soup = fetch(url)
        if soup is None:
            continue
        items = parse_listing_page(soup)
        print(f"  page {page + 1}/{total_pages} (start={start}): {len(items)} items")
        all_items.extend(items)
        time.sleep(0.4)  # be polite
    # de-dupe by URL just in case of pagination overlap
    seen = set()
    deduped = []
    for item in all_items:
        if item.url not in seen:
            seen.add(item.url)
            deduped.append(item)
    return deduped


def enrich_with_detail_page(item: Assessment) -> Assessment:
    soup = fetch(item.url)
    if soup is None:
        return item
    # Description: SHL detail pages usually have a lead paragraph near the top
    desc_el = soup.select_one("div.description, .product-description, article p")
    if desc_el:
        item.description = desc_el.get_text(" ", strip=True)
    else:
        # fallback: meta description
        meta = soup.find("meta", attrs={"name": "description"})
        if meta and meta.get("content"):
            item.description = meta["content"].strip()

    # Job levels / languages often appear as labeled lists on the page
    text_blocks = soup.get_text("\n", strip=True)
    for label, attr in (("Job levels", "job_levels"), ("Languages", "languages")):
        if label in text_blocks:
            idx = text_blocks.find(label)
            snippet = text_blocks[idx: idx + 300]
            setattr(item, attr, snippet.split("\n")[1:6])

    return item


def scrape_details(items: list[Assessment], max_workers: int = 8) -> list[Assessment]:
    enriched = []
    with cf.ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(enrich_with_detail_page, item): item for item in items}
        for i, fut in enumerate(cf.as_completed(futures), 1):
            enriched.append(fut.result())
            if i % 20 == 0:
                print(f"  enriched {i}/{len(items)} detail pages")
    return enriched


def main():
    print("Step 1: scraping listing pages...")
    items = scrape_all_listings()
    print(f"Total unique assessments found: {len(items)}")

    print("Step 2: visiting each detail page for description/job levels...")
    items = scrape_details(items)

    # expand test type letters to full names too, for readability
    payload = []
    for item in items:
        d = asdict(item)
        d["test_type_names"] = [TEST_TYPE_LEGEND.get(t, t) for t in item.test_types]
        payload.append(d)

    with open("shl_catalog.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    with open("shl_catalog.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(payload[0].keys()))
        writer.writeheader()
        for row in payload:
            row = row.copy()
            row["test_types"] = ";".join(row["test_types"])
            row["test_type_names"] = ";".join(row["test_type_names"])
            row["job_levels"] = ";".join(row["job_levels"])
            row["languages"] = ";".join(row["languages"])
            writer.writerow(row)

    print(f"\nDone. Wrote shl_catalog.json and shl_catalog.csv ({len(payload)} assessments).")


if __name__ == "__main__":
    main()
