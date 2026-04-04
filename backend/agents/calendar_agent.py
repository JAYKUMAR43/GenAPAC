from sqlalchemy.orm import Session
from backend.tools.calendar_tool import CalendarTool
from backend.tools.notification_tool import NotificationTool

class CalendarAgent:
    def __init__(self):
        self.tool = CalendarTool()
        self.notification_tool = NotificationTool()

    def handle(self, intent_data: dict, db: Session) -> dict:
        intent = intent_data.get("intent")
        entities = intent_data.get("entities", {})
        
        input_data = {"db": db}
        
        if intent == "calendar.create":
            input_data["action"] = "create"
            input_data["title"] = entities.get("title")
            input_data["datetime"] = entities.get("datetime")
            
            # Optionally schedule a notification
            if input_data.get("datetime"):
                notif_data = {
                    "db": db,
                    "action": "schedule",
                    "message": f"Reminder: {input_data['title']}",
                    "trigger_time": input_data["datetime"]
                }
                self.notification_tool.execute(notif_data)
                
        elif intent == "calendar.list":
            input_data["action"] = "list"
        else:
            return {"status": "error", "response": "Invalid calendar intent."}
            
        return self.tool.execute(input_data)
