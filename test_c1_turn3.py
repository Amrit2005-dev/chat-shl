import requests
import json
import time

url = "http://localhost:8000/chat"
payload = {
    "messages": [
        {"role": "user", "content": "We need a solution for senior leadership."},
        {"role": "assistant", "content": "To recommend the best solution for your senior leadership roles, I need a bit more information. Could you please specify target role or skills?"},
        {"role": "user", "content": "The pool consists of CXOs, director-level postions; people with more than 15 years of experience."},
        {"role": "assistant", "content": "For senior leadership positions with more than 15 years of experience, such as CXOs and director-level positions, I recommend assessments that evaluate..."},
        {"role": "user", "content": "Selection - comparing candidates against a leadership benchmark."}
    ]
}

print("Sending request to /chat...")
t0 = time.time()
try:
    resp = requests.post(url, json=payload, timeout=20)
    print(f"Status: {resp.status_code}")
    print("Response JSON:")
    print(json.dumps(resp.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")
print(f"Total time: {time.time() - t0:.2f}s")
