from sqlalchemy.orm import Session
from backend.services.gemini_service import analyze_intent
from backend.services.logger import log_action
from backend.agents.task_agent import TaskAgent
from backend.agents.calendar_agent import CalendarAgent
from backend.agents.notes_agent import NotesAgent

class RouterAgent:
    def __init__(self):
        self.task_agent = TaskAgent()
        self.calendar_agent = CalendarAgent()
        self.notes_agent = NotesAgent()

    def handle(self, user_input: str, db: Session) -> dict:
        # Step 1: Detect Intent via LLM
        intent_data = analyze_intent(user_input)
        intent = intent_data.get("intent", "unknown")
        
        # Fallback response from Gemini if it's unknown or conversational
        fallback_msg = intent_data.get("response", "I'm sorry, I couldn't understand that request.")

        # If error occurred in Gemini service
        if intent == "error":
            return {"status": "error", "intent": "error", "response": fallback_msg}

        # Step 2: Route to specific Agent
        result = {}
        if intent.startswith("task."):
            result = self.task_agent.handle(intent_data, db)
        elif intent.startswith("calendar."):
            result = self.calendar_agent.handle(intent_data, db)
        elif intent.startswith("notes."):
            result = self.notes_agent.handle(intent_data, db)
        else:
            result = {"status": "success", "response": fallback_msg}
            
        result["intent"] = intent
        
        # Step 3: Log Action
        action_desc = f"Executed {intent}"
        log_action(db, user_input, intent, action_desc)

        return result
