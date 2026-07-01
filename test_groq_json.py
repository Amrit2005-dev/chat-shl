import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

def test():
    client = Groq(api_key=api_key)
    
    print("Calling Groq in JSON mode...")
    
    system_prompt = """You are a helpful assistant. You must respond ONLY in a valid JSON object matching this schema:
{
  "reply": "your text response",
  "recommendations": [
    {
      "name": "exact name of recommended item",
      "url": "exact URL of recommended item",
      "test_type": "type letter code"
    }
  ],
  "end_of_conversation": false
}
"""
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "I need a test for a mid-level Java developer."}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        response_text = completion.choices[0].message.content
        print("Success! Raw Response:")
        print(response_text)
        
        # Verify JSON
        data = json.loads(response_text)
        print("Parsed JSON:")
        print(json.dumps(data, indent=2))
    except Exception as e:
        print("Error with Groq JSON mode:", e)

if __name__ == '__main__':
    test()
