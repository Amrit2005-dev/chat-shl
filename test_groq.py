import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
print(f"Loaded GROQ_API_KEY: {'yes' if api_key else 'no'}")

if not api_key:
    print("Error: GROQ_API_KEY not found.")
    exit(1)

# Check models via direct HTTP request
url = "https://api.groq.com/openai/v1/models"
headers = {
    "Authorization": f"Bearer {api_key}"
}

try:
    resp = requests.get(url, headers=headers, timeout=10)
    print("Status code:", resp.status_code)
    if resp.status_code == 200:
        models = resp.json().get("data", [])
        print("Available Groq models:")
        for m in models:
            print(f" - {m['id']}")
    else:
        print("Error response:", resp.text)
except Exception as e:
    print("Error checking Groq models:", e)
