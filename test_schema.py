import os
import json
import google.generativeai as genai
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Define schemas
class RecommendationItem(BaseModel):
    name: str = Field(description="Exact product name from catalog")
    url: str = Field(description="Exact product URL from catalog")
    test_type: str = Field(description="Test type letter codes (e.g. K or P)")

class ChatResponse(BaseModel):
    reply: str = Field(description="Natural language reply. Must match style of trace replies.")
    recommendations: List[RecommendationItem] = Field(description="Array of 1-10 recommendations, or empty array if not recommending.")
    end_of_conversation: bool = Field(description="True if conversation is finished, else False.")

def test():
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    prompt = "I need an assessment for a mid-level Java developer. Respond in the required JSON schema format."
    
    print("Sending request with Pydantic schema...")
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=ChatResponse
            )
        )
        print("Success! Response text:")
        print(response.text)
        
        # Verify JSON loads
        data = json.loads(response.text)
        print("Parsed JSON dict:", data)
    except Exception as e:
        print("Error with response_schema:", e)

if __name__ == '__main__':
    test()
