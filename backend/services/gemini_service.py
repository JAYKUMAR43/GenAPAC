import os
import json
from google import genai
from backend.utils.config import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

def analyze_intent(user_input: str) -> dict:
    """
    Analyzes user input (English, Hindi, Hinglish) and returns a structured JSON intent.
    Intents: task.create, task.list, task.complete, calendar.create, calendar.list, notes.create, notes.list, unknown
    """
    if not client:
        return {"intent": "error", "response": "Gemini API key not configured."}

    prompt = f"""
    You are an intelligent routing agent for a productivity assistant.
    Analyze the following user input, which may be in English, Hindi, or Hinglish.
    Determine the correct intent and extract relevant entities. Keep your responses short and crisp.

    Valid intents:
    - task.create (requires 'title')
    - task.list
    - task.complete (requires 'task_id')
    - calendar.create (requires 'title', 'datetime' in format YYYY-MM-DD HH:MM)
    - calendar.list
    - notes.create (requires 'content')
    - notes.list
    - unknown (for unrecognized requests)

    User Input: "{user_input}"

    Output ONLY a valid JSON object with 'intent' and 'entities' (if applicable).
    Example:
    {{
        "intent": "calendar.create",
        "entities": {{
            "title": "Meeting with Rahul",
            "datetime": "2026-03-28 10:00"
        }}
    }}
    """
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
            
        parsed = json.loads(text.strip())
        return parsed
    except Exception as e:
        print(f"Gemini Error: {e}")
        return {"intent": "error", "response": "Internal AI reasoning error."}
