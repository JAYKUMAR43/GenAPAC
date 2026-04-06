from sqlalchemy.orm import Session
from backend.tools.notes_tool import NotesTool
from backend.tools.notification_tool import NotificationTool

class NotesAgent:
    def __init__(self):
        self.tool = NotesTool()
        self.notification_tool = NotificationTool()

    def handle(self, intent_data: dict, db: Session) -> dict:
        intent = intent_data.get("intent")
        entities = intent_data.get("entities", {})
        
        input_data = {"db": db}
        
        if intent == "notes.create":
            input_data["action"] = "create"
            input_data["content"] = entities.get("content")
            
            if entities.get("datetime"):
                notif_data = {
                    "db": db,
                    "action": "schedule",
                    "message": f"Note Reminder: {input_data['content']}",
                    "trigger_time": entities.get("datetime")
                }
                self.notification_tool.execute(notif_data)
        elif intent == "notes.list":
            input_data["action"] = "list"
        else:
            return {"status": "error", "response": "Invalid notes intent."}
            
        return self.tool.execute(input_data)
