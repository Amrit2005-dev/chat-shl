import glob
import re
import json

def verify():
    with open('catalog.json', 'r', encoding='utf-8') as f:
        d = json.load(f)
    urls_in_catalog = {i['url']: i for i in d}
    names_in_catalog = {i['name'].lower().strip(): i for i in d}

    print(f"Loaded {len(d)} catalog items.")

    for fpath in sorted(glob.glob('sample_conversations/GenAI_SampleConversations/*.md')):
        print(f"\n=== {fpath} ===")
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Match table rows like:
        # | 1 | SVAR Spoken English (US) (New) | K | Simulations | - | English (USA) | <https://www.shl.com/products/product-catalog/view/svar-spoken-english-us-new/> |
        # Let's use a regex to extract Name, TestType and URL
        rows = re.findall(r'\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*[^|]*?\|\s*[^|]*?\|\s*[^|]*?\|\s*<([^>]+)>', content)
        if not rows:
            print("  No recommendation table found in this trace.")
            continue
            
        seen = set()
        for row in rows:
            num = row[0]
            name = row[1].strip()
            test_type_str = row[2].strip()
            url = row[3].strip()
            
            key = (name, url)
            if key in seen:
                continue
            seen.add(key)
            
            match_url = urls_in_catalog.get(url)
            # Match name loosely: remove hyphens, replace multiple spaces
            norm_name = name.lower().replace('-', ' ').replace('  ', ' ').strip()
            match_name = None
            for cat_name, item in names_in_catalog.items():
                norm_cat = cat_name.replace('-', ' ').replace('  ', ' ').strip()
                if norm_name == norm_cat:
                    match_name = item
                    break

            print(f"  Trace Name: '{name}'")
            if match_url:
                print(f"    URL Match: '{match_url['name']}' | test_type: {match_url['test_type']}")
            else:
                print(f"    WARNING: URL NOT FOUND IN CATALOG: {url}")
            
            if match_name:
                print(f"    Name Match: '{match_name['name']}' | URL: {match_name['url']}")
            else:
                print(f"    WARNING: Name NOT FOUND IN CATALOG: '{name}'")

if __name__ == '__main__':
    verify()
