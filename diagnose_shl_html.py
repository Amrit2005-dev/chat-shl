"""
Quick diagnostic: run this in the SAME Colab session (network already works there).
It prints out the raw HTML structure around the catalog table so we can see the
actual tags/classes SHL uses, then fix the real scraper accordingly.
"""
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}

url = "https://www.shl.com/products/product-catalog/?start=0&type=1"
resp = requests.get(url, headers=HEADERS, timeout=20)
print("STATUS:", resp.status_code)
print("LENGTH:", len(resp.text))

html = resp.text

# Save the full raw HTML so you can download and share it if needed
with open("raw_page.html", "w", encoding="utf-8") as f:
    f.write(html)

# Print the region around the first occurrence of a known assessment-ish keyword
# to see real tag structure (try a few anchors in case one doesn't appear)
for marker in ["Individual Test Solutions", "table", "Pre-packaged Job Solutions", "product-catalog"]:
    idx = html.find(marker)
    print(f"\n--- context around '{marker}' (found at index {idx}) ---")
    if idx != -1:
        print(html[max(0, idx - 300): idx + 1500])
    else:
        print("NOT FOUND")
