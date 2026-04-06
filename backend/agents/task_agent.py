from sqlalchemy.orm import Session
from backend.tools.task_tool import TaskTool
from backend.tools.notification_tool import NotificationTool

class TaskAgent:
    def __init__(self):
        self.tool = TaskTool()
        self.notification_tool = NotificationTool()

    def handle(self, intent_data: dict, db: Session) -> dict:
        intent = intent_data.get("intent")
        entities = intent_data.get("entities", {})
        
        input_data = {"db": db}
        
        if intent == "task.create":
            input_data["action"] = "create"
            input_data["title"] = entities.get("title")
            
            if entities.get("datetime"):
                notif_data = {
                    "db": db,
                    "action": "schedule",
                    "message": f"Task Reminder: {input_data['title']}",
                    "trigger_time": entities.get("datetime")
                }
                self.notification_tool.execute(notif_data)
        elif intent == "task.list":
            input_data["action"] = "list"
        elif intent == "task.complete":
            input_data["action"] = "complete"
            input_data["task_id"] = entities.get("task_id")
        else:
            return {"status": "error", "response": "Invalid task intent."}
            
        return self.tool.execute(input_data)
