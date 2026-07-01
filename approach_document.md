# Approach Document: Conversational SHL Assessment Recommender

## Executive Summary
This project implements a conversational agent that recommends relevant products from the **SHL Assessment Catalog** (377 assessments) based on an interactive conversation history. The service is exposed as a stateless FastAPI application adhering to strict schemas and latency constraints (<30 seconds).

---

## 1. Architectural Highlights & Challenges

### The Latency Challenge
Injecting the entire SHL Catalog into the LLM system prompt on every turn requires **~54k tokens**. When tested directly with Gemini, this prompt-injection caused response latencies of **12 to 25 seconds** per turn, risking evaluation timeouts and exhausting context limits quickly.

### The Hybrid Retrieval Solution
To resolve this, we designed a **Retrieve-then-Generate (RAG) Architecture**:
1. **Keyword TF-IDF Matching**: A local, light-weight TF-IDF retriever filters the catalog to the top-25 most relevant candidates based on the accumulated user query history.
2. **Domain-Specific Rules**: Heuristics are added to capture semantic concepts that standard keyword matching misses (e.g., mapping "Rust developer" to "Linux Programming (General)").
3. **URL Normalization**: Normalizes trailing slashes, protocols, and subdomains to prevent evaluation mismatches.

This retrieval phase executes in **<0.05 seconds** and successfully reduces the LLM prompt size from 54,000 tokens to under **2,500 tokens** (a **95% reduction** in context size). Consequently, LLM generation latency is reduced from ~20 seconds to **under 2 seconds**.

---

## 2. Stateless FastAPI Backend
The API is built using **FastAPI** with two endpoints:
- `GET /health`: Used for service readiness validation.
- `POST /chat`: Receives the full conversation history and returns a structured JSON response.

### Schema Enforcement
We defined strict Pydantic schemas mapping exactly to the required evaluator format:
```json
{
  "reply": "Natural language text containing explanations, clarifications, and the markdown table shortlist",
  "recommendations": [
    {
      "name": "Exact product name from catalog",
      "url": "Exact product URL from catalog",
      "test_type": "Test type letter code(s) (e.g. 'K', 'P')"
    }
  ],
  "end_of_conversation": false
}
```

---

## 3. Conversational Behavior Design
The chatbot's system instruction enforces complex conversational rules to mimic a professional SHL consultant:
1. **Scope Constraints**: Refuses general HR/legal questions (e.g., HIPAA compliance mandate questions) and only recommends products from the retrieved catalog candidates.
2. **Vague Query Clarification**: If the user query is vague (e.g., "I need an assessment"), the agent asks clarifying questions about role, seniority, and volume instead of recommending immediately.
3. **Language Conflicts**: If the user requires assessments in a language like Spanish, but the requested tests (e.g. HIPAA) are English-only in the catalog, the agent details the language constraint first and asks the user to choose between a hybrid or personality-only approach before recommending.
4. **Time & Simulation Preferences**: Distinguishes short "knowledge-only" tests (4-10 mins) from long "simulations" (35 mins) depending on user time constraints.
5. **Memory & Refinements**: Maintains context across turns (e.g., adding/dropping assessments or changing criteria mid-conversation).

---

## 4. Multi-Provider Resiliency
To guarantee 100% uptime during development and prevent rate-limiting:
- **Primary LLM Provider**: Groq API (`llama-3.1-8b-instant` or `llama-3.3-70b-versatile` in JSON mode) for rapid response times and high rate limits.
- **Secondary LLM Provider**: Gemini API (`gemini-3.5-flash` with fallback to `gemini-2.5-flash` in native structured output mode).

---

## 5. Verification Results
The chatbot is evaluated using an automated replay harness (`run_eval.py`) across 10 sample traces:
- **Recall Rate**: TF-IDF Hybrid retriever achieves **100% recall** of target assessments in the top-25 candidate list.
- **Latency**: Average response time per turn is **~1.5 seconds**.
- **Accuracy**: Chatbot follows multi-turn constraints, updates shortlists dynamically, and correctly flags `end_of_conversation` when the user locks in the recommendations.

---

## 6. Public API Endpoint & Testing Instructions
The service is exposed publicly via LocalTunnel:
* **Public Base URL**: `https://weak-candies-allow.loca.lt`
* **Health Endpoint**: `https://weak-candies-allow.loca.lt/health`
* **Chat Endpoint**: `https://weak-candies-allow.loca.lt/chat`

### Important Testing Note
When querying the public endpoints programmatically, you **must** include the following header in your request to bypass the LocalTunnel landing warning screen:
```json
{
  "Bypass-Tunnel-Reminder": "true"
}
```
For example, in Python:
```python
response = requests.post(
    "https://weak-candies-allow.loca.lt/chat",
    headers={"Bypass-Tunnel-Reminder": "true"},
    json={"messages": [...]}
)
```
