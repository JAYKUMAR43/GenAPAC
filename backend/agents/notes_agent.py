from sqlalchemy.orm import Session
from backend.tools.notes_tool import NotesTool

class NotesAgent:
    def __init__(self):
        self.tool = NotesTool()

    def handle(self, intent_data: dict, db: Session) -> dict:
        intent = intent_data.get("intent")
        entities = intent_data.get("entities", {})
        
        input_data = {"db": db}
        
        if intent == "notes.create":
            input_data["action"] = "create"
            input_data["content"] = entities.get("content")
        elif intent == "notes.list":
            input_data["action"] = "list"
        else:
            return {"status": "error", "response": "Invalid notes intent."}
            
        return self.tool.execute(input_data)
