import requests
import json

url = "https://tcp-us-prod-rnd.shl.com/voiceRater/shl-ai-hiring/shl_product_catalog.json"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

resp = requests.get(url, headers=headers, timeout=30)
print("STATUS:", resp.status_code)
print("CONTENT-TYPE:", resp.headers.get("content-type"))
print("LENGTH:", len(resp.content))

# save raw
with open("shl_product_catalog_raw.json", "wb") as f:
    f.write(resp.content)

# try to parse and show structure
try:
    data = resp.json()
    print("\nParsed OK.")
    if isinstance(data, list):
        print("Type: list, length:", len(data))
        print("First item:\n", json.dumps(data[0], indent=2)[:1500])
    elif isinstance(data, dict):
        print("Type: dict, top-level keys:", list(data.keys()))
        print(json.dumps(data, indent=2)[:1500])
except Exception as e:
    print("Could not parse as JSON:", e)
    print("First 1000 chars of raw response:")
    print(resp.text[:1000])
