import glob
import re
import json
import requests
import time

API_URL = "http://localhost:8000/chat"
HEALTH_URL = "http://localhost:8000/health"

def load_catalog(path="catalog.json"):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return {item['url'].strip(): item for item in data}

def parse_trace(fpath):
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Split into turns
    # Turns are marked by ### Turn 1, ### Turn 2, etc.
    turns = re.split(r'### Turn \d+', content)
    # The first element is pre-turn stuff, like ## Conversation
    turns = turns[1:]
    
    parsed_turns = []
    for turn in turns:
        # Extract user input
        user_match = re.search(r'\*\*User\*\*\s*>\s*(.*?)(?=\n\n|\n_|\n\*\*|$)', turn, re.DOTALL)
        user_text = user_match.group(1).strip() if user_match else ""
        
        # Check if recommendations are expected (it shouldn't be null)
        no_recs = "recommendations: null" in turn or "No recommendations" in turn
        
        # Parse expected recommendations from the table in the turn if present
        expected_urls = re.findall(r'\|\s*\d+\s*\|[^|]+?\|[^|]+?\|[^|]*?\|[^|]*?\|[^|]*?\|\s*<([^>]+)>', turn)
        expected_urls = [u.strip() for u in expected_urls]
        
        end_of_conv = "end_of_conversation: **true**" in turn or "end_of_conversation`: **true**" in turn.lower()
        
        parsed_turns.append({
            "user_text": user_text,
            "no_recs": no_recs,
            "expected_urls": expected_urls,
            "end_of_conv": end_of_conv
        })
    return parsed_turns

def run_evaluation():
    catalog_urls = load_catalog()
    trace_files = sorted(glob.glob('sample_conversations/GenAI_SampleConversations/*.md'))
    
    # Wait for server to be ready
    print("Waiting for local FastAPI server to start...")
    for _ in range(30):
        try:
            resp = requests.get(HEALTH_URL, timeout=2)
            if resp.status_code == 200:
                print("Server is ready!")
                break
        except Exception:
            pass
        time.sleep(1)
    else:
        print("Error: FastAPI server is not reachable on port 8000. Please start it using 'uvicorn app:app --port 8000'.")
        return

    total_traces = 0
    passed_traces = 0
    all_recalls = []

    for fpath in trace_files:
        print(f"\n==================================================")
        print(f"Replaying trace: {fpath}")
        print(f"==================================================")
        
        turns = parse_trace(fpath)
        conversation_history = []
        
        trace_passed = True
        trace_recalls = []
        
        for turn_idx, turn in enumerate(turns):
            user_text = turn["user_text"]
            print(f"\nTurn {turn_idx + 1}: User says -> '{user_text}'")
            
            # Add user message to history
            conversation_history.append({"role": "user", "content": user_text})
            
            # Call API
            t0 = time.time()
            try:
                resp = requests.post(API_URL, json={"messages": conversation_history}, timeout=60)
                t1 = time.time()
                print(f"  API Response received in {t1 - t0:.2f}s")
            except Exception as e:
                print(f"  ERROR: API Call failed: {e}")
                trace_passed = False
                break
                
            time.sleep(12) # Prevent overloading Groq/local server
                
            if resp.status_code != 200:
                print(f"  ERROR: HTTP status {resp.status_code}. Response: {resp.text}")
                trace_passed = False
                break
                
            res_json = resp.json()
            reply = res_json.get("reply", "")
            recommendations = res_json.get("recommendations", [])
            end_of_conversation = res_json.get("end_of_conversation", False)
            
            print(f"  Agent reply: '{reply[:150]}...'")
            print(f"  Recommendations count: {len(recommendations)}")
            print(f"  End of conversation: {end_of_conversation}")
            
            # Verify Schema
            if not isinstance(reply, str) or not isinstance(recommendations, list) or not isinstance(end_of_conversation, bool):
                print("  ERROR: Schema type mismatch!")
                trace_passed = False
                
            # Verify recommended items exist in catalog
            for rec in recommendations:
                name = rec.get("name")
                url = rec.get("url")
                test_type = rec.get("test_type")
                
                if not name or not url or not test_type:
                    print(f"  ERROR: Missing recommendation field: {rec}")
                    trace_passed = False
                    
                match = catalog_urls.get(url.strip())
                if not match:
                    print(f"  ERROR: Recommended URL '{url}' is NOT in the catalog!")
                    trace_passed = False
                else:
                    # Optional warning if name differs
                    cat_name = match['name']
                    if cat_name.lower().replace('\n', '').strip() != name.lower().replace('\n', '').strip():
                        print(f"  WARNING: Name mismatch between recommendation '{name}' and catalog '{cat_name}'")

            # Check expected recommendations and compute recall
            expected_urls = turn["expected_urls"]
            if expected_urls:
                rec_urls = [r["url"].strip().lower().rstrip('/') for r in recommendations]
                expected_clean = [u.lower().rstrip('/') for u in expected_urls]
                
                # Compute recall@10
                relevant_in_rec = sum(1 for u in expected_clean if u in rec_urls)
                recall = relevant_in_rec / len(expected_clean) if expected_clean else 0.0
                trace_recalls.append(recall)
                print(f"  Recall@10 for this turn: {recall * 100:.1f}%")
            else:
                if recommendations:
                    print("  WARNING: Expected NO recommendations, but API returned some.")
            
            # Add assistant message to history
            conversation_history.append({"role": "assistant", "content": reply})
            
        if trace_passed:
            passed_traces += 1
            if trace_recalls:
                avg_recall = sum(trace_recalls) / len(trace_recalls)
                all_recalls.append(avg_recall)
                print(f"\nTrace finished. Avg Recall: {avg_recall*100:.1f}%")
            else:
                print(f"\nTrace finished. No recommendation turns.")
        else:
            print(f"\nTrace failed verification.")
            
        total_traces += 1
        
    print(f"\n==================================================")
    print(f"Evaluation Complete:")
    print(f"  Total Traces Run: {total_traces}")
    print(f"  Passed Schema & URL Checks: {passed_traces}/{total_traces}")
    if all_recalls:
        print(f"  Mean Recall@10: {sum(all_recalls)/len(all_recalls)*100:.1f}%")
    print(f"==================================================")

if __name__ == '__main__':
    run_evaluation()
