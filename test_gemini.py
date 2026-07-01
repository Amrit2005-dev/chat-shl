import os
import time
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Load env variables
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

with open("catalog.json", "r", encoding="utf-8") as f:
    catalog = json.load(f)

# Create condensed catalog representation
catalog_condensed = []
for i in catalog:
    catalog_condensed.append({
        "id": i.get("id"),
        "name": i.get("name"),
        "url": i.get("url"),
        "description": i.get("description"),
        "test_type": i.get("test_type"),
        "job_levels": i.get("job_levels")
    })

catalog_json_str = json.dumps(catalog_condensed, ensure_ascii=False)

system_instruction = f"""
You are an expert SHL product recommender assistant.
You have access to the complete SHL Individual Test Solutions catalog below.
Catalog JSON:
{catalog_json_str}

Your goal is to recommend the correct assessments.
"""

def test_model(model_name):
    print(f"\n--- Testing model: {model_name} ---")
    try:
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_instruction
        )
        # Call 1
        t0 = time.time()
        response1 = model.generate_content("I need an assessment for a mid-level Java developer who works with stakeholders. What do you recommend?")
        t1 = time.time()
        print(f"Call 1 finished in {t1 - t0:.2f} seconds.")
        
        # Call 2 (warm cache test)
        t0 = time.time()
        response2 = model.generate_content("What is the difference between OPQ and GSA?")
        t1 = time.time()
        print(f"Call 2 finished in {t1 - t0:.2f} seconds.")
    except Exception as e:
        print(f"Error with model {model_name}: {e}")

if __name__ == '__main__':
    test_model("gemini-2.0-flash")
    test_model("gemini-2.5-flash")
    test_model("gemini-3.5-flash")
