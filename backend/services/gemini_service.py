import os
import json
from google import genai
from google.genai import types
from backend.utils.config import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

def analyze_intent(user_input: str, history: str = None) -> dict:
    """
    Analyzes user input (English, Hindi, Hinglish) and returns a structured JSON intent.
    Intents: task.create, task.list, task.complete, calendar.create, calendar.list, notes.create, notes.list, ask_clarification, unknown
    """
    if not client:
        return {"intent": "error", "response": "Gemini API key not configured."}

    prompt = f"""
    You are an intelligent routing agent for a productivity assistant.
    Analyze the following user input (in English, Hindi, or Hinglish) and recent conversation history.
    Determine the correct intent and extract relevant entities. Keep your responses short and crisp.

    If the user's intent matches action creation but is missing required fields (e.g. they say "Schedule a meeting" without a title or time), 
    return intent "ask_clarification" and put the question you want to ask in the "response" field.

    Valid intents:
    - task.create (requires 'title', 'datetime' in format YYYY-MM-DD HH:MM)
    - task.list
    - task.complete (requires 'task_id')
    - calendar.create (requires 'title', 'datetime' in format YYYY-MM-DD HH:MM)
    - calendar.list
    - notes.create (requires 'content', 'datetime' in format YYYY-MM-DD HH:MM)
    - notes.list
    - ask_clarification
    - unknown (for unrecognized requests)

    Recent History: {history if history else "None"}
    User Input: "{user_input}"

    Output ONLY a valid JSON object with 'intent', 'entities' (if applicable), and 'response' (if ask_clarification or unknown).
    Example for creation:
    {{
        "intent": "calendar.create",
        "entities": {{
            "title": "Meeting with Rahul",
            "datetime": "2026-03-28 10:00"
        }}
    }}
    Example for missing time:
    {{
        "intent": "ask_clarification",
        "response": "What time would you like to schedule the meeting?"
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

def analyze_document(file_bytes: bytes, mime_type: str) -> dict:
    if not client:
        return {"status": "error", "response": "Gemini API key not configured."}
    
    prompt = """
    Analyze the following document or image. 
    1. If it contains a meeting setup, extract the topic, date, and time.
    2. If it contains tasks, list them.
    3. If it contains general notes, extract them.
    Return ONLY a JSON block summarizing what action should be taken. We will feed this into the router.
    Output must be a JSON object with 'status' and 'extracted_text'.
    Example:
    { "status": "success", "extracted_text": "Schedule a meeting titled 'Design Sync' tomorrow at 2 PM." }
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
                prompt
            ]
        )
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
            
        parsed = json.loads(text.strip())
        return {"status": "success", "extracted_text": parsed.get("extracted_text", text)}
    except Exception as e:
        print(f"Document Analysis Error: {e}")
        return {"status": "error", "response": "Failed to analyze document."}
