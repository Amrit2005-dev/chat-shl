import json
import requests
from collections import Counter

url = "https://tcp-us-prod-rnd.shl.com/voiceRater/shl-ai-hiring/shl_product_catalog.json"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

resp = requests.get(url, headers=headers, timeout=30)
data = json.loads(resp.text, strict=False)  # allow literal control chars inside strings

print("Type:", type(data))
print("Total items:", len(data))

# Collect every key seen across all items (schema may vary slightly item to item)
all_keys = Counter()
for item in data:
    all_keys.update(item.keys())
print("\nAll keys seen and how many items have them:")
for k, v in all_keys.most_common():
    print(f"  {k}: {v}")

# Show one full example
print("\n--- full example item ---")
print(json.dumps(data[0], indent=2)[:2000])

# Check for anything that distinguishes "Individual Test Solutions" vs "Job Solutions" (Pre-packaged)
# Look for likely field names
for key in ["type", "category", "solution_type", "product_type", "test_type", "is_prepackaged"]:
    values = set()
    for item in data:
        if key in item:
            v = item[key]
            values.add(json.dumps(v) if isinstance(v, (list, dict)) else v)
    if values:
        print(f"\nDistinct values for '{key}' ({len(values)} distinct):", list(values)[:20])

# Save the cleanly-parsed version
with open("shl_catalog_clean.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print("\nSaved shl_catalog_clean.json")
