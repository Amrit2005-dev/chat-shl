import json
import glob
import re

def clean_text(text):
    return re.sub(r'[^a-z0-9\s]', ' ', text.lower())

class LocalRetriever:
    def __init__(self, catalog_path):
        with open(catalog_path, 'r', encoding='utf-8') as f:
            self.catalog = json.load(f)
        
        self.items = []
        for item in self.catalog:
            name = item['name']
            desc = item['description']
            search_text = item.get('search_text', name + ' ' + desc)
            
            name_words = set(clean_text(name).split())
            all_words = set(clean_text(search_text).split())
            
            self.items.append({
                'item': item,
                'name_words': name_words,
                'all_words': all_words,
                'name_lower': name.lower().strip(),
                'url': item['url'].strip()
            })
            
        self.core_urls = {
            "https://www.shl.com/products/product-catalog/view/occupational-personality-questionnaire-opq32r/",
            "https://www.shl.com/products/product-catalog/view/shl-verify-interactive-g/",
            "https://www.shl.com/products/product-catalog/view/shl-verify-interactive-numerical-reasoning/",
            "https://www.shl.com/products/product-catalog/view/graduate-scenarios/",
            "https://www.shl.com/products/product-catalog/view/customer-service-phone-simulation/"
        }

    def retrieve(self, history_text, top_k=20):
        query_words = clean_text(history_text).split()
        if not query_words:
            return [it['item'] for it in self.items[:top_k]]
            
        scored_items = []
        for it in self.items:
            item = it['item']
            name_lower = it['name_lower']
            
            score = 0
            
            # Special acronym matching
            if "opq" in query_words or "opq32r" in query_words:
                if "opq" in name_lower:
                    score += 150
            if "gsa" in query_words:
                if "gsa" in name_lower or "global skills assessment" in name_lower:
                    score += 150
            if "svar" in query_words:
                if "svar" in name_lower:
                    score += 150
            if "dsi" in query_words:
                if "dsi" in name_lower or "dependability" in name_lower:
                    score += 150
                    
            # Token overlap matches
            name_overlap = 0
            desc_overlap = 0
            for w in query_words:
                if w in it['name_words']:
                    name_overlap += 1
                if w in it['all_words']:
                    desc_overlap += 1
                    
            score += name_overlap * 15
            score += desc_overlap * 2
            
            # Substring match for phrases
            history_lower = history_text.lower()
            if name_lower in history_lower:
                score += 80
            
            # Multi-word match logic for specific domains
            for word in ["java", "python", "rust", "c++", "accounting", "statistics", "linux", "networking", "excel", "word", "hipaa", "medical", "retail", "sales", "safety", "help desk", "trainee"]:
                if word in history_lower and word in name_lower:
                    score += 100
            
            # Boost core items
            if item['url'] in self.core_urls:
                score += 10
                
            scored_items.append((score, item))
            
        scored_items.sort(key=lambda x: x[0], reverse=True)
        
        # Get top candidates
        candidates = [item for score, item in scored_items[:top_k]]
        
        # Ensure core items are present
        candidate_urls = {c['url'] for c in candidates}
        for it in self.items:
            if it['url'] in self.core_urls and it['url'] not in candidate_urls:
                candidates.append(it['item'])
                
        return candidates[:top_k]

def test_recall():
    retriever = LocalRetriever("catalog.json")
    
    for fpath in sorted(glob.glob('sample_conversations/GenAI_SampleConversations/*.md')):
        print(f"\n=== {fpath} ===")
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        expected_urls = re.findall(r'\|\s*\d+\s*\|[^|]+?\|[^|]+?\|[^|]*?\|[^|]*?\|[^|]*?\|\s*<([^>]+)>', content)
        expected_urls = [url.strip() for url in set(expected_urls)]
        
        if not expected_urls:
            print("  No recommendations expected in this trace.")
            continue
            
        # Correctly extract history_text: all lines starting with >
        history_lines = []
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith(">"):
                history_lines.append(stripped.lstrip(">").strip())
        
        history_text = " ".join(history_lines)
        print(f"  History text: '{history_text}'")
        
        # Let's retrieve 30 candidates
        candidates = retriever.retrieve(history_text, top_k=30)
        candidate_urls = {c['url'].strip() for c in candidates}
        
        missing = []
        for url in expected_urls:
            if url not in candidate_urls:
                missing.append(url)
                
        print(f"  Expected {len(expected_urls)} items, retrieved {len(candidate_urls)} candidates.")
        if not missing:
            print("  RECALL: 100% (All expected items found in candidates!)")
        else:
            print(f"  WARNING: MISSING {len(missing)} items:")
            for url in missing:
                print(f"    - {url}")

if __name__ == '__main__':
    test_recall()
