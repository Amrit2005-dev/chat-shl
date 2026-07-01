"""
Run this in the SAME Colab session (raw_page.html should already exist from
the previous diagnostic run). This checks whether the page embeds its data
as JSON directly in the HTML (very common in React/Next.js apps), which
would let us skip needing a real browser entirely.
"""
import re
import json

with open("raw_page.html", "r", encoding="utf-8") as f:
    html = f.read()

candidates = [
    "__NEXT_DATA__",
    "__NUXT__",
    "window.__INITIAL_STATE__",
    "application/json",
    "drupal-settings-json",
    "data-drupal-selector",
]

for marker in candidates:
    idx = html.find(marker)
    print(f"'{marker}': found at index {idx}")

# Try to locate any <script type="application/json"> blocks and show their ids + a size preview
print("\n--- <script type=application/json> blocks ---")
for m in re.finditer(r'<script[^>]*type=["\']application/json["\'][^>]*>', html):
    tag = m.group(0)
    start = m.end()
    end = html.find("</script>", start)
    snippet = html[start:min(end, start + 200)]
    print(f"\nTAG: {tag}\nSIZE: {end - start} chars\nPREVIEW: {snippet}")

# Also check for any obvious API/ajax hints
print("\n--- possible API endpoint hints ---")
for m in re.finditer(r'["\'](/[a-zA-Z0-9_\-/]*(?:api|ajax|json|catalog)[a-zA-Z0-9_\-/]*)["\']', html):
    print(m.group(1))
