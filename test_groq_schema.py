import os
import json
from groq import Groq
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

class RecommendationItem(BaseModel):
    name: str = Field(description="Exact product name from catalog")
    url: str = Field(description="Exact product URL from catalog")
    test_type: str = Field(description="Test type letter codes (e.g. K or P)")

class ChatResponse(BaseModel):
    reply: str = Field(description="Natural language reply. Must match style of trace replies.")
    recommendations: List[RecommendationItem] = Field(description="Array of 1-10 recommendations, or empty array if not recommending.")
    end_of_conversation: bool = Field(description="True if conversation is finished, else False.")

def test():
    client = Groq(api_key=api_key)
    
    print("Calling Groq with Pydantic structured output...")
    try:
        completion = client.beta.chat.completions.parse(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Respond strictly in the required JSON schema format."},
                {"role": "user", "content": "I need a test for a mid-level Java developer."}
            ],
            response_format=ChatResponse
        )
        response_obj = completion.choices[0].message.parsed
        print("Success! Parsed object:")
        print("Reply:", response_obj.reply)
        print("Recommendations:", response_obj.recommendations)
        print("End of conversation:", response_obj.end_of_conversation)
    except Exception as e:
        print("Error with Groq structured output:", e)

if __name__ == '__main__':
    test()
